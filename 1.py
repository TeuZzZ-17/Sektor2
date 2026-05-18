# --- START 1.py ---
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import copy
import re
import platform
import subprocess

# --- CONFIGURATION & CONSTANTS ---
DEFAULT_W, DEFAULT_H = 40, 40
DEFAULT_HGT = 0x7F
# Height Constraints (+/- 30 from 0x7F)
HGT_MIN = 0x61 # 97
HGT_MAX = 0x9D # 157

GRID_COLOR = "#707070"
MARKER_COLOR = "#FF00FF"
CUSTOM_BORDER_COLOR = "#FF0000" # Bright Red for Custom
TEXT_COLOR = "#00FFFF"
SCROLL_BG = "#00AAAA"
SCROLL_ACTIVE = TEXT_COLOR

# WORLD SCALE
SECTOR_SIZE = 3072
HALF_SECTOR = SECTOR_SIZE // 2

# Tech Layout
TECH_ITEM_W = 450
TECH_ITEM_H = 24

# Data Structures
FACTIONS = {
    0: ("NEUTRAL", None),
    1: ("RESISTANCE", "#0088FF"),
    2: ("SULGOGAR", "#00FF00"),
    3: ("MYKON", "#FFFFFF"),
    4: ("TAERKASTEN", "#FFFF00"),
    5: ("BLACK SECT", "#555555"),
    6: ("GHORKOV", "#FF0000"),
    7: ("DRONES", "#000000")
}

FACTION_TEXT_COLORS = {
    0: "#FFFFFF", 1: "#0088FF", 2: "#00FF00", 3: "#FFFFFF",
    4: "#FFFF00", 5: "#AAAAAA", 6: "#FF4444", 7: "#000000"
}

HEIGHTS = list(range(256))

class SektorEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Sektor Beta 1 - GATE FIX + DRONES")

        self.root.option_add("*Entry.selectBackground", "#3399FF")
        self.root.option_add("*Entry.selectForeground", "white")

        # 1. Initialization
        self.set_folder = self.ask_set()
        if not self.set_folder:
            root.destroy()
            return

        self.current_filename = None 
        self.update_window_title()

        # 2. State & Data
        self.mw, self.mh = DEFAULT_W, DEFAULT_H
        self.zoom_m, self.zoom_p = 64, 64
        self.mode = "TYPE"
        self.clear_view = False

        # LEVEL INFO
        self.lvl_info = {
            'title': "Untitled Map",
            'sky': "objects/x7.bas",
            'mbmap': "MB_53.IFF",
            'dbmap': "DB_53.IFF",
            'music': "None",   
            'movie': "None"    
        }
        self.script_content = ""
        self.grids = {}

        # MULTI-SLOT SYSTEM (Max 8)
        self.gates = {i: {'active': False, 'x': -1, 'y': -1, 'keys': [], 'target': 0, 'closed_bp': 25, 'opened_bp': 26} for i in range(1, 9)}
        self.items = {i: {'active': False, 'x': -1, 'y': -1, 'keys': [], 'countdown': 300000,
                          'inactive_bp': 35, 'active_bp': 36, 'trigger_bp': 37, 'type': 1} for i in range(1, 9)}

        self.gems = {i: {'x': -1, 'y': -1, 'blg': 50, 'type': 3, 'actions': []} for i in range(1, 9)}

        # VISIBILITY COUNTERS
        self.visible_gate_slots = 1
        self.visible_item_slots = 1
        self.visible_gem_slots = 1

        # SQUADS SYSTEM
        self.squads = []
        self.current_squad_data = {'owner': 1, 'veh': 1, 'num': 1, 'hidden': False, 'custom_name': None}
        self.current_squad_index = -1
        self._drag_squad_idx = -1

        # HOST STATIONS SYSTEM 
        self.host_stations = []
        self.current_host_data = {
            'owner': 1,
            'veh': 56, 
            'energy': 500000,
            'pos_y': -330, 
            'custom_name': None,
            'hidden': False 
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
        self.defs = {'veh':{}, 'blg':{}, 'host':{}}
        self.sky_previews = {}

        # 4. Boot Sequence
        self.load_definitions()
        self.load_assets()

        self.build_gui()
        self.reset_map(confirm=False)

        self.set_mode("TYPE")
        self.root.after(100, self.ask_dims)

    def update_window_title(self):
        title = f"Sektor Beta 1 - Env: {self.set_folder.upper()}"
        if self.current_filename:
            title += f" - [{self.current_filename}]"
        self.root.title(title)

    # --- COLLISION LOGIC ---
    def has_main_object(self, cx, cy, exclude_mode=None, exclude_slot=None):
        for i in range(1, 9):
            if exclude_mode == "GATE" and exclude_slot == i: continue
            if self.gates[i]['x'] == cx and self.gates[i]['y'] == cy: return True

        for i in range(1, 9):
            if exclude_mode == "ITEM" and exclude_slot == i: continue
            if self.items[i]['x'] == cx and self.items[i]['y'] == cy: return True

        for i in range(1, 9):
            if exclude_mode == "GEM" and exclude_slot == i: continue
            if self.gems[i]['x'] == cx and self.gems[i]['y'] == cy: return True
        return False

    def has_key(self, cx, cy):
        for i in range(1, 9):
            if (cx, cy) in self.gates[i]['keys']: return True
            if (cx, cy) in self.items[i]['keys']: return True
        return False

    def has_squad(self, cx, cy, exclude_index=None):
        for i, s in enumerate(self.squads):
            if exclude_index is not None and i == exclude_index: continue
            if s['x'] == cx and s['y'] == cy: return True
        return False

    def has_host(self, cx, cy, exclude_index=None):
        for i, h in enumerate(self.host_stations):
            if exclude_index is not None and i == exclude_index: continue
            if h['x'] == cx and h['y'] == cy: return True
        return False

    # --- ASSET MANAGEMENT (Base) ---
    def load_assets(self):
        def load_icon(filename, key, fallback_col, fallback_txt):
            path = os.path.join("icons", filename)
            if os.path.exists(path):
                self.assets[key] = Image.open(path)
            else:
                img = Image.new("RGBA", (64,64), (0,0,0,0)); d = ImageDraw.Draw(img)
                d.rectangle([4,4,60,60], outline=fallback_col, width=4)
                d.text((10,20), fallback_txt, fill=fallback_col)
                self.assets[key] = img

        if os.path.exists(self.set_folder):
            for f in sorted(os.listdir(self.set_folder)):
                if f.lower().endswith(('.png','.jpg')):
                    key = os.path.splitext(f)[0]
                    self.assets[key] = Image.open(os.path.join(self.set_folder, f))
                    self.lists['type'].append(key)
        if self.lists['type']: self.sel['type'] = self.lists['type'][0]

        if not os.path.exists("buildings"): os.makedirs("buildings")
        for f in sorted(os.listdir("buildings")):
            if f.lower().endswith(('.png','.jpg')):
                key = os.path.splitext(f)[0]
                self.assets[f"blg_{key}"] = Image.open(os.path.join("buildings", f))
                self.lists['blg'].append(key)

        if not os.path.exists("icons"): os.makedirs("icons")

        load_icon("custom.png", "custom_mod", "#FF00FF", "MOD")
        load_icon("gate.png", "gate", "#00FFFF", "GATE")
        load_icon("key.png", "key", "#FFFF00", "KEY")
        load_icon("superitem.png", "item", "#FF00FF", "ITEM")
        load_icon("superitem_key.png", "item_key", "#FF9900", "KEY")
        load_icon("gem.png", "gem", "#00FF00", "GEM")

        for i in range(1, 9):
            fac_col = FACTIONS[i][1] if i in FACTIONS and FACTIONS[i][1] else "#FFF"
            load_icon(f"host_{i}.png", f"host_{i}", fac_col, f"HOST\n{i}")

        if not os.path.exists("skies"): os.makedirs("skies")
        self.lists['sky'] = [f for f in sorted(os.listdir("skies")) if f.lower().endswith(('.png','.jpg','.jpeg'))]

    def load_definitions(self):
        for kind, filename in [('veh','vehicles.txt'), ('blg','buildings.txt'), ('host', 'hoststations.txt')]:
            candidates = [os.path.join("definitions", filename), os.path.join("definitions", filename.capitalize()), filename, filename.capitalize()]
            content = ""
            for p in candidates:
                if os.path.exists(p):
                    try:
                        with open(p, 'r', errors='ignore') as f: content = f.read(); break
                    except: pass

            if content:
                prefix = "vehicle" if kind == 'veh' or kind == 'host' else "building"
                simple_matches = re.findall(rf'^\s*{prefix}\s*=\s*(\d+)\s*;\s*(.+)', content, re.MULTILINE | re.IGNORECASE)
                for eid, name in simple_matches: self.defs[kind][int(eid)] = name.strip()

                block_prefix = "new_vehicle" if kind == 'veh' or kind == 'host' else "new_building"
                standard_matches = re.findall(rf'{block_prefix}\s+(\d+)(.*?)end', content, re.DOTALL | re.IGNORECASE)
                for eid, rest in standard_matches:
                    eid_int = int(eid)
                    if eid_int not in self.defs[kind]:
                        nm = re.search(r'name\s*=\s*(.+)', rest, re.IGNORECASE)
                        self.defs[kind][eid_int] = nm.group(1).strip() if nm else f"Unknown_{eid}"

            if not self.defs[kind]:
                if kind == 'host':
                     self.defs[kind] = { 56: "Resistance_Host", 60: "Taerkasten_Host", 62: "BlackSect_Host", 58: "Ghorkov_Host", 59: "Mykonian_Host", 57: "Sulgogar_Host" }
                else:
                    self.defs[kind] = {i:f"Obj_{i}" for i in range(1,100)}

    def get_img(self, cat, name, sz, extra=None):
        key = (cat, name, sz, extra)
        if key in self.cache: return self.cache[key]
        src = None

        if cat == 'type':
            if name in self.assets: src = self.assets[name]

        elif cat == 'blg':
            if f"blg_{name}" in self.assets: src = self.assets[f"blg_{name}"]

        elif cat == 'gem_graphic':
            if f"gem_graphic_{name}" in self.assets: src = self.assets[f"gem_graphic_{name}"]

        elif cat == 'special':
            if name in self.assets: src = self.assets[name]

        elif cat == 'host':
            h_key = f"host_{name}"
            if h_key in self.assets: src = self.assets[h_key]
            else: src = self.assets["custom_mod"]

        elif cat == 'overlay':
            fid = int(name)
            if fid in FACTIONS and FACTIONS[fid][1]:
                col = FACTIONS[fid][1]
                rgb = tuple(int(col.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                if extra == 'pale': alpha = 200
                elif fid == 7: alpha = 171
                elif fid == 5: alpha = 128
                else: alpha = 60
                src = Image.new("RGBA", (sz, sz), rgb + (alpha,))
        elif cat == 'hgt':
            h = int(name)
            diff = abs(h - 127)
            alpha = int(min(200, diff * 6.6))
            c = (255,255,255) if h > 127 else (0,0,0)
            src = Image.new("RGBA", (sz, sz), c + (alpha,))
        elif cat == 'border':
            src = Image.new("RGBA", (sz, sz), (0, 255, 255, 140))

        if src:
            tk_img = ImageTk.PhotoImage(src.resize((sz, sz), Image.Resampling.NEAREST))
            self.cache[key] = tk_img
            return tk_img
        return None

# --- END 1.py ---
