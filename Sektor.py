# Sektor
# Copyright (c) 2025 TeuZzZ
# Licensed under GNU GPL v3

import tkinter as tk
import os
import sys

from sektor_constants import *
from sektor_history import HistoryMixin
from sektor_assets import AssetMixin
from sektor_ui import UIMixin
from sektor_canvas import CanvasMixin
from sektor_map_io import MapIOMixin
from sektor_dialogs import DialogMixin


class SektorEditor(
    HistoryMixin,
    AssetMixin,
    UIMixin,
    CanvasMixin,
    MapIOMixin,
    DialogMixin,
):
    def __init__(self, root, startup_file=None):
        self.root = root
        self.root.title(APP_NAME)

        self.root.option_add("*Entry.selectBackground", "#3399FF")
        self.root.option_add("*Entry.selectForeground", "white")

        startup_file = os.path.abspath(startup_file) if startup_file else None
        if startup_file and (not os.path.isfile(startup_file) or not startup_file.lower().endswith(".ldf")):
            startup_file = None
        self.startup_file = startup_file

        # 1. Initialization
        startup_map_settings = None
        if self.startup_file:
            self.set_folder = self.detect_ldf_set_folder(self.startup_file) or "set1"
        else:
            startup_map_settings = self.ask_new_map_settings(title=APP_NAME)
            if not startup_map_settings:
                root.destroy()
                return
            self.set_folder = startup_map_settings['set_folder']

        self.current_filename = None 
        self.current_filepath = None
        self.update_window_title()

        # 2. State & Data
        if startup_map_settings:
            self.mw, self.mh = startup_map_settings['width'], startup_map_settings['height']
        else:
            self.mw, self.mh = DEFAULT_W, DEFAULT_H
        self.zoom_m, self.zoom_p = 64, 128
        self.zoom_m_min = 32
        self.zoom_m_max = 192
        self.zoom_m_step = 8
        self.mode = "TYPE"
        self.clear_view = False
        self.left_panel_width = 440
        self._palette_resize_refresh_pending = False
        self._map_layout_refresh_pending = False
        self.space_pan_active = False
        self._map_panning = False
        self._map_pan_source = None
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 100
        self.dirty = False
        self._map_edit_snapshot_taken = False
        self._map_right_edit_snapshot_taken = False
        self.hover_cell = None

        # LEVEL INFO
        self.lvl_info = {
            'title': "Untitled Map",
            'sky': "objects/x7.bas",
            'mbmap': "MB_53.IFF",
            'dbmap': "DB_53.IFF",
            'music': "None",   
            'movie': "None"    
        }
        self.script_content = DEFAULT_SCRIPT_CONTENT
        self.grids = {}

        # MULTI-SLOT SYSTEM
        self.gates = {i: {'active': False, 'x': -1, 'y': -1, 'keys': [], 'target': 0, 'closed_bp': 25, 'opened_bp': 26, 'hidden': False} for i in range(1, MAX_SPECIAL_SLOTS + 1)}
        self.items = {i: {'active': False, 'x': -1, 'y': -1, 'keys': [], 'countdown': 300000,
                          'inactive_bp': 35, 'active_bp': 36, 'trigger_bp': 37, 'type': 1, 'hidden': False} for i in range(1, MAX_SPECIAL_SLOTS + 1)}

        self.gems = {i: {'x': -1, 'y': -1, 'blg': 50, 'type': 3, 'actions': [], 'hidden': False} for i in range(1, MAX_SPECIAL_SLOTS + 1)}

        # VISIBILITY COUNTERS
        self.visible_gate_slots = 1
        self.visible_item_slots = 1
        self.visible_gem_slots = 1

        # SQUADS SYSTEM
        self.squads = []
        self.current_squad_data = {'owner': 1, 'veh': 1, 'num': 1, 'hidden': False, 'useable': False, 'custom_name': None}
        self.current_squad_index = -1
        self._drag_squad_idx = -1

        # HOST STATIONS SYSTEM 
        self.player_owner = 1
        self.host_stations = []
        self.current_host_data = {
            'owner': 1,
            'veh': 56, 
            'energy': 500000,
            'pos_y': DEFAULT_HOST_POS_Y,
            'reload_const': DEFAULT_HOST_RELOAD_CONST,
            'viewangle': DEFAULT_HOST_VIEWANGLE,
            'custom_name': None,
            'hidden': False,
            'ai': self.make_host_ai()
        }
        self.current_host_index = -1
        self._drag_host_idx = -1

        self.current_gate_slot = 1
        self.current_item_slot = 1
        self.current_gem_slot = 1

        self.tech = {i: {'veh': [], 'blg': []} for i in range(1, 8)}
        self.custom_tech_names = {}
        self.curr_tech_faction = 1
        self._last_dragged_id = None
        self._tech_drag_active = False
        self._tech_dragging = False
        self._tech_drag_snapshot_taken = False
        self._tech_drag_start = (0, 0)
        self._tech_drag_action = "enable"
        
        # CUSTOM DEFINITIONS FOR MAP TILES (ID -> Name)
        self.custom_definitions = {
            'type': {}, # Key: int ID, Val: str Name
            'blg': {}   # Key: int ID, Val: str Name
        }

        # DRAGGING STATE FOR KEYS
        self._drag_key_list = None
        self._drag_key_idx = -1

        self.gate_tool = "GATE"
        self.item_tool = "ITEM"
        self.gem_tool = "GEM"

        # 3. Resources
        self.assets = {}
        self.lists = {'type':[], 'blg':['00'], 'sky':[], 'gem_graphics': []}
        self.sel = {'type':'00', 'own':1, 'hgt':DEFAULT_HGT, 'blg':'00'}
        self.cache = {}
        self.defs = {'veh':{}, 'blg':{}, 'host':{}, 'weapon':{}}
        self.building_overlays = {}
        self.sky_previews = {}

        # 4. Boot Sequence
        self.load_definitions()
        self.load_assets()

        self.build_gui()
        self.reset_map(confirm=False, track_history=False)

        if self.startup_file:
            if not self.load_map_from_path(self.startup_file, prompt_unsaved=False, show_success=False):
                self.mark_saved_state()
                self.set_mode("TYPE")
        else:
            self.mark_saved_state()
            self.set_mode("TYPE")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

if __name__ == "__main__":
    root = tk.Tk()
    try: root.state('zoomed')
    except: pass
    startup_file = sys.argv[1] if len(sys.argv) > 1 else None
    SektorEditor(root, startup_file=startup_file)
    root.mainloop()
