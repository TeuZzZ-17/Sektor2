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

    def build_gui(self):
        # MOD: Removed PanedWindow to prevent Sash/Button glitch. Using Frames.
        f_main = tk.Frame(self.root, bg="#222")
        f_main.pack(fill=tk.BOTH, expand=True)

        f_left = tk.Frame(f_main, bg="#1a1a1a", width=460)
        f_left.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        f_left.pack_propagate(False) # Force width

        f_right = tk.Frame(f_main, bg="#000")
        f_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- LEFT PANEL ---
        tb_pal = tk.Frame(f_left, bg="#2a2a2a", height=36); tb_pal.pack(fill=tk.X)
        self.lbl_sel = tk.Label(tb_pal, text="SEL: 00", bg="#2a2a2a", fg="#00FFFF", font=("Courier", 12, "bold"), width=15, anchor="w")
        self.lbl_sel.pack(side=tk.LEFT, padx=5)

        # CUSTOM ID LABELS & ENTRY
        self.f_custom_inputs = tk.Frame(tb_pal, bg="#2a2a2a")
        
        # ID Input
        self.lbl_custom_title = tk.Label(self.f_custom_inputs, text="ID:", bg="#2a2a2a", fg="#aaa", font=("Arial",8))
        self.lbl_custom_title.pack(side=tk.LEFT, padx=(5,1))
        
        self.entry_custom = tk.Entry(self.f_custom_inputs, width=4, bg="#111", fg="white", insertbackground="white")
        self.entry_custom.pack(side=tk.LEFT, padx=1)
        self.entry_custom.bind("<KeyRelease>", self.on_custom_input)

        # Name Input
        tk.Label(self.f_custom_inputs, text="Name:", bg="#2a2a2a", fg="#aaa", font=("Arial",8)).pack(side=tk.LEFT, padx=(5,1))
        self.entry_custom_name = tk.Entry(self.f_custom_inputs, width=10, bg="#111", fg="#FFFF00", insertbackground="white")
        self.entry_custom_name.pack(side=tk.LEFT, padx=1)
        self.entry_custom_name.bind("<KeyRelease>", self.on_custom_name_input)

        zoom_sty = {'bg':'#333','fg':'white','padx':5,'font':("Arial",8)}
        self.btn_zm_p_out = tk.Button(tb_pal, text="-", command=lambda: self.zoom_pal(-16), **zoom_sty)
        self.btn_zm_p_in = tk.Button(tb_pal, text="+", command=lambda: self.zoom_pal(16), **zoom_sty)

        self.btn_zm_p_out.pack(side=tk.RIGHT, padx=2)
        self.btn_zm_p_in.pack(side=tk.RIGHT, padx=2)

        self.cnt_frame = tk.Frame(f_left, bg="#1a1a1a")
        self.cnt_frame.pack(fill=tk.BOTH, expand=True)
        self.cv_pal = tk.Canvas(self.cnt_frame, bg="#1a1a1a", highlightthickness=0)

        self.sb_pal = tk.Scrollbar(self.cnt_frame, command=self.cv_pal.yview, bg=SCROLL_BG, activebackground=SCROLL_ACTIVE, troughcolor='#555')
        self.cv_pal.config(yscrollcommand=self.sb_pal.set)
        self.cv_pal.bind("<Configure>", self.draw_palette)
        self.bind_scroll(self.cv_pal)

        self.panels = {
            'GATE': tk.Frame(self.cnt_frame, bg="#1a1a1a"),
            'ITEM': tk.Frame(self.cnt_frame, bg="#1a1a1a"),
            'GEM': tk.Frame(self.cnt_frame, bg="#1a1a1a"),
            'TECH': tk.Frame(self.cnt_frame, bg="#1a1a1a"),
            'SCRIPT': tk.Frame(self.cnt_frame, bg="#1a1a1a"),
            'HGT_INPUT': tk.Frame(self.cnt_frame, bg="#1a1a1a"),
            'SQUAD': tk.Frame(self.cnt_frame, bg="#1a1a1a"),
            'HOST': tk.Frame(self.cnt_frame, bg="#1a1a1a")
        }

        # --- RIGHT PANEL (MAP) ---
        tb_map = tk.Frame(f_right, bg="#2a2a2a", height=50); tb_map.pack(fill=tk.X)
        tk.Label(tb_map, text="MODE:", bg="#2a2a2a", fg="#aaa").pack(side=tk.LEFT, padx=5)
        self.btns = {}

        modes = [("TYPE","SECTOR","#0066CC"),
                 ("BLG","BUILDING","#C71585"),
                 ("OWN","OWNER","#CC6600"),
                 ("HGT","HEIGHT","#660066"),
                 ("GATE","BEAMGATE","#00AAAA"),
                 ("ITEM","BOMB","#FF00FF"),
                 ("GEM","GEM","#00FF00"),
                 ("SQUAD", "SQUAD", "#FF4400"),
                 ("HOST", "HOST", "#FFD700"),
                 ("TECH","TECH","#888800"),
                 ("SCRIPT","SCRIPT","#008080")]

        for m, txt, col in modes:
            b = tk.Button(tb_map, text=txt, bg="#444", fg="white", command=lambda x=m: self.set_mode(x))
            b.pack(side=tk.LEFT, padx=1); self.btns[m] = (b, col)

        tk.Frame(tb_map, width=20, bg="#2a2a2a").pack(side=tk.LEFT)
        actions = [("+", lambda: self.zoom_map(16), "#333"), ("-", lambda: self.zoom_map(-16), "#333"),
            ("RESET", lambda: self.reset_map(True), "#800000"),
            ("RESIZE", self.resize_map_dialog, "#663300"),
            ("FILL", self.fill_map, "#333")]
        for t, cmd, bg in actions: tk.Button(tb_map, text=t, command=cmd, bg=bg, fg="white", font=("Arial",8)).pack(side=tk.LEFT, padx=1)

        self.btn_cl = tk.Button(tb_map, text="CLEAR VIEW", command=self.toggle_clear, bg="#444", fg="white", font=("Arial",8))
        self.btn_cl.pack(side=tk.LEFT, padx=5)

        io_btns = [("CHANGE LEVEL INFO", self.edit_info, "#4B0082"), ("LOAD MAP", self.load_map, "#CC0000"), ("SAVE MAP", self.save_map, "#006600")]
        for t, cmd, bg in io_btns: tk.Button(tb_map, text=t, command=cmd, bg=bg, fg="white", font=("Arial",8,"bold")).pack(side=tk.LEFT, padx=5)

        # SCROLLABLE MAP CONTAINER
        f_map_container = tk.Frame(f_right, bg="#000")
        f_map_container.pack(fill=tk.BOTH, expand=True)

        self.cv_map = tk.Canvas(f_map_container, bg="#000", highlightthickness=0)

        v_scroll = tk.Scrollbar(f_map_container, orient=tk.VERTICAL, command=self.cv_map.yview, bg=SCROLL_BG, activebackground=SCROLL_ACTIVE, troughcolor="#333")
        h_scroll = tk.Scrollbar(f_map_container, orient=tk.HORIZONTAL, command=self.cv_map.xview, bg=SCROLL_BG, activebackground=SCROLL_ACTIVE, troughcolor="#333")

        self.cv_map.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.cv_map.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.bind_scroll(self.cv_map)
        self.cv_map.bind("<Button-1>", self.on_click); self.cv_map.bind("<B1-Motion>", self.on_click)
        self.cv_map.bind("<Button-3>", self.on_right_click); self.cv_map.bind("<B3-Motion>", self.on_right_click)
        self.cv_map.bind("<Button-2>", self.pick)
        self.cv_map.bind("<ButtonRelease-1>", self.on_release)

    def on_release(self, e):
        # Reset Key Dragging
        self._drag_key_list = None
        self._drag_key_idx = -1
        # Reset Tech Dragging
        self._last_dragged_id = None
        # Reset Squad Dragging
        self._drag_squad_idx = -1
        # Reset Host Dragging
        self._drag_host_idx = -1

    def on_custom_input(self, event):
        val_str = self.entry_custom.get().strip()
        if not val_str: return
        try:
            val_int = int(val_str, 16)
            if self.mode == "TYPE":
                 self.set_sel(f"{val_int:02X}")
            elif self.mode == "BLG":
                 self.set_sel(f"{val_int:02X}")
        except: pass

    def on_custom_name_input(self, event):
        name_str = self.entry_custom_name.get().strip()
        val_str = self.entry_custom.get().strip()
        if not val_str: return
        
        try:
            val_int = int(val_str, 16)
            cat = 'type' if self.mode == "TYPE" else 'blg' if self.mode == "BLG" else None
            
            if cat:
                if name_str:
                    self.custom_definitions[cat][val_int] = name_str
                elif val_int in self.custom_definitions[cat]:
                    del self.custom_definitions[cat][val_int]
        except: pass

    def upd_lbl(self):
        if self.mode == "GATE":
            tgt = self.gates[self.current_gate_slot]['target']
            self.lbl_sel.config(text=f"BEAMGATE [{self.current_gate_slot}]: TGT {tgt}")
        elif self.mode == "ITEM":
            mins = self.items[self.current_item_slot]['countdown'] // 60000
            self.lbl_sel.config(text=f"BOMB [{self.current_item_slot}]: {mins}m")
        elif self.mode == "GEM":
             typ = self.gems[self.current_gem_slot]['type']
             t_str = "PWR" if typ==1 else "SHLD" if typ==2 else "TECH"
             self.lbl_sel.config(text=f"GEM [{self.current_gem_slot}]: {t_str}")
        elif self.mode == "TECH":
            fid = self.curr_tech_faction
            self.lbl_sel.config(text=f"TECH: {FACTIONS[fid][0]}")
        elif self.mode == "SQUAD":
             self.lbl_sel.config(text="SQUAD EDITOR")
        elif self.mode == "HOST":
             self.lbl_sel.config(text="HOST EDITOR")
        elif self.mode == "SCRIPT":
            self.lbl_sel.config(text="SCRIPT EDITOR")
        elif self.mode == "HGT":
            self.lbl_sel.config(text="")
        else:
            v = self.sel['type'] if self.mode=="TYPE" else self.sel['own'] if self.mode=="OWN" else self.sel['blg']
            t = f"{v:02X}" if isinstance(v,int) else str(v)
            self.lbl_sel.config(text=f"{self.mode}: {t}")

            if self.mode in ["TYPE", "BLG"] and isinstance(v, str):
                try:
                    v_int = int(v, 16)
                    cat = 'type' if self.mode == "TYPE" else 'blg'
                    self.entry_custom.delete(0, tk.END)
                    self.entry_custom.insert(0, v)
                    
                    self.entry_custom_name.delete(0, tk.END)
                    if v_int in self.custom_definitions[cat]:
                        self.entry_custom_name.insert(0, self.custom_definitions[cat][v_int])
                except: pass


    def get_current_items(self):
        if self.mode=="TYPE": return self.lists['type']
        elif self.mode=="OWN": return list(FACTIONS.keys())
        elif self.mode=="HGT":
            return list(range(HGT_MIN, HGT_MAX + 1))
        elif self.mode=="BLG": return self.lists['blg']
        return []

    def set_mode(self, m):
        self.mode = m
        self._drag_squad_idx = -1
        self._drag_host_idx = -1

        for k, (b, c) in self.btns.items(): b.config(bg=c if k==m else "#444")
        self.cv_pal.pack_forget(); self.sb_pal.pack_forget()
        for p in self.panels.values(): p.pack_forget()

        if m in ["TYPE", "BLG"]:
            self.lbl_sel.pack(side=tk.LEFT, padx=5)
            self.btn_zm_p_out.pack(side=tk.RIGHT, padx=2)
            self.btn_zm_p_in.pack(side=tk.RIGHT, padx=2)

            self.f_custom_inputs.pack(side=tk.LEFT, padx=5)
            if m == "TYPE": self.lbl_custom_title.config(text="Custom Sector ID:")
            else: self.lbl_custom_title.config(text="Custom Building ID:")
            
        else:
            self.lbl_sel.pack_forget()
            self.btn_zm_p_in.pack_forget()
            self.btn_zm_p_out.pack_forget()
            self.f_custom_inputs.pack_forget()

        if m == "HGT":
            self.build_height_input_panel()
            self.panels['HGT_INPUT'].pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        elif m in self.panels:
            if m == "GATE": self.build_gate_ui()
            elif m == "ITEM": self.build_item_ui()
            elif m == "GEM": self.build_gem_ui()
            elif m == "TECH": self.build_tech_ui()
            elif m == "SCRIPT": self.build_script_ui()
            elif m == "SQUAD": self.build_squad_ui()
            elif m == "HOST": self.build_host_ui()
            self.panels[m].pack(fill=tk.BOTH, expand=True)
        else:
            self.sb_pal.pack(side=tk.RIGHT, fill=tk.Y); self.cv_pal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.draw_palette()

        self.upd_lbl()
        self.draw_grid()

    def build_height_input_panel(self):
        p = self.panels['HGT_INPUT']
        for w in p.winfo_children(): w.destroy()
        tk.Label(p, text="HEIGHT EDITOR (0 - 60)", bg="#660066", fg="white", font=("Arial",12,"bold")).pack(fill=tk.X, pady=(10,20))

        f = tk.Frame(p, bg="#1a1a1a"); f.pack(pady=10)

        current_user_val = self.sel['hgt'] - HGT_MIN

        def update_hex_label():
            hv_real = self.sel['hgt']
            if hasattr(self, 'lbl_hgt_hex'):
                self.lbl_hgt_hex.config(text=f"real hex output: {hv_real:02X}")

        def adj_hgt(d):
            new_val = max(HGT_MIN, min(HGT_MAX, self.sel['hgt'] + d))
            self.sel['hgt'] = new_val
            user_val = new_val - HGT_MIN
            self.hgt_entry.delete(0, tk.END); self.hgt_entry.insert(0, str(user_val))
            update_hex_label()

        tk.Button(f, text="<", command=lambda: adj_hgt(-1), bg="#333", fg="white", font=("bold", 14), width=3).pack(side=tk.LEFT, padx=10)

        self.hgt_entry = tk.Entry(f, width=5, font=("Courier", 24, "bold"), justify='center', bg="#222", fg="#00FFFF", insertbackground="white")
        self.hgt_entry.pack(side=tk.LEFT, padx=10, ipady=4)
        self.hgt_entry.insert(0, str(current_user_val))

        def manual_entry(e):
             self.process_height_input(e)
             update_hex_label()

        self.hgt_entry.bind("<KeyRelease>", manual_entry)

        tk.Button(f, text=">", command=lambda: adj_hgt(1), bg="#333", fg="white", font=("bold", 14), width=3).pack(side=tk.LEFT, padx=10)

        self.lbl_hgt_hex = tk.Label(p, text=f"real hex output: {self.sel['hgt']:02X}", bg="#1a1a1a", fg="#888", font=("Courier", 10, "bold"))
        self.lbl_hgt_hex.pack(pady=(0, 20))

    def process_height_input(self, event=None):
        val_str = self.hgt_entry.get().strip()
        if not val_str.isdigit(): return
        try:
            val = int(val_str)
            val = max(0, min(60, val))
            self.sel['hgt'] = val + HGT_MIN
        except ValueError: pass

    # --- GATE UI (FIXED PRESETS) ---
    def build_gate_ui(self):
        p = self.panels['GATE']
        for w in p.winfo_children(): w.destroy()

        f_slots = tk.Frame(p, bg="#1a1a1a"); f_slots.pack(fill=tk.X, pady=5)

        for i in range(1, self.visible_gate_slots + 1):
            bg = "#00FFFF" if i == self.current_gate_slot else "#333"
            fg = "black" if i == self.current_gate_slot else "white"
            tk.Button(f_slots, text=str(i), bg=bg, fg=fg, width=2, command=lambda x=i: self.select_gate_slot(x)).pack(side=tk.LEFT, padx=1)

        if self.visible_gate_slots < 8:
            def add_slot():
                self.visible_gate_slots += 1; self.build_gate_ui()
            tk.Button(f_slots, text="+", bg="#008888", fg="white", width=2, command=add_slot).pack(side=tk.LEFT, padx=5)

        if self.visible_gate_slots > 1:
            def rem_slot():
                idx = self.visible_gate_slots
                self.gates[idx] = {'active': False, 'x': -1, 'y': -1, 'keys': [], 'target': 0, 'closed_bp': 25, 'opened_bp': 26}
                self.visible_gate_slots -= 1
                if self.current_gate_slot > self.visible_gate_slots: self.current_gate_slot = self.visible_gate_slots
                self.build_gate_ui(); self.draw_grid()
            tk.Button(f_slots, text="-", bg="#880000", fg="white", width=2, command=rem_slot).pack(side=tk.LEFT, padx=2)

        g_data = self.gates[self.current_gate_slot]

        # --- PRESET DROPDOWN (GATE) ---
        f_pre = tk.Frame(p, bg="#1a1a1a"); f_pre.pack(fill=tk.X, pady=(10,2))
        tk.Label(f_pre, text="Road Preset:", bg="#1a1a1a", fg="#aaa").pack(side=tk.LEFT, padx=5)
        
        # MOD: Inversione dei valori 
        # 5/6 = No Road (Standard)
        # 25/26 = With Roads (Cranes)
        gate_preset_values = ["No Road (5/6)", "With Roads (25/26)"]
        cb_gate_preset = ttk.Combobox(f_pre, values=gate_preset_values, state="readonly", width=25)
        cb_gate_preset.pack(side=tk.LEFT, padx=5)
        
        if g_data['closed_bp'] == 5 and g_data['opened_bp'] == 6:
            cb_gate_preset.set("No Road (5/6)")
        elif g_data['closed_bp'] == 25 and g_data['opened_bp'] == 26:
             cb_gate_preset.set("With Roads (25/26)")
        else:
             cb_gate_preset.set("") 

        def on_gate_preset_select(event):
            val = cb_gate_preset.get()
            if "No Road" in val:
                g_data['closed_bp'] = 5
                g_data['opened_bp'] = 6
            elif "With Roads" in val:
                g_data['closed_bp'] = 25
                g_data['opened_bp'] = 26
            self.build_gate_ui() 
            self.draw_grid()

        cb_gate_preset.bind("<<ComboboxSelected>>", on_gate_preset_select)
        
        tk.Label(p, text="(Custom values allowed)", fg="#777", bg="#1a1a1a", font=("Arial", 7)).pack(pady=(0,5))

        f = tk.Frame(p, bg="#1a1a1a"); f.pack(fill=tk.X, pady=5)

        tk.Label(f, text="Target Level:", fg="white", bg="#1a1a1a", width=10).grid(row=0, column=0)
        e_tgt = tk.Entry(f, width=5); e_tgt.grid(row=0, column=1)
        e_tgt.insert(0, str(g_data['target']))

        tk.Label(f, text="Off Model:", fg="white", bg="#1a1a1a", width=10).grid(row=0, column=2)
        e_cls = tk.Entry(f, width=5); e_cls.grid(row=0, column=3)
        e_cls.insert(0, str(g_data['closed_bp']))

        tk.Label(f, text="On Model:", fg="white", bg="#1a1a1a", width=10).grid(row=1, column=0)
        e_opn = tk.Entry(f, width=5); e_opn.grid(row=1, column=1)
        e_opn.insert(0, str(g_data['opened_bp']))

        def upd_g(ev):
            try:
                g_data['target'] = int(e_tgt.get())
                g_data['closed_bp'] = int(e_cls.get())
                g_data['opened_bp'] = int(e_opn.get())
                
                # Logic updated to match the new definitions
                if g_data['closed_bp'] == 5 and g_data['opened_bp'] == 6: cb_gate_preset.set("No Road (5/6)")
                elif g_data['closed_bp'] == 25 and g_data['opened_bp'] == 26: cb_gate_preset.set("With Roads (25/26)")
                else: cb_gate_preset.set("")
                self.upd_lbl()
            except: pass
        e_tgt.bind("<KeyRelease>", upd_g); e_cls.bind("<KeyRelease>", upd_g); e_opn.bind("<KeyRelease>", upd_g)

        def set_t(t): self.gate_tool=t
        tk.Button(p, text="[ PLACE BEAMGATE ]", command=lambda: set_t("GATE"), bg="#00FFFF", fg="black").pack(fill=tk.X, pady=5)
        tk.Button(p, text="[ PLACE KEYSECT ]", command=lambda: set_t("KEY"), bg="#FFFF00", fg="black").pack(fill=tk.X, pady=2)
        self.upd_lbl()
        self.draw_grid()

    def select_gate_slot(self, slot):
        self.current_gate_slot = slot; self.build_gate_ui()

    # --- ITEM UI (UPDATED WITH PRESETS) ---
    def build_item_ui(self):
        p = self.panels['ITEM']
        for w in p.winfo_children(): w.destroy()

        f_slots = tk.Frame(p, bg="#1a1a1a"); f_slots.pack(fill=tk.X, pady=5)

        for i in range(1, self.visible_item_slots + 1):
            bg = "#FF00FF" if i == self.current_item_slot else "#333"
            fg = "white"
            tk.Button(f_slots, text=str(i), bg=bg, fg=fg, width=2, command=lambda x=i: self.select_item_slot(x)).pack(side=tk.LEFT, padx=1)

        if self.visible_item_slots < 8:
            def add_slot():
                self.visible_item_slots += 1; self.build_item_ui()
            tk.Button(f_slots, text="+", bg="#880088", fg="white", width=2, command=add_slot).pack(side=tk.LEFT, padx=5)

        if self.visible_item_slots > 1:
            def rem_slot():
                idx = self.visible_item_slots
                self.items[idx] = {'active': False, 'x': -1, 'y': -1, 'keys': [], 'countdown': 300000,
                          'inactive_bp': 35, 'active_bp': 36, 'trigger_bp': 37, 'type': 1}
                self.visible_item_slots -= 1
                if self.current_item_slot > self.visible_item_slots: self.current_item_slot = self.visible_item_slots
                self.build_item_ui(); self.draw_grid()
            tk.Button(f_slots, text="-", bg="#880000", fg="white", width=2, command=rem_slot).pack(side=tk.LEFT, padx=2)

        i_data = self.items[self.current_item_slot]
        
        # --- PRESET DROPDOWN (ITEM) ---
        f_pre = tk.Frame(p, bg="#1a1a1a"); f_pre.pack(fill=tk.X, pady=(10,2))
        tk.Label(f_pre, text="Model Preset:", bg="#1a1a1a", fg="#aaa").pack(side=tk.LEFT, padx=5)
        
        preset_values = ["Standard (35/36/37)", "Parasite (68/69/70)"]
        cb_preset = ttk.Combobox(f_pre, values=preset_values, state="readonly", width=25)
        cb_preset.pack(side=tk.LEFT, padx=5)
        
        if i_data['inactive_bp'] == 35 and i_data['active_bp'] == 36 and i_data['trigger_bp'] == 37:
             cb_preset.set("Standard (35/36/37)")
        elif i_data['inactive_bp'] == 68 and i_data['active_bp'] == 69 and i_data['trigger_bp'] == 70:
             cb_preset.set("Parasite (68/69/70)")
        else:
             cb_preset.set("") 

        def on_preset_select(event):
            val = cb_preset.get()
            if "Standard" in val:
                i_data['inactive_bp'] = 35
                i_data['active_bp'] = 36
                i_data['trigger_bp'] = 37
            elif "Parasite" in val:
                i_data['inactive_bp'] = 68
                i_data['active_bp'] = 69
                i_data['trigger_bp'] = 70
            self.build_item_ui() 
            self.draw_grid()

        cb_preset.bind("<<ComboboxSelected>>", on_preset_select)
        
        tk.Label(p, text="(Custom values allowed)", fg="#777", bg="#1a1a1a", font=("Arial", 7)).pack(pady=(0,5))
        
        f = tk.Frame(p, bg="#1a1a1a"); f.pack(fill=tk.X, pady=5)

        tk.Label(f, text="Timer:", fg="white", bg="#1a1a1a").grid(row=0, column=0)
        e_cnt = tk.Entry(f, width=6); e_cnt.grid(row=0, column=1); e_cnt.insert(0, str(i_data['countdown']))

        lbl_mins = tk.Label(f, text="", bg="#1a1a1a", fg="#00FF00", font=("Arial", 8))
        lbl_mins.grid(row=0, column=2, padx=2)

        tk.Label(f, text="Type:", fg="white", bg="#1a1a1a").grid(row=0, column=3)
        e_typ = tk.Entry(f, width=6); e_typ.grid(row=0, column=4); e_typ.insert(0, str(i_data['type']))

        tk.Label(f, text="Off Model:", fg="white", bg="#1a1a1a").grid(row=1, column=0)
        e_ina = tk.Entry(f, width=6); e_ina.grid(row=1, column=1); e_ina.insert(0, str(i_data['inactive_bp']))

        tk.Label(f, text="On Model:", fg="white", bg="#1a1a1a").grid(row=1, column=3)
        e_act = tk.Entry(f, width=6); e_act.grid(row=1, column=4); e_act.insert(0, str(i_data['active_bp']))

        tk.Label(f, text="Trigger:", fg="white", bg="#1a1a1a").grid(row=2, column=0)
        e_trg = tk.Entry(f, width=6); e_trg.grid(row=2, column=1); e_trg.insert(0, str(i_data['trigger_bp']))

        def upd(ev=None):
            try:
                val = int(e_cnt.get())
                i_data['countdown'] = val
                lbl_mins.config(text=f"{val/60000:.1f}m")
                i_data['type'] = int(e_typ.get())
                i_data['inactive_bp'] = int(e_ina.get())
                i_data['active_bp'] = int(e_act.get())
                i_data['trigger_bp'] = int(e_trg.get())
                
                if i_data['inactive_bp'] == 35 and i_data['active_bp'] == 36 and i_data['trigger_bp'] == 37:
                    cb_preset.set("Standard (35/36/37)")
                elif i_data['inactive_bp'] == 68 and i_data['active_bp'] == 69 and i_data['trigger_bp'] == 70:
                    cb_preset.set("Parasite (68/69/70)")
                else:
                    cb_preset.set("")
                    
                self.upd_lbl()
            except: lbl_mins.config(text=f"ERR")
        upd();
        for e in [e_cnt, e_typ, e_ina, e_act, e_trg]: e.bind("<KeyRelease>", upd)

        def set_t(t): self.item_tool=t
        tk.Button(p, text="[ PLACE BOMB ]", command=lambda: set_t("ITEM"), bg="#FF00FF", fg="black").pack(fill=tk.X, pady=5)
        tk.Button(p, text="[ PLACE KEYSECT ]", command=lambda: set_t("KEY"), bg="#FF9900", fg="black").pack(fill=tk.X, pady=2)
        self.upd_lbl()
        self.draw_grid()

    def select_item_slot(self, slot):
        self.current_item_slot = slot; self.build_item_ui()

    # --- SQUAD UI ---
    def build_squad_ui(self):
        p = self.panels['SQUAD']
        for w in p.winfo_children(): w.destroy()

        tk.Label(p, text="SQUAD PLACER", bg="#FF4400", fg="black", font=("bold", 12)).pack(fill=tk.X, pady=(10,5))

        # Faction
        f_fac = tk.Frame(p, bg="#1a1a1a"); f_fac.pack(fill=tk.X, pady=2)
        tk.Label(f_fac, text="Owner:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        self.btn_squad_fac = tk.Menubutton(f_fac, text="1", bg="#333", fg="white", relief="raised")
        self.btn_squad_fac.pack(side=tk.LEFT, padx=5)

        def set_fac(f):
            if self.current_squad_index != -1:
                self.squads[self.current_squad_index]['owner'] = f
                self.refresh_squad_list()
            else:
                self.current_squad_data['owner'] = f
            self.btn_squad_fac.config(text=f"{f} ({FACTIONS[f][0]})", fg=FACTIONS[f][1] if FACTIONS[f][1] else "white")

        menu = tk.Menu(self.btn_squad_fac, tearoff=0)
        self.btn_squad_fac.configure(menu=menu)
        for i in range(1, 8):
            menu.add_command(label=f"{i} - {FACTIONS[i][0]}", command=lambda x=i: set_fac(x))
        
        curr = self.current_squad_data['owner']
        self.btn_squad_fac.config(text=f"{curr} ({FACTIONS[curr][0]})", fg=FACTIONS[curr][1] if FACTIONS[curr][1] else "white")

        # Vehicle
        f_veh = tk.Frame(p, bg="#1a1a1a"); f_veh.pack(fill=tk.X, pady=2)
        tk.Label(f_veh, text="Vehicle:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        veh_list = []
        sorted_vehs = sorted(self.defs['veh'].items())
        for vid, name in sorted_vehs:
            veh_list.append(f"{vid} - {name}")

        self.cb_veh = ttk.Combobox(f_veh, values=veh_list, width=25)
        self.cb_veh.pack(side=tk.LEFT, padx=5)

        curr_v = self.current_squad_data['veh']
        self.cb_veh.set(f"{curr_v} - {self.defs['veh'].get(curr_v, 'Unknown')}")

        def on_veh_change(ev):
            if self.current_squad_index != -1:
                val = self.cb_veh.get().strip()
                match = re.match(r'^(\d+)\s*-\s*(.*)$', val)
                if match:
                    self.squads[self.current_squad_index]['veh'] = int(match.group(1))
                    if match.group(2): self.squads[self.current_squad_index]['custom_name'] = match.group(2).strip()
                else:
                    try: 
                        self.squads[self.current_squad_index]['veh'] = int(val)
                        self.squads[self.current_squad_index]['custom_name'] = "Custom_Unit"
                    except: pass
                self.refresh_squad_list()
        self.cb_veh.bind("<<ComboboxSelected>>", on_veh_change)
        self.cb_veh.bind("<KeyRelease>", on_veh_change)

        tk.Label(p, text="To customize: Type 'ID - Name' directly above", fg="#aaa", bg="#1a1a1a", font=("Arial", 8, "italic")).pack(pady=(0,5))

        f_cnt = tk.Frame(p, bg="#1a1a1a"); f_cnt.pack(fill=tk.X, pady=2)
        tk.Label(f_cnt, text="Count:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)
        self.e_squad_cnt = tk.Entry(f_cnt, width=5); self.e_squad_cnt.pack(side=tk.LEFT, padx=5)
        self.e_squad_cnt.insert(0, str(self.current_squad_data['num']))

        def upd_cnt(ev):
            val = 1
            try: val = int(self.e_squad_cnt.get())
            except: pass
            
            if self.current_squad_index != -1:
                self.squads[self.current_squad_index]['num'] = val
                self.refresh_squad_list()
            else:
                self.current_squad_data['num'] = val
        self.e_squad_cnt.bind("<KeyRelease>", upd_cnt)

        # --- HIDDEN CHECKBOX ---
        f_opt = tk.Frame(p, bg="#1a1a1a"); f_opt.pack(fill=tk.X, pady=5)
        self.var_squad_hid = tk.BooleanVar(value=self.current_squad_data['hidden'])
        
        def tog_hid():
            val = self.var_squad_hid.get()
            if self.current_squad_index != -1:
                self.squads[self.current_squad_index]['hidden'] = val
                self.refresh_squad_list() 
            else:
                self.current_squad_data['hidden'] = val

        tk.Checkbutton(f_opt, text="Unknown (Hide in Briefing)", variable=self.var_squad_hid, command=tog_hid, bg="#1a1a1a", fg="white", selectcolor="#444").pack(anchor=tk.W, padx=5)

        f_list = tk.Frame(p, bg="#1a1a1a"); f_list.pack(fill=tk.BOTH, expand=True, padx=5)
        tk.Label(f_list, text="Placed Squads (Right-Click map to remove):", bg="#1a1a1a", fg="white").pack(anchor=tk.W)

        self.lb_squads = tk.Listbox(f_list, bg="#222", fg="white", height=10,
                                    selectbackground="#008888", selectforeground="white")
        self.lb_squads.pack(fill=tk.BOTH, expand=True)
        self.lb_squads.bind('<<ListboxSelect>>', self.on_squad_select)

        def delete_selected_squad():
            sel = self.lb_squads.curselection()
            if not sel: return
            idx = sel[0]
            self.squads.pop(idx)
            self.current_squad_index = -1 
            self.draw_grid()
            self.refresh_squad_list()
            self.var_squad_hid.set(self.current_squad_data['hidden'])

        tk.Button(f_list, text="[ DELETE SELECTED SQUAD ]", command=delete_selected_squad, bg="#880000", fg="white", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=5)
        self.refresh_squad_list()

    def on_squad_select(self, evt):
        sel = self.lb_squads.curselection()
        if sel:
            idx = sel[0]
            self.current_squad_index = idx
            s = self.squads[idx]
            
            self.var_squad_hid.set(s['hidden'])
            self.e_squad_cnt.delete(0, tk.END)
            self.e_squad_cnt.insert(0, str(s['num']))
            vname = s['custom_name'] if s['custom_name'] else self.defs['veh'].get(s['veh'], "Unknown")
            self.cb_veh.set(f"{s['veh']} - {vname}")
            f = s['owner']
            self.btn_squad_fac.config(text=f"{f} ({FACTIONS[f][0]})", fg=FACTIONS[f][1] if FACTIONS[f][1] else "white")

        else:
            self.current_squad_index = -1
        
        self.draw_grid()

    def refresh_squad_list(self):
        if not hasattr(self, 'lb_squads') or not self.lb_squads.winfo_exists(): return
        self.lb_squads.delete(0, tk.END)
        for i, s in enumerate(self.squads):
            vname = s['custom_name'] if s['custom_name'] else self.defs['veh'].get(s['veh'], "Unknown")
            
            hid_tag = "[H] " if s['hidden'] else ""
            txt = f"[{i}] {hid_tag}Own:{s['owner']} Veh:{s['veh']} ({vname}) Num:{s['num']}"
            self.lb_squads.insert(tk.END, txt)

            color = FACTION_TEXT_COLORS.get(s['owner'], "#FFFFFF")
            self.lb_squads.itemconfig(i, {'fg': color})
            
            if i == self.current_squad_index:
                self.lb_squads.selection_set(i)
                self.lb_squads.activate(i)

        self.draw_grid()

    # --- HOST STATION UI ---
    def build_host_ui(self):
        p = self.panels['HOST']
        for w in p.winfo_children(): w.destroy()

        tk.Label(p, text="HOST STATION PLACER", bg="#FFD700", fg="black", font=("bold", 12)).pack(fill=tk.X, pady=(10,5))

        # Faction
        f_fac = tk.Frame(p, bg="#1a1a1a"); f_fac.pack(fill=tk.X, pady=2)
        tk.Label(f_fac, text="Owner:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        self.btn_host_fac = tk.Menubutton(f_fac, text="1", bg="#333", fg="white", relief="raised")
        self.btn_host_fac.pack(side=tk.LEFT, padx=5)

        def set_host_fac(f):
            if self.current_host_index != -1:
                self.host_stations[self.current_host_index]['owner'] = f
                self.refresh_host_list()
            else:
                self.current_host_data['owner'] = f
            
            self.btn_host_fac.config(text=f"{f} ({FACTIONS[f][0]})", fg=FACTIONS[f][1] if FACTIONS[f][1] else "white")

        menu = tk.Menu(self.btn_host_fac, tearoff=0)
        self.btn_host_fac.configure(menu=menu)
        for i in range(1, 8):
            menu.add_command(label=f"{i} - {FACTIONS[i][0]}", command=lambda x=i: set_host_fac(x))
        
        curr = self.current_host_data['owner']
        self.btn_host_fac.config(text=f"{curr} ({FACTIONS[curr][0]})", fg=FACTIONS[curr][1] if FACTIONS[curr][1] else "white")

        # Vehicle Type
        f_veh = tk.Frame(p, bg="#1a1a1a"); f_veh.pack(fill=tk.X, pady=2)
        tk.Label(f_veh, text="Station Type:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        host_list = []
        sorted_hosts = sorted(self.defs['host'].items())
        for vid, name in sorted_hosts:
            host_list.append(f"{vid} - {name}")

        self.cb_host = ttk.Combobox(f_veh, values=host_list, width=25)
        self.cb_host.pack(side=tk.LEFT, padx=5)
        
        curr_v = self.current_host_data['veh']
        self.cb_host.set(f"{curr_v} - {self.defs['host'].get(curr_v, 'Unknown')}")

        def on_host_change(ev):
            if self.current_host_index != -1:
                val = self.cb_host.get().strip()
                match = re.match(r'^(\d+)\s*-\s*(.*)$', val)
                if match:
                    self.host_stations[self.current_host_index]['veh'] = int(match.group(1))
                    if match.group(2): self.host_stations[self.current_host_index]['custom_name'] = match.group(2).strip()
                else:
                    try: 
                        self.host_stations[self.current_host_index]['veh'] = int(val)
                        self.host_stations[self.current_host_index]['custom_name'] = "Custom_Host"
                    except: pass
                self.refresh_host_list()
        self.cb_host.bind("<<ComboboxSelected>>", on_host_change)
        self.cb_host.bind("<KeyRelease>", on_host_change)

        tk.Label(p, text="To customize: Type 'ID - Name' directly above", fg="#aaa", bg="#1a1a1a", font=("Arial", 8, "italic")).pack(pady=(0,5))

        # Energy & Altitude
        f_stats = tk.Frame(p, bg="#1a1a1a"); f_stats.pack(fill=tk.X, pady=2)

        tk.Label(f_stats, text="Energy:", fg="white", bg="#1a1a1a").grid(row=0, column=0, padx=5)
        self.e_host_en = tk.Entry(f_stats, width=10)
        self.e_host_en.grid(row=0, column=1, padx=5)
        self.e_host_en.insert(0, str(self.current_host_data['energy']))

        tk.Label(f_stats, text="Altitude (Y):", fg="white", bg="#1a1a1a").grid(row=0, column=2, padx=5)
        self.e_host_y = tk.Entry(f_stats, width=6)
        self.e_host_y.grid(row=0, column=3, padx=5)
        self.e_host_y.insert(0, str(self.current_host_data['pos_y']))

        tk.Label(f_stats, text="(Default: -330)", fg="#888", bg="#1a1a1a", font=("Arial", 8)).grid(row=0, column=4, padx=5)

        def upd_host_stats(ev):
            if self.current_host_index != -1:
                try:
                    self.host_stations[self.current_host_index]['energy'] = int(self.e_host_en.get())
                    self.host_stations[self.current_host_index]['pos_y'] = int(self.e_host_y.get())
                    self.refresh_host_list()
                except: pass
            else:
                try:
                    self.current_host_data['energy'] = int(self.e_host_en.get())
                    self.current_host_data['pos_y'] = int(self.e_host_y.get())
                except: pass
        self.e_host_en.bind("<KeyRelease>", upd_host_stats)
        self.e_host_y.bind("<KeyRelease>", upd_host_stats)

        # --- HOST HIDE OPTION ---
        f_opt = tk.Frame(p, bg="#1a1a1a"); f_opt.pack(fill=tk.X, pady=5)
        self.var_host_hid = tk.BooleanVar(value=self.current_host_data['hidden'])
        
        def tog_host_hid():
            val = self.var_host_hid.get()
            if self.current_host_index != -1:
                self.host_stations[self.current_host_index]['hidden'] = val
                self.refresh_host_list()
            else:
                self.current_host_data['hidden'] = val

        tk.Checkbutton(f_opt, text="Unknown (Hide in Briefing)", variable=self.var_host_hid, command=tog_host_hid, bg="#1a1a1a", fg="white", selectcolor="#444").pack(anchor=tk.W, padx=5)

        f_list = tk.Frame(p, bg="#1a1a1a"); f_list.pack(fill=tk.BOTH, expand=True, padx=5)
        tk.Label(f_list, text="Placed Host Stations:", bg="#1a1a1a", fg="white").pack(anchor=tk.W)

        self.lb_hosts = tk.Listbox(f_list, bg="#222", fg="white", height=6,
                                    selectbackground="#008888", selectforeground="white")
        self.lb_hosts.pack(fill=tk.BOTH, expand=True)
        self.lb_hosts.bind('<<ListboxSelect>>', self.on_host_select)

        def delete_selected_host():
            sel = self.lb_hosts.curselection()
            if not sel: return
            idx = sel[0]
            self.host_stations.pop(idx)
            self.current_host_index = -1
            self.draw_grid()
            self.refresh_host_list()
            self.var_host_hid.set(self.current_host_data['hidden'])

        tk.Button(f_list, text="[ DELETE SELECTED HOST ]", command=delete_selected_host, bg="#880000", fg="white", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=5)
        self.refresh_host_list()

    def on_host_select(self, evt):
        sel = self.lb_hosts.curselection()
        if sel:
            idx = sel[0]
            self.current_host_index = idx
            h = self.host_stations[idx]

            self.var_host_hid.set(h['hidden'])
            
            self.e_host_en.delete(0, tk.END); self.e_host_en.insert(0, str(h['energy']))
            self.e_host_y.delete(0, tk.END); self.e_host_y.insert(0, str(h['pos_y']))

            vname = h['custom_name'] if h['custom_name'] else self.defs['host'].get(h['veh'], "Unknown")
            self.cb_host.set(f"{h['veh']} - {vname}")

            f = h['owner']
            self.btn_host_fac.config(text=f"{f} ({FACTIONS[f][0]})", fg=FACTIONS[f][1] if FACTIONS[f][1] else "white")

        else:
            self.current_host_index = -1
        self.draw_grid()

    def refresh_host_list(self):
        if not hasattr(self, 'lb_hosts') or not self.lb_hosts.winfo_exists(): return
        self.lb_hosts.delete(0, tk.END)
        for i, h in enumerate(self.host_stations):
            vname = h['custom_name']
            if not vname: vname = self.defs['host'].get(h['veh'], "Unknown")

            hid_tag = "[H] " if h['hidden'] else ""
            txt = f"[{i}] {hid_tag}Own:{h['owner']} ID:{h['veh']} ({vname}) HP:{h['energy']}"
            self.lb_hosts.insert(tk.END, txt)

            color = FACTION_TEXT_COLORS.get(h['owner'], "#FFFFFF")
            self.lb_hosts.itemconfig(i, {'fg': color})
            
            if i == self.current_host_index:
                self.lb_hosts.selection_set(i)
                self.lb_hosts.activate(i)

        self.draw_grid()

    # --- GEM UI ---
    def build_gem_ui(self):
        p = self.panels['GEM']
        for w in p.winfo_children(): w.destroy()

        # 1. SLOTS
        f_slots = tk.Frame(p, bg="#1a1a1a"); f_slots.pack(fill=tk.X, pady=5)
        for i in range(1, self.visible_gem_slots + 1):
            bg = "#00FF00" if i == self.current_gem_slot else "#333"
            fg = "black" if i == self.current_gem_slot else "white"
            tk.Button(f_slots, text=str(i), bg=bg, fg=fg, width=2, command=lambda x=i: self.select_gem_slot(x)).pack(side=tk.LEFT, padx=1)

        if self.visible_gem_slots < 8:
            def add_slot():
                self.visible_gem_slots += 1; self.build_gem_ui()
            tk.Button(f_slots, text="+", bg="#005500", fg="white", width=2, command=add_slot).pack(side=tk.LEFT, padx=5)

        if self.visible_gem_slots > 1:
            def rem_slot():
                idx = self.visible_gem_slots
                self.gems[idx] = {'x': -1, 'y': -1, 'blg': 50, 'type': 3, 'actions': []}
                self.visible_gem_slots -= 1
                if self.current_gem_slot > self.visible_gem_slots: self.current_gem_slot = self.visible_gem_slots
                self.build_gem_ui(); self.draw_grid()
            tk.Button(f_slots, text="-", bg="#880000", fg="white", width=2, command=rem_slot).pack(side=tk.LEFT, padx=2)

        data = self.gems[self.current_gem_slot]

        # 2. PROPERTIES (ID & TYPE)
        f_prop = tk.Frame(p, bg="#1a1a1a"); f_prop.pack(fill=tk.X, pady=10)

        tk.Label(f_prop, text="Building ID:", fg="white", bg="#1a1a1a").grid(row=0, column=0, padx=5)

        e_blg = tk.Entry(f_prop, width=5)
        e_blg.grid(row=0, column=1, padx=5)
        e_blg.insert(0, str(data['blg']))

        def upd_b(ev):
            try: data['blg'] = int(e_blg.get())
            except: pass
        e_blg.bind("<KeyRelease>", upd_b)

        # TYPE DROPDOWN
        tk.Label(f_prop, text="Type:", fg="white", bg="#1a1a1a").grid(row=0, column=3, padx=5)
        type_map = {1: "1 (Weapon/Pwr)", 2: "2 (Shield)", 3: "3 (Tech/Unlock)"}
        rev_map = {v: k for k, v in type_map.items()}
        current_display = type_map.get(data['type'], "3 (Tech/Unlock)")
        type_var = tk.StringVar(value=current_display)
        def upd_t(val):
             data['type'] = rev_map.get(val, 3)
             self.upd_lbl(); self.draw_grid()
        om = ttk.OptionMenu(f_prop, type_var, current_display, *type_map.values(), command=upd_t)
        om.grid(row=0, column=4, padx=5)

        # 3. ACTIONS
        tk.Label(p, text="--- ACTIONS ---", fg="#00FF00", bg="#1a1a1a", font=("bold")).pack(pady=(15,5))
        f_act = tk.Frame(p, bg="#1a1a1a"); f_act.pack(fill=tk.X)

        f_act.grid_columnconfigure(0, minsize=50)
        f_act.grid_columnconfigure(1, minsize=140)
        f_act.grid_columnconfigure(2, minsize=50)

        # Define Variables first
        tgt_type_var = tk.StringVar(value="modify_vehicle")

        # UI Elements (Row 0)
        tk.Label(f_act, text="Modify:", fg="white", bg="#1a1a1a").grid(row=0, column=0, sticky="w")

        # Dropdown Modify
        om_mod = ttk.OptionMenu(f_act, tgt_type_var, "modify_vehicle", "modify_vehicle", "modify_building", "modify_weapon")
        om_mod.grid(row=0, column=1, sticky="ew")

        tk.Label(f_act, text="ID:", fg="white", bg="#1a1a1a").grid(row=0, column=2, sticky="e", padx=(0, 5))
        e_id = tk.Entry(f_act, width=4)
        e_id.grid(row=0, column=3, sticky="w")
        e_id.insert(0, "0") # Default is 0 per Action ID

        # UI Elements (Row 1)
        tk.Label(f_act, text="Do:", fg="white", bg="#1a1a1a").grid(row=1, column=0, sticky="w")

        param_combo = ttk.Combobox(f_act, values=["enable", "add_energy", "add_shield", "num_weapons"], width=15)
        param_combo.set("enable")
        param_combo.grid(row=1, column=1, sticky="ew")

        tk.Label(f_act, text="Val:", fg="white", bg="#1a1a1a").grid(row=1, column=2, sticky="e", padx=(0, 5))
        e_val = tk.Entry(f_act, width=6); e_val.grid(row=1, column=3, sticky="w")
        e_val.insert(0,"0")

        # Custom Definition Note
        tk.Label(f_act, text="(Custom definition allowed)", fg="#777", bg="#1a1a1a", font=("Arial", 7)).grid(row=2, column=1, sticky="w", pady=(0,5))

        # LOGIC FOR AUTO-UPDATE (Updates e_blg, NOT e_id)
        def on_modify_change(*args):
            sel = tgt_type_var.get()

            # 1. Update BUILDING ID (Visual) based on Type
            e_blg.delete(0, tk.END)
            if sel == "modify_building":
                e_blg.insert(0, "16")
                data['blg'] = 16
            elif sel == "modify_weapon":
                e_blg.insert(0, "15")
                data['blg'] = 15
            else: # modify_vehicle
                e_blg.insert(0, "50")
                data['blg'] = 50

            # 2. Update Parameter List (Do)
            if sel == "modify_vehicle":
                param_combo['values'] = ["enable", "add_energy", "add_shield", "num_weapons"]
                param_combo.set("enable")
            elif sel == "modify_building":
                param_combo['values'] = ["enable"]
                param_combo.set("enable")
            elif sel == "modify_weapon":
                param_combo['values'] = ["add_energy"]
                param_combo.set("add_energy")

        tgt_type_var.trace("w", on_modify_change)

        # LISTBOX & SCROLLBAR
        lb_frame = tk.Frame(p); lb_frame.pack(fill=tk.X, padx=5, pady=5)
        lb = tk.Listbox(lb_frame, height=5, bg="#222", fg="white", selectbackground="#008888", selectforeground="white", font=("Courier", 9))
        lb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sb = tk.Scrollbar(lb_frame, command=lb.yview, bg=SCROLL_BG, activebackground=SCROLL_ACTIVE, troughcolor="#444"); sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.config(yscrollcommand=sb.set)

        def refresh_list():
            lb.delete(0, tk.END)
            for a in data['actions']:
                tgt = a['target_type'].replace("modify_", "")
                lb.insert(tk.END, f"{tgt} {a['id']}: {a['param']}={a['val']}")

        def add_action():
            try:
                tid = int(e_id.get())
                val = e_val.get()
                prm = param_combo.get().strip()
                if not prm: return
                action = {'target_type': tgt_type_var.get(), 'id': tid, 'param': prm, 'val': val}
                data['actions'].append(action)
                refresh_list()
            except: messagebox.showerror("Error", "Invalid ID")

        def del_action():
            sel = lb.curselection()
            if sel: data['actions'].pop(sel[0]); refresh_list()

        refresh_list()
        f_btns = tk.Frame(p, bg="#1a1a1a"); f_btns.pack(fill=tk.X, pady=2)
        tk.Button(f_btns, text="ADD", command=add_action, bg="#005500", fg="white", width=8).pack(side=tk.LEFT, padx=10)
        tk.Button(f_btns, text="DEL", command=del_action, bg="#550000", fg="white", width=8).pack(side=tk.RIGHT, padx=10)

        # 4. PLACE BUTTON
        tk.Button(p, text="[ PLACE GEM ON MAP ]", command=lambda: self.set_gem_tool(), bg="#00FF00", fg="black", font=("bold")).pack(fill=tk.X, pady=10)
        self.upd_lbl()
        self.draw_grid()

    def select_gem_slot(self, slot):
        self.current_gem_slot = slot; self.build_gem_ui()

    def set_gem_tool(self):
        if not self.gems[self.current_gem_slot]['actions']:
             messagebox.showinfo("Error", "Define actions in the Upgrade panel first.")
             return
        self.gem_tool = "GEM"

    # --- TECH UI (UPDATED FOR DRONES) ---
    def build_tech_ui(self):
        p = self.panels['TECH']
        for w in p.winfo_children(): w.destroy()
        h = tk.Frame(p, bg="#1a1a1a", height=40); h.pack(fill=tk.X)
        
        # MOD: Nav Logic Range to 7 (Drones)
        def nav_tech(d):
            self.curr_tech_faction = 1 if self.curr_tech_faction+d > 7 else 7 if self.curr_tech_faction+d < 1 else self.curr_tech_faction+d
            self.update_tech_header(lbl_faction, lbl_num)
            self.draw_tech_list()
            self.upd_lbl()
            
        tk.Button(h, text="<", command=lambda: nav_tech(-1), bg="#333", fg="white", font=("bold",12)).pack(side=tk.LEFT, padx=10)
        lbl_num = tk.Label(h, text="01", bg="#333", font=("Arial", 14, "bold"), width=3); lbl_num.pack(side=tk.LEFT, padx=5)

        lbl_faction = tk.Label(h, text="", bg="#1a1a1a", font=("Arial", 12, "bold"), anchor=tk.W)
        lbl_faction.pack(side=tk.LEFT, expand=True, fill=tk.X)

        tk.Button(h, text=">", command=lambda: nav_tech(1), bg="#333", fg="white", font=("bold",12)).pack(side=tk.RIGHT, padx=10)
        self.update_tech_header(lbl_faction, lbl_num)

        f_cust = tk.Frame(p, bg="#1a1a1a"); f_cust.pack(fill=tk.X, pady=2)
        tk.Label(f_cust, text="Custom ID:", bg="#1a1a1a", fg="#aaa").pack(side=tk.LEFT, padx=5)
        e_cust = tk.Entry(f_cust, width=5); e_cust.pack(side=tk.LEFT)

        tk.Label(f_cust, text="Name:", fg="#aaa", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)
        e_name = tk.Entry(f_cust, width=12); e_name.pack(side=tk.LEFT)

        def add_cust_tech(kind):
            try:
                vid = int(e_cust.get())
                cname = e_name.get().strip()
                lst = self.tech[self.curr_tech_faction][kind]
                if cname: self.custom_tech_names[vid] = cname
                if vid not in lst: lst.append(vid)
                self.draw_tech_list()
            except: pass
        tk.Button(f_cust, text="+ VEH", command=lambda: add_cust_tech('veh'), bg="#444", fg="white", font=("Arial",7)).pack(side=tk.LEFT, padx=2)
        tk.Button(f_cust, text="+ BLG", command=lambda: add_cust_tech('blg'), bg="#444", fg="white", font=("Arial",7)).pack(side=tk.LEFT, padx=2)

        self.cv_tech = tk.Canvas(p, bg="#222", highlightthickness=0)
        self.sb_tech = tk.Scrollbar(p, command=self.cv_tech.yview, bg=SCROLL_BG, activebackground=SCROLL_ACTIVE, troughcolor='#444')
        self.cv_tech.configure(yscrollcommand=self.sb_tech.set)
        self.sb_tech.pack(side=tk.RIGHT, fill=tk.Y); self.cv_tech.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.cv_tech.bind("<Configure>", lambda e: self.draw_tech_list())
        self.bind_scroll(self.cv_tech)
        self.cv_tech.bind("<Button-1>", self.on_tech_click)

        self.root.after(50, self.draw_tech_list)

    def update_tech_header(self, lbl_name, lbl_n):
        fid = self.curr_tech_faction
        fname, fcolor = FACTIONS[fid]
        lbl_name.config(text=fname, fg=fcolor)
        lbl_n.config(text=f"{fid:02d}", fg=fcolor)

    def draw_tech_list(self,):
        if not hasattr(self, 'cv_tech') or not self.cv_tech.winfo_exists(): return
        self.cv_tech.delete("all")
        width = self.cv_tech.winfo_width()
        fid = self.curr_tech_faction

        if fid == 1: 
            active_bg = "#004444"
            active_outline = "#00FFFF"
            active_text = "#FFFFFF"
        else: 
            base_col = FACTIONS[fid][1] 
            active_bg = base_col 
            active_outline = "white"
            active_text = "black" if fid in [2, 3, 4] else "white"

        items = []
        for uid, name in self.defs['veh'].items():
             if uid in self.custom_tech_names: name = self.custom_tech_names[uid]
             items.append(('veh', uid, name))
        for uid, name in self.defs['blg'].items():
             if uid in self.custom_tech_names: name = self.custom_tech_names[uid]
             items.append(('blg', uid, name))

        active_veh = self.tech[fid]['veh']; active_blg = self.tech[fid]['blg']
        for vid in active_veh:
             if not any(i[0]=='veh' and i[1]==vid for i in items):
                 name = self.custom_tech_names.get(vid, f"Custom_{vid}")
                 items.append(('veh', vid, name))
        for bid in active_blg:
             if not any(i[0]=='blg' and i[1]==bid for i in items):
                 name = self.custom_tech_names.get(bid, f"Custom_{bid}")
                 items.append(('blg', bid, name))

        items.sort(key=lambda x: (0 if x[0]=='veh' else 1, x[1]))

        for i, (cat, uid, name) in enumerate(items):
            x, y = 10, i * TECH_ITEM_H + 5
            is_active = uid in (active_veh if cat=='veh' else active_blg)
            is_custom = uid in self.custom_tech_names

            if is_active:
                if is_custom: 
                    bg_color = "#440000"
                    border_color = "#FF0000"
                    text_color = "#FFCCCC"
                else:
                    bg_color = active_bg
                    border_color = active_outline
                    text_color = active_text
            else:
                bg_color = "#333333"
                border_color = "#555555"
                text_color = "#BBBBBB"

            line_w = 2 if is_active else 1
            tag = f"item_{cat}_{uid}"
            self.cv_tech.create_rectangle(x, y, x + TECH_ITEM_W, y + TECH_ITEM_H - 4, fill=bg_color, outline=border_color, width=line_w, tags=tag)
            prefix = "vehicle" if cat == "veh" else "building"
            self.cv_tech.create_text(x + 10, y + (TECH_ITEM_H/2) - 3, text=f"{prefix} = {uid} ; {name}", fill=text_color, anchor=tk.W, font=("Courier", 9, "bold" if is_active else "normal"), tags=tag)
        self.cv_tech.config(scrollregion=(0, 0, width, len(items) * TECH_ITEM_H + 20))

    def on_tech_click(self, e):
        self._last_dragged_id = None
        self.process_tech_hit(e.x, e.y)

    def process_tech_hit(self, x, y):
        cy = int(self.cv_tech.canvasy(y)); idx = cy // TECH_ITEM_H
        items = []
        for uid, name in self.defs['veh'].items(): items.append(('veh', uid))
        for uid, name in self.defs['blg'].items(): items.append(('blg', uid))
        active_veh = self.tech[self.curr_tech_faction]['veh']; active_blg = self.tech[self.curr_tech_faction]['blg']
        for vid in active_veh:
             if not any(i[0]=='veh' and i[1]==vid for i in items): items.append(('veh', vid))
        for bid in active_blg:
             if not any(i[0]=='blg' and i[1]==bid for i in items): items.append(('blg', bid))
        items.sort(key=lambda x: (0 if x[0]=='veh' else 1, x[1]))

        if 0 <= idx < len(items):
            cat, uid = items[idx]; unique_id = f"{cat}_{uid}"
            lst = self.tech[self.curr_tech_faction][cat]
            if uid in lst: lst.remove(uid)
            else: lst.append(uid)
            self.draw_tech_list()

    # --- SCRIPT UI ---
    def build_script_ui(self):
        p = self.panels['SCRIPT']
        for w in p.winfo_children(): w.destroy()

        tk.Label(p, text="LEVEL SCRIPT (LDF)", fg="#008080", bg="#1a1a1a", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(p, text="Write custom LDF commands here (e.g. includes):", fg="#aaa", bg="#1a1a1a", font=("Arial", 9)).pack(pady=2)

        txt = tk.Text(p, bg="#111", fg="#00FF00", font=("Courier", 10), insertbackground="white", height=20)
        txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        txt.insert("1.0", self.script_content)

        def save_script():
            self.script_content = txt.get("1.0", tk.END).strip()
            messagebox.showinfo("Script", "Script saved successfully!")

        tk.Button(p, text="SAVE SCRIPT", command=save_script, bg="#005555", fg="white", font=("bold")).pack(fill=tk.X, padx=5, pady=5)

    def draw_cell(self, c, r):
        sz = self.zoom_m; x, y = c*sz, r*sz; tag = f"c_{c}_{r}"
        self.cv_map.delete(tag)

        # RULER LOGIC
        if r == 0 or r == self.mh - 1 or c == 0 or c == self.mw - 1:
            self.cv_map.create_rectangle(x, y, x + sz, y + sz, fill="#151515", outline="#404040", tags=tag)
            h_val = self.grids['hgt'][r][c]
            h_user = h_val - HGT_MIN
            h_str = f"{h_user}"
            self.cv_map.create_text(x+3, y+2, text=h_str, fill=TEXT_COLOR, font=("Arial",max(6,sz//6),"bold"), anchor=tk.NW, tags=tag)
            
            txt = ""
            if (r == 0 or r == self.mh - 1) and (0 < c < self.mw - 1): txt = str(c)
            elif (c == 0 or c == self.mw - 1) and (0 < r < self.mh - 1): txt = str(r)
            if txt: self.cv_map.create_text(x + sz//2, y + sz//2, text=txt, fill="#00FFFF", font=("Arial", max(8, sz//3), "bold"), tags=tag)
            return

        # --- STANDARD MAP RENDERING (BASE LAYER) ---
        tid = self.grids['type'][r][c]
        
        # 1. Background Fill (Always standard dark grid to allow transparency)
        self.cv_map.create_rectangle(x,y,x+sz,y+sz, fill="#202020", outline="", tags=tag)

        # 2. Sector Image
        img = self.get_img('type', tid, sz)
        if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)

        # 3. Custom Sector Outline & Logic (Transparent center)
        is_custom_sector = tid not in self.lists['type']
        if is_custom_sector:
            # Only Red Border, no fill (Transparent)
            self.cv_map.create_rectangle(x,y,x+sz,y+sz, outline=CUSTOM_BORDER_COLOR, width=2, tags=tag)

        if self.clear_view: self.cv_map.create_rectangle(x,y,x+sz,y+sz, outline=GRID_COLOR, tags=tag); return

        # 4. Building Layer
        bid = self.grids['blg'][r][c]
        is_custom_building = (bid != '00' and bid not in self.lists['blg'])

        if bid!='00':
            img = self.get_img('blg', bid, sz)
            if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
            
            if is_custom_building:
                 self.cv_map.create_rectangle(x+1,y+1,x+sz-1,y+sz-1, outline=CUSTOM_BORDER_COLOR, width=3, tags=tag)
            else:
                 self.cv_map.create_rectangle(x+1,y+1,x+sz-1,y+sz-1, outline=MARKER_COLOR, width=2, tags=tag)

        # --- MOD: TEXT RENDERING PRIORITY & COLOR UNIFICATION ---
        # Rule: Show Building Text if present. Else Show Sector Text if present.
        # Color: Yellow (#FFFF00) for both.
        # Format: ID \n Name
        
        text_to_draw = None
        
        if is_custom_building:
            try:
                 val_int = int(bid, 16)
                 name = self.custom_definitions['blg'].get(val_int, "MOD")
            except: name = "MOD"
            text_to_draw = f"{bid}\n{name}"
            
        elif is_custom_sector:
            # Only draw sector text if building text is NOT drawn
            try:
                val_int = int(tid, 16)
                name = self.custom_definitions['type'].get(val_int, "MOD")
            except: name = "MOD"
            text_to_draw = f"{tid}\n{name}"

        if text_to_draw:
             f_size = max(8, sz // 4)
             self.cv_map.create_text(x+sz//2, y+sz//2, text=text_to_draw, fill="#FFFF00", font=("Arial", int(f_size), "bold"), justify=tk.CENTER, tags=tag)


        # --- GLOW LOGIC ---
        glow_width = 3

        # BEAMGATES
        for i in range(1, self.visible_gate_slots + 1):
            g = self.gates[i]
            if g['x'] == c and g['y'] == r:
                img = self.get_img('special', 'gate', sz)
                if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
                if self.mode == "GATE" and i == self.current_gate_slot:
                     self.cv_map.create_rectangle(x+2, y+2, x+sz-2, y+sz-2, outline="white", width=glow_width, tags=tag)

            if (c,r) in g['keys']:
                img = self.get_img('special', 'key', sz)
                if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
                if self.mode == "GATE" and i == self.current_gate_slot:
                     self.cv_map.create_rectangle(x+2, y+2, x+sz-2, y+sz-2, outline="white", width=glow_width, tags=tag)

        # BOMBS
        for i in range(1, self.visible_item_slots + 1):
            it = self.items[i]
            if it['x'] == c and it['y'] == r:
                img = self.get_img('special', 'item', sz)
                if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
                if self.mode == "ITEM" and i == self.current_item_slot:
                     self.cv_map.create_rectangle(x+2, y+2, x+sz-2, y+sz-2, outline="white", width=glow_width, tags=tag)

            if (c,r) in it['keys']:
                img = self.get_img('special', 'item_key', sz)
                if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
                if self.mode == "ITEM" and i == self.current_item_slot:
                     self.cv_map.create_rectangle(x+2, y+2, x+sz-2, y+sz-2, outline="white", width=glow_width, tags=tag)

        # GEMS
        for i in range(1, self.visible_gem_slots + 1):
            gm = self.gems[i]
            if gm['x'] == c and gm['y'] == r:
                img = self.get_img('special', 'gem', sz)
                if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
                if self.mode == "GEM" and i == self.current_gem_slot:
                     self.cv_map.create_rectangle(x+2, y+2, x+sz-2, y+sz-2, outline="white", width=glow_width, tags=tag)

        fid = self.grids['own'][r][c]
        if fid != 0:
            img = self.get_img('overlay', fid, sz)
            if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)

        # --- Height Border ---
        if self.mode == "HGT":
            h = self.grids['hgt'][r][c]
            if h!=127:
                img = self.get_img('hgt', h, sz)
                if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)

            h_norm = max(0, min(60, h - HGT_MIN))
            val = int((h_norm / 60) * 200) + 50
            hex_col = f"#{val:02x}{val:02x}{val:02x}"
            self.cv_map.create_rectangle(x+1, y+1, x+sz-1, y+sz-1, outline=hex_col, width=3, tags=tag)

        # HOST STATIONS
        hosts_here = [(i, h) for i, h in enumerate(self.host_stations) if h['x'] == c and h['y'] == r]
        if hosts_here:
            i, h = hosts_here[-1]
            f_col = FACTIONS[h['owner']][1] if FACTIONS[h['owner']][1] else "#FFF"
            self.cv_map.create_rectangle(x+2, y+2, x+sz-2, y+sz-2, outline=f_col, width=3, tags=tag)
            img = self.get_img('host', h['owner'], sz)
            if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
            vname = h['custom_name']
            if not vname: vname = self.defs['host'].get(h['veh'], "Unknown")
            txt_col = "black" if h['owner'] in [2,3,4] else "white"
            f_size = max(8, sz // 5)
            char_w = f_size * 0.7
            max_chars = int(sz / char_w)
            if len(vname) > max_chars: vname = vname[:max_chars-1] + "."
            text_pixel_w = len(vname) * char_w
            pad_x = 4; cx = x + sz // 2
            x1 = cx - (text_pixel_w // 2) - pad_x; x2 = cx + (text_pixel_w // 2) + pad_x
            x1 = max(x, x1); x2 = min(x+sz, x2)
            y1 = y + sz - (f_size + 6); y2 = y + sz - 1
            self.cv_map.create_rectangle(x1, y1, x2, y2, fill=f_col, outline="black", tags=tag)
            self.cv_map.create_text(cx, y + sz - (f_size//2) - 3, text=vname, fill=txt_col, font=("Arial", int(f_size), "bold"), tags=tag)
            if self.mode == "HOST" and i == self.current_host_index:
                 self.cv_map.create_rectangle(x+1, y+1, x+sz-1, y+sz-1, outline="white", width=2, tags=tag)

        # SQUADS
        squads_here = [(i, s) for i, s in enumerate(self.squads) if s['x'] == c and s['y'] == r]
        if squads_here:
            i, s = squads_here[-1]
            vname = s['custom_name']
            if not vname: vname = self.defs['veh'].get(s['veh'], "Unknown")
            col = FACTIONS[s['owner']][1] if FACTIONS[s['owner']][1] else "#FFF"
            txt_col = "black" if s['owner'] in [2,3,4] else "white"
            f_size = max(8, sz // 5)
            char_w = f_size * 0.7
            max_chars = int(sz / char_w)
            if len(vname) > max_chars: vname = vname[:max_chars-1] + "."
            text_pixel_w = len(vname) * char_w
            pad_x = 4; cx = x + sz // 2
            x1 = cx - (text_pixel_w // 2) - pad_x; x2 = cx + (text_pixel_w // 2) + pad_x
            x1 = max(x, x1); x2 = min(x+sz, x2)
            y1 = y + sz - (f_size + 6); y2 = y + sz - 1
            self.cv_map.create_rectangle(x1, y1, x2, y2, fill=col, outline="black", tags=tag)
            self.cv_map.create_text(cx, y + sz - (f_size//2) - 3, text=vname, fill=txt_col, font=("Arial", int(f_size), "bold"), tags=tag)
            if self.mode == "SQUAD" and i == self.current_squad_index:
                 self.cv_map.create_rectangle(x+1, y+1, x+sz-1, y+sz-1, outline="white", width=3, tags=tag)

        self.cv_map.create_rectangle(x,y,x+sz,y+sz, outline=GRID_COLOR, tags=tag)
        if sz>=32:
             h_user = self.grids['hgt'][r][c] - HGT_MIN
             txt = f"{h_user}"
             num_color = "#FF0000" if self.mode == "HGT" else TEXT_COLOR
             self.cv_map.create_text(x+3, y+2, text=txt, fill=num_color, font=("Arial",max(6,sz//6),"bold"), anchor=tk.NW, tags=tag)

    def draw_grid(self):
        if not hasattr(self, 'cv_map'): return
        self.cv_map.delete("all")
        rows = getattr(self, 'mh', DEFAULT_H)
        cols = getattr(self, 'mw', DEFAULT_W)
        for r in range(rows):
            for c in range(cols): self.draw_cell(c, r)

    def draw_palette(self, e=None):
        if self.mode in ["GATE", "ITEM", "TECH", "GEM", "SCRIPT", "SQUAD", "HOST"]: return

        self.cv_pal.delete("all")
        w = self.cv_pal.winfo_width() or 300
        sz = self.zoom_p
        cw, ch = sz+5, sz+25
        cols = max(1, w // (cw+5))
        items = self.get_current_items()

        if not items: return

        sel_val = self.sel['type'] if self.mode=="TYPE" else self.sel['own'] if self.mode=="OWN" else self.sel['hgt'] if self.mode=="HGT" else self.sel['blg']
        r, c = 0, 0
        for it in items:
            x, y = c*cw+10, r*ch+10
            if it==sel_val: self.cv_pal.create_rectangle(x-3,y-3,x+sz+3,y+sz+20, fill="#008080", outline="")

            img = None
            lbl = str(it)

            if self.mode=="TYPE": img = self.get_img('type', it, sz)
            elif self.mode=="OWN":
                 if it!=0: img = self.get_img('overlay', it, sz, 'pale'); lbl=f"{it:02d}"
            elif self.mode=="BLG":
                 if it!='00': img = self.get_img('blg', it, sz)
            elif self.mode=="HGT":
                 lbl = str(it - HGT_MIN)
                 img = self.get_img('hgt', it, sz)

            if img: self.cv_pal.create_image(x,y,image=img, anchor=tk.NW)
            else: self.cv_pal.create_rectangle(x,y,x+sz,y+sz, fill="#222", outline="#555")
            self.cv_pal.create_text(x+sz//2,y+sz+10, text=lbl, fill="white", font=("Arial",8,"bold"))
            tag = self.cv_pal.create_rectangle(x-3,y-3,x+sz+3,y+sz+20, fill="", outline="")
            self.cv_pal.tag_bind(tag, "<Button-1>", lambda e, i=it: self.set_sel(i))
            c+=1
            if c>=cols: c=0; r+=1
        content_h = (r+1)*ch+20
        canvas_h = self.cv_pal.winfo_height()
        if content_h <= canvas_h: self.cv_pal.config(scrollregion=(0, 0, w, canvas_h))
        else: self.cv_pal.config(scrollregion=(0, 0, w, content_h))

    # --- CORE LOGIC: THE 1200/700 FORMULA v11.0 ---
    def grid_to_world(self, col, row):
        STEP = 1200
        OFFSET = 700
        wx = (col * STEP) + OFFSET
        wz = -1 * ((row * STEP) + OFFSET)
        return wx, wz

    def world_to_grid(self, wx, wz):
        STEP = 1200
        OFFSET = 700
        col = int(round((wx - OFFSET) / STEP))
        row = int(round((abs(wz) - OFFSET) / STEP))
        return col, row

    # --- LIVE COORDINATE TRACKER ---
    def on_mouse_move(self, e):
        if self.mode in ["TYPE", "OWN", "BLG", "HGT"]: return

        cx = int(self.cv_map.canvasx(e.x)//self.zoom_m)
        cy = int(self.cv_map.canvasy(e.y)//self.zoom_m)
        world_x, world_z = self.grid_to_world(cx, cy)

        if hasattr(self, 'lbl_sel'):
            base_txt = self.lbl_sel.cget("text").split(" | ")[0]
            self.lbl_sel.config(text=f"{base_txt} | POS_X: {world_x}  POS_Z: {world_z}")

        # Auto-trigger move logic for Dragging
        if (self.mode == "SQUAD" or self.mode == "HOST") and str(e.type) == '6': self.on_click(e)

    def on_click(self, e):
        cx, cy = int(self.cv_map.canvasx(e.x)//self.zoom_m), int(self.cv_map.canvasy(e.y)//self.zoom_m)
        if not (0<=cx<self.mw and 0<=cy<self.mh): return

        # --- 1. GLOBAL BORDER PROTECTION (Except HGT) ---
        if self.mode != "HGT":
            if cx == 0 or cx == self.mw - 1 or cy == 0 or cy == self.mh - 1:
                if str(e.type) == '4':
                    messagebox.showwarning("Restricted Area", "Cannot modify map borders (Reserved for Logic)!")
                return

        # --- 2. GATES / ITEMS / GEMS HANDLING ---
        if self.mode in ["GATE", "ITEM", "GEM"]:
            tool = self.gate_tool if self.mode == "GATE" else self.item_tool if self.mode == "ITEM" else "GEM"
            data_list = self.gates if self.mode == "GATE" else self.items if self.mode == "ITEM" else self.gems
            current_slot = self.current_gate_slot if self.mode == "GATE" else self.current_item_slot if self.mode == "ITEM" else self.current_gem_slot
            current_data = data_list[current_slot]

            # A. MOTION (DRAGGING)
            if str(e.type) == '6':
                # 1. Key Dragging Logic (Always valid if dragging a key)
                if self.mode in ["GATE", "ITEM"] and self._drag_key_list is not None and self._drag_key_idx != -1:
                    if self._drag_key_idx < len(self._drag_key_list):
                        old_x, old_y = self._drag_key_list[self._drag_key_idx]
                        if (old_x != cx or old_y != cy):
                            self._drag_key_list[self._drag_key_idx] = (cx, cy)
                            self.draw_cell(old_x, old_y); self.draw_cell(cx, cy)
                    return
                
                # 2. Main Object Dragging Logic (ONLY if NOT using KEY tool)
                if tool != "KEY" and current_data['x'] != -1:
                        if current_data['x'] != cx or current_data['y'] != cy:
                             if not self.has_main_object(cx, cy, self.mode, current_slot):
                                 ox, oy = current_data['x'], current_data['y']
                                 current_data['x'], current_data['y'] = cx, cy
                                 self.draw_cell(ox, oy); self.draw_cell(cx, cy)
                return

            # B. CLICK (PLACEMENT)
            if str(e.type) == '4':
                if (self.mode == "GATE" and tool == "KEY") or (self.mode == "ITEM" and tool == "KEY"):
                    if current_data['x'] == cx and current_data['y'] == cy:
                        messagebox.showwarning("Error", "Cannot place Key on Parent Object!"); return
                    if self.has_key(cx, cy) and (cx, cy) not in current_data['keys']:
                        messagebox.showwarning("Occupied", "Tile has a Key!"); return
                    if self.has_main_object(cx, cy):
                        messagebox.showwarning("Occupied", "Cannot place Key on Object!"); return

                    if (cx, cy) in current_data['keys']:
                        self._drag_key_list = current_data['keys']
                        self._drag_key_idx = current_data['keys'].index((cx, cy))
                    else:
                        current_data['keys'].append((cx, cy))
                        self.draw_cell(cx, cy)
                    return
                else:
                    target_mode = self.mode
                    if target_mode == "GEM" and not current_data['actions']:
                         messagebox.showwarning("Error", "Cannot place Gem without actions!\nAdd actions in the panel first.")
                         return
                    if self.has_main_object(cx, cy, target_mode, current_slot):
                        messagebox.showwarning("Occupied", "Tile occupied!"); return
                    if target_mode in ["GATE", "ITEM"]:
                        if (cx, cy) in current_data['keys']:
                            messagebox.showwarning("Error", "Cannot place Object on its own Key!"); return

                    old_x, old_y = current_data['x'], current_data['y']
                    current_data['x'] = cx; current_data['y'] = cy
                    if old_x != -1: self.draw_cell(old_x, old_y)
                    self.draw_cell(cx, cy)
            return

        # --- 3. SQUAD HANDLING ---
        if self.mode == "SQUAD":
            if str(e.type) == '6': # Drag
                if hasattr(self, '_drag_squad_idx') and self._drag_squad_idx != -1:
                    idx = self._drag_squad_idx
                    if idx < len(self.squads):
                         if self.has_squad(cx, cy, exclude_index=idx): return
                         sq = self.squads[idx]; old_x, old_y = sq['x'], sq['y']
                         if old_x != cx or old_y != cy:
                            sq['x'], sq['y'] = cx, cy
                            self.draw_cell(old_x, old_y); self.draw_cell(cx, cy)
                return

            if str(e.type) == '4': # Click
                clicked_squad_index = -1
                for i, s in enumerate(self.squads):
                    if s['x'] == cx and s['y'] == cy: clicked_squad_index = i; break

                if clicked_squad_index != -1:
                    self.lb_squads.selection_clear(0, tk.END)
                    self.lb_squads.selection_set(clicked_squad_index)
                    self.lb_squads.activate(clicked_squad_index)
                    self.lb_squads.see(clicked_squad_index)
                    self.current_squad_index = clicked_squad_index
                    self._drag_squad_idx = clicked_squad_index
                    self.draw_grid()
                    return

                if self.has_squad(cx, cy):
                    messagebox.showwarning("Occupied", "Tile occupied!"); return

                # CUSTOM ID/NAME PARSING (SQUAD)
                combo_val = self.cb_veh.get().strip()
                parsed_id = 1; parsed_name = None
                
                # Regex for "ID - Name" pattern
                match = re.match(r'^(\d+)\s*-\s*(.*)$', combo_val)
                if match:
                    parsed_id = int(match.group(1))
                    nm = match.group(2).strip()
                    # If regex matched, we prioritize this name as custom if it exists
                    if nm: parsed_name = nm
                else:
                    # Fallback for just an ID number
                    try:
                        parsed_id = int(combo_val)
                        if parsed_id not in self.defs['veh']: parsed_name = "Custom_Unit"
                    except: pass

                self.current_squad_data['veh'] = parsed_id
                self.current_squad_data['custom_name'] = parsed_name
                new_sq = copy.deepcopy(self.current_squad_data)
                new_sq['x'], new_sq['y'] = cx, cy
                self.squads.append(new_sq)
                self.draw_cell(cx, cy); self.refresh_squad_list()
            return

        # --- 4. HOST STATION HANDLING ---
        if self.mode == "HOST":
            if str(e.type) == '6': # Drag
                if hasattr(self, '_drag_host_idx') and self._drag_host_idx != -1:
                    idx = self._drag_host_idx
                    if idx < len(self.host_stations):
                         if self.has_host(cx, cy, exclude_index=idx): return
                         hst = self.host_stations[idx]; old_x, old_y = hst['x'], hst['y']
                         if old_x != cx or old_y != cy:
                            hst['x'], hst['y'] = cx, cy
                            self.draw_cell(old_x, old_y); self.draw_cell(cx, cy)
                return

            if str(e.type) == '4': # Click
                clicked_host_index = -1
                for i, h in enumerate(self.host_stations):
                    if h['x'] == cx and h['y'] == cy: clicked_host_index = i; break

                if clicked_host_index != -1:
                    self.lb_hosts.selection_clear(0, tk.END)
                    self.lb_hosts.selection_set(clicked_host_index)
                    self.lb_hosts.activate(clicked_host_index)
                    self.lb_hosts.see(clicked_host_index)
                    self.current_host_index = clicked_host_index
                    self._drag_host_idx = clicked_host_index
                    self.draw_grid()
                    return

                if self.has_host(cx, cy):
                    messagebox.showwarning("Occupied", "Tile occupied!"); return

                # CUSTOM ID/NAME PARSING (HOST)
                combo_val = self.cb_host.get().strip()
                parsed_id = 56; parsed_name = None
                
                # Regex for "ID - Name" pattern
                match = re.match(r'^(\d+)\s*-\s*(.*)$', combo_val)
                if match:
                    parsed_id = int(match.group(1))
                    nm = match.group(2).strip()
                    if nm: parsed_name = nm
                else:
                    try:
                        parsed_id = int(combo_val)
                        if parsed_id not in self.defs['host']: parsed_name = "Custom_Host"
                    except: pass

                self.current_host_data['veh'] = parsed_id
                self.current_host_data['custom_name'] = parsed_name
                new_hst = copy.deepcopy(self.current_host_data)
                new_hst['x'], new_hst['y'] = cx, cy

                self.host_stations.append(new_hst)
                self.draw_cell(cx, cy); self.refresh_host_list()
            return

        # --- 5. TILE PAINTING ---
        if self.mode in ["TECH", "SCRIPT"]: return

        if self.mode=="TYPE": self.grids['type'][cy][cx]=self.sel['type']
        elif self.mode=="OWN": self.grids['own'][cy][cx]=self.sel['own']
        elif self.mode=="HGT": self.grids['hgt'][cy][cx] = max(HGT_MIN, min(HGT_MAX, self.sel['hgt']))
        elif self.mode=="BLG": self.grids['blg'][cy][cx]=self.sel['blg']
        self.draw_cell(cx, cy)

    def on_right_click(self, e):
        cx, cy = int(self.cv_map.canvasx(e.x)//self.zoom_m), int(self.cv_map.canvasy(e.y)//self.zoom_m)
        if not (0<=cx<self.mw and 0<=cy<self.mh): return

        # SQUAD REMOVAL
        if self.mode == "SQUAD":
             self.lb_squads.selection_clear(0, tk.END); self.current_squad_index = -1; self.draw_grid()
             for i in reversed(range(len(self.squads))):
                    s = self.squads[i]
                    if s['x'] == cx and s['y'] == cy:
                        self.squads.pop(i); self.draw_cell(cx, cy); self.refresh_squad_list(); break
             return

        # HOST REMOVAL
        if self.mode == "HOST":
             self.lb_hosts.selection_clear(0, tk.END); self.current_host_index = -1; self.draw_grid()
             for i in reversed(range(len(self.host_stations))):
                    h = self.host_stations[i]
                    if h['x'] == cx and h['y'] == cy:
                        self.host_stations.pop(i); self.draw_cell(cx, cy); self.refresh_host_list(); break
             return

        if self.mode in ["TYPE", "OWN", "BLG", "HGT"]: self.pick(e); return
        if self.mode == "GATE":
            for i, g in self.gates.items():
                if g['x'] == cx and g['y'] == cy: g['x'] = -1; g['y'] = -1; self.draw_cell(cx, cy); return
                if (cx, cy) in g['keys']: g['keys'].remove((cx, cy)); self.draw_cell(cx, cy); return
        elif self.mode == "ITEM":
            for i, it in self.items.items():
                if it['x'] == cx and it['y'] == cy: it['x'] = -1; it['y'] = -1; self.draw_cell(cx, cy); return
                if (cx, cy) in it['keys']: it['keys'].remove((cx, cy)); self.draw_cell(cx, cy); return
        elif self.mode == "GEM":
            for i, gm in self.gems.items():
                if gm['x'] == cx and gm['y'] == cy: gm['x'] = -1; gm['y'] = -1; self.draw_cell(cx, cy); return

    def handle_special_click(self, cx, cy, data_dict, tool_type):
        if tool_type.endswith("GATE") or tool_type.endswith("ITEM"):
            if data_dict['x'] != -1: ox, oy = data_dict['x'], data_dict['y']; data_dict['x'] = -1; self.draw_cell(ox, oy)
            data_dict['x'], data_dict['y'] = cx, cy
        elif "KEY" in tool_type:
            if (cx,cy) in data_dict['keys']: data_dict['keys'].remove((cx,cy))
            else: data_dict['keys'].append((cx,cy))
        self.draw_cell(cx, cy)

    def pick(self, e):
        cx, cy = int(self.cv_map.canvasx(e.x)//self.zoom_m), int(self.cv_map.canvasy(e.y)//self.zoom_m)
        if 0<=cx<self.mw:
            if self.mode=="TYPE": self.sel['type']=self.grids['type'][cy][cx]
            elif self.mode=="OWN": self.sel['own']=self.grids['own'][cy][cx]
            elif self.mode=="HGT":
                new_hgt = self.grids['hgt'][cy][cx]; self.sel['hgt']=new_hgt;
                if hasattr(self, 'hgt_entry'):
                    user_val = new_hgt - HGT_MIN
                    self.hgt_entry.delete(0, tk.END); self.hgt_entry.insert(0, str(user_val))
            elif self.mode=="BLG": self.sel['blg']=self.grids['blg'][cy][cx]
            self.upd_lbl(); self.draw_palette()

    def set_sel(self, val):
        if self.mode=="TYPE": self.sel['type']=val
        elif self.mode=="OWN": self.sel['own']=val
        elif self.mode=="HGT": self.sel['hgt']=val
        elif self.mode=="BLG": self.sel['blg']=val
        self.upd_lbl(); self.draw_palette()

    def cycle_sel(self, d):
        items = self.get_current_items();
        if not items: return
        curr = self.sel['type'] if self.mode=="TYPE" else self.sel['own'] if self.mode=="OWN" else self.sel['hgt'] if self.mode=="HGT" else self.sel['blg']
        try: idx = items.index(curr); new_idx = (idx + d) % len(items); new_val = items[new_idx]; self.set_sel(new_val)
        except ValueError: self.set_sel(items[0])

    def zoom_pal(self, d): self.zoom_p = max(32, min(256, self.zoom_p+d)); self.draw_palette()
    def zoom_map(self, d):
        self.zoom_m = max(48, min(192, self.zoom_m+d))
        self.draw_grid(); self.cv_map.config(scrollregion=(0,0,self.mw*self.zoom_m, self.mh*self.zoom_m))

    def toggle_clear(self):
        self.clear_view = not self.clear_view
        self.btn_cl.config(bg="#00FF00" if self.clear_view else "#444"); self.draw_grid()

    def bind_scroll(self, w):
        w.bind("<Button-4>", lambda e: w.yview_scroll(-1,"units"))
        w.bind("<Button-5>", lambda e: w.yview_scroll(1,"units"))
        w.bind("<MouseWheel>", lambda e: w.yview_scroll(int(-1*(e.delta/120)),"units"))
        w.bind("<Motion>", self.on_mouse_move)

    def ask_set(self):
        n = simpledialog.askinteger("Sektor", "Select Set (1-6):", minvalue=1, maxvalue=6, initialvalue=1)
        return f"set{n}" if n else None

    def ask_dims(self):
        w = simpledialog.askinteger("Sektor", "W:", initialvalue=DEFAULT_W, minvalue=10)
        h = simpledialog.askinteger("Sektor", "H:", initialvalue=DEFAULT_H, minvalue=10)
        if w and h: self.mw, self.mh = w, h; self.reset_map(False)
        else: self.root.destroy()

    def resize_map_dialog(self):
        w = simpledialog.askinteger("Resize Map", "New Width:", initialvalue=self.mw, minvalue=10)
        h = simpledialog.askinteger("Resize Map", "New Height:", initialvalue=self.mh, minvalue=10)
        
        if w and h:
            old_w, old_h = self.mw, self.mh
            new_grids = {
                'type': [['00'] * w for _ in range(h)],
                'own': [[0] * w for _ in range(h)],
                'hgt': [[DEFAULT_HGT] * w for _ in range(h)],
                'blg': [['00'] * w for _ in range(h)]
            }

            copy_w = min(old_w, w)
            copy_h = min(old_h, h)

            for r in range(copy_h):
                for c in range(copy_w):
                    new_grids['type'][r][c] = self.grids['type'][r][c]
                    new_grids['own'][r][c] = self.grids['own'][r][c]
                    new_grids['hgt'][r][c] = self.grids['hgt'][r][c]
                    new_grids['blg'][r][c] = self.grids['blg'][r][c]

            self.mw, self.mh = w, h
            self.grids = new_grids
            self.apply_borders() 
            self.draw_grid()
            messagebox.showinfo("Resized", f"Map resized to {w}x{h}")

    def reset_map(self, confirm=True):
        if confirm and not messagebox.askyesno("RESET", "Wipe map?"): return
        self.grids = { 'type': [['00'] * self.mw for _ in range(self.mh)], 'own': [[0] * self.mw for _ in range(self.mh)], 'hgt': [[DEFAULT_HGT] * self.mw for _ in range(self.mh)], 'blg': [['00'] * self.mw for _ in range(self.mh)] }
        self.apply_borders()
        self.gates = {i: {'active': False, 'x': -1, 'y': -1, 'keys': [], 'target': 0, 'closed_bp': 25, 'opened_bp': 26} for i in range(1, 9)}
        self.items = {i: {'active': False, 'x': -1, 'y': -1, 'keys': [], 'countdown': 300000, 'inactive_bp': 35, 'active_bp': 36, 'trigger_bp': 37, 'type': 1} for i in range(1, 9)}
        self.gems = {i: {'x': -1, 'y': -1, 'blg': 50, 'type': 3, 'actions': []} for i in range(1, 9)}
        self.visible_gate_slots = 1; self.visible_item_slots = 1; self.visible_gem_slots = 1
        self.squads = []; self.current_squad_index = -1
        self.host_stations = []; self.current_host_index = -1
        if hasattr(self, 'cv_map'): self.draw_grid()

    def apply_borders(self):
        w, h = self.mw, self.mh
        for r in range(h):
            for c in range(w):
                if r == 0: t = 'f8' if c == 0 else 'f9' if c == w - 1 else 'fc'
                elif r == h - 1: t = 'fb' if c == 0 else 'fa' if c == w - 1 else 'fe'
                elif c == 0: t = 'ff'
                elif c == w - 1: t = 'fd'
                else: continue
                self.grids['type'][r][c] = t

    def fill_map(self):
        if self.mode in ["GATE", "ITEM", "TECH", "GEM", "SCRIPT", "SQUAD", "HOST"]: return
        if messagebox.askyesno("Confirm", "Fill map (no borders)?"):
            for r in range(self.mh):
                for c in range(self.mw):
                    if not (r == 0 or r == self.mh - 1 or c == 0 or c == self.mw - 1):
                        if self.mode == "TYPE": self.grids['type'][r][c] = self.sel['type']
                        elif self.mode == "OWN": self.grids['own'][r][c] = self.sel['own']
                        elif self.mode == "HGT": self.grids['hgt'][r][c] = self.sel['hgt']
                        elif self.mode == "BLG": self.grids['blg'][r][c] = self.sel['blg']
            self.draw_grid()

    def edit_info(self):
        win = tk.Toplevel(self.root); win.title("Level Info"); win.geometry("500x700"); win.configure(bg="#222")

        # TITLE
        tk.Label(win, text="Level Title:", bg="#222", fg="white").pack(pady=5)
        e_title = tk.Entry(win, width=40); e_title.pack(); e_title.insert(0, self.lvl_info['title'])

        # MAP FILES
        f_maps = tk.Frame(win, bg="#222"); f_maps.pack(pady=10)
        tk.Label(f_maps, text="Briefing Map (MB):", bg="#222", fg="#AAA").grid(row=0, column=0, padx=5)
        e_mb = tk.Entry(f_maps, width=20); e_mb.grid(row=0, column=1); e_mb.insert(0, self.lvl_info.get('mbmap', 'MB_53.IFF'))
        tk.Label(f_maps, text="Debriefing Map (DB):", bg="#222", fg="#AAA").grid(row=1, column=0, padx=5)
        e_db = tk.Entry(f_maps, width=20); e_db.grid(row=1, column=1); e_db.insert(0, self.lvl_info.get('dbmap', 'DB_53.IFF'))

        # SKY SELECTION
        f_sky_lbl = tk.Frame(win, bg="#222"); f_sky_lbl.pack(pady=(10,0))
        tk.Label(f_sky_lbl, text="Select Sky:", bg="#222", fg="white", font=("bold", 11)).pack(side=tk.LEFT, padx=5)
        
        current_sky_name = os.path.basename(self.lvl_info['sky']).replace(".base", "").replace(".bas", "")
        lbl_sky_current = tk.Label(f_sky_lbl, text=f"[{current_sky_name}]", bg="#222", fg="#00FF00", font=("Arial", 10))
        lbl_sky_current.pack(side=tk.LEFT)

        fr_sky = tk.Frame(win, bg="#333", bd=2, relief="sunken"); fr_sky.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        cv_s = tk.Canvas(fr_sky, bg="#111", highlightthickness=0); sb_s = tk.Scrollbar(fr_sky, command=cv_s.yview)
        cv_s.config(yscrollcommand=sb_s.set); sb_s.pack(side=tk.RIGHT, fill=tk.Y)
        sb_s.config(bg=SCROLL_BG, activebackground=SCROLL_ACTIVE, troughcolor="#444")
        cv_s.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def draw_skies():
            cv_s.delete("all"); w = cv_s.winfo_width()
            if w < 50: w = 400
            sky_w, sky_h = 140, 90; cols = max(1, w // (sky_w + 10)); r, c = 0, 0
            
            raw_sky = self.lvl_info['sky'].lower().replace("\\", "/")
            base_name = os.path.basename(raw_sky)
            curr_sel = os.path.splitext(base_name)[0]

            for f in self.lists['sky']:
                file_base_name = os.path.splitext(f)[0]
                x, y = c * (sky_w + 10) + 10, r * (sky_h + 10) + 10
                is_selected = (file_base_name.lower() == curr_sel.lower())
                fill_color = "#004400" if is_selected else "#333"
                border_color = "#00FF00" if is_selected else "#555"
                tag = f"sky_{file_base_name}"
                cv_s.create_rectangle(x, y, x + sky_w, y + sky_h, fill=fill_color, outline=border_color, width=2, tags=tag)
                
                if file_base_name not in self.sky_previews:
                    try: 
                        path = os.path.join("skies", f)
                        img = Image.open(path).resize((130, 70), Image.Resampling.LANCZOS)
                        self.sky_previews[file_base_name] = ImageTk.PhotoImage(img)
                    except: 
                        img = Image.new("RGB", (130, 70), "#300")
                        self.sky_previews[file_base_name] = ImageTk.PhotoImage(img)
                
                cv_s.create_image(x + sky_w//2, y + 40, image=self.sky_previews[file_base_name], tags=tag)
                cv_s.create_text(x + sky_w//2, y + sky_h - 10, text=file_base_name, fill="white", font=("Arial", 9), tags=tag)
                cv_s.tag_bind(tag, "<Button-1>", lambda e, s=file_base_name: select_sky(s))
                c += 1;
                if c >= cols: c = 0; r += 1
            cv_s.config(scrollregion=(0,0,w, (r+1)*(sky_h+10) + 20))

        def select_sky(name): 
            self.lvl_info['sky'] = f"objects/{name}.bas"
            lbl_sky_current.config(text=f"[{name}]")
            draw_skies()

        cv_s.bind("<Configure>", lambda e: draw_skies()); self.bind_scroll(cv_s); win.after(100, draw_skies)
        
        f_media = tk.Frame(win, bg="#222"); f_media.pack(fill=tk.X, pady=10)
        tk.Label(f_media, text="Ambience Track:", bg="#222", fg="#AAA").grid(row=0, column=0, padx=5, sticky="e")
        music_options = ["None", "2", "3", "4", "5", "6"]
        cb_music = ttk.Combobox(f_media, values=music_options, width=15) 
        cb_music.grid(row=0, column=1, padx=5, sticky="w")
        cb_music.set(self.lvl_info.get('music', "None"))

        tk.Label(f_media, text="Intro Movie:", bg="#222", fg="#AAA").grid(row=1, column=0, padx=5, sticky="e")
        movie_options = ["None", "intro.mpg", "logo.mpg", "tut1.mpg", "tut2.mpg", "tut3.mpg", "tut4.mpg", "tut5.mpg", "tut6.mpg", "tut7.mpg", "tut8.mpg", "win.mpg", "lose.mpg"]
        cb_movie = ttk.Combobox(f_media, values=movie_options, width=20) 
        cb_movie.grid(row=1, column=1, padx=5, sticky="w")
        
        current_movie = self.lvl_info.get('movie', "None")
        if current_movie.lower().startswith("mov/"): current_movie = current_movie[4:] 
        elif current_movie.lower().startswith("mov:"): current_movie = current_movie[4:]
        cb_movie.set(current_movie)

        tk.Label(f_media, text="(You can select from list or type custom values)", bg="#222", fg="#777", font=("Arial", 8)).grid(row=2, column=0, columnspan=2, pady=5)

        def save():
            self.lvl_info['title'] = e_title.get()
            self.lvl_info['mbmap'] = e_mb.get().strip() or "MB_53.IFF"
            self.lvl_info['dbmap'] = e_db.get().strip() or "DB_53.IFF"
            self.lvl_info['music'] = cb_music.get()
            
            raw_movie = cb_movie.get().strip()
            if raw_movie == "None" or raw_movie == "":
                self.lvl_info['movie'] = "None"
            else:
                if not raw_movie.lower().startswith("mov/") and not raw_movie.lower().startswith("mov:"):
                     self.lvl_info['movie'] = f"mov/{raw_movie}"
                else:
                     self.lvl_info['movie'] = raw_movie.replace(":", "/")

            win.destroy(); messagebox.showinfo("Success", "Level Info Updated!")
        
        tk.Button(win, text="CONFIRM", command=save, bg="#008800", fg="white", width=20).pack(pady=15)

    def reload_assets(self):
        self.assets = {}
        self.lists = {'type':[], 'blg':['00'], 'sky':[], 'gem_graphics': []}
        self.cache = {}

        def load_icon(filename, key, fallback_col, fallback_txt):
            path = os.path.join("icons", filename)
            if os.path.exists(path):
                self.assets[key] = Image.open(path)
            else:
                img = Image.new("RGBA", (64,64), (0,0,0,0)); d = ImageDraw.Draw(img)
                d.rectangle([4,4,60,60], outline=fallback_col, width=4)
                d.text((10,20), fallback_txt, fill=fallback_col)
                self.assets[key] = img

        for i in range(1, 9):
            key = f"overlay_{i}"
            col_hex = FACTIONS.get(i, ["Unknown", "#888888"])[1]
            if col_hex.startswith("#"): col_hex = col_hex[1:]
            if len(col_hex) == 3: col_hex = "".join([c*2 for c in col_hex]) 
            try: r, g, b = tuple(int(col_hex[j:j+2], 16) for j in (0, 2, 4))
            except: r, g, b = (128, 128, 128)
            if i in [1, 2, 4, 6, 7]: alpha = 40 
            else: alpha = 90 
            img = Image.new("RGBA", (64, 64), (r, g, b, alpha))
            self.assets[str(i)] = img 

        if os.path.exists(self.set_folder):
            for f in sorted(os.listdir(self.set_folder)):
                if f.lower().endswith(('.png','.jpg')):
                    key = os.path.splitext(f)[0]
                    self.assets[key] = Image.open(os.path.join(self.set_folder, f))
                    self.lists['type'].append(key)
        if self.lists['type']: self.sel['type'] = self.lists['type'][0]

        for f in sorted(os.listdir("buildings")):
            if f.lower().endswith(('.png','.jpg')):
                key = os.path.splitext(f)[0]
                self.assets[f"blg_{key}"] = Image.open(os.path.join("buildings", f))
                if key not in self.lists['blg']: self.lists['blg'].append(key)

        if os.path.exists("gems"):
            for f in sorted(os.listdir("gems")):
                if f.lower().endswith('.png'):
                    key = os.path.splitext(f)[0]
                    try:
                        self.assets[f"gem_graphic_{key}"] = Image.open(os.path.join("gems", f))
                        self.lists['gem_graphics'].append(key)
                    except: pass

        if os.path.exists("skies"):
            self.lists['sky'] = [f for f in sorted(os.listdir("skies")) if f.lower().endswith(('.png','.jpg','.jpeg'))]

        if not os.path.exists("icons"): os.makedirs("icons")
        load_icon("custom_sector.png", "custom_sector", "#FF0000", "SEC\nMOD")
        load_icon("custom_building.png", "custom_building", "#FF0000", "BLG\nMOD")
        load_icon("custom.png", "custom_mod", "#FF00FF", "MOD")
        load_icon("gate.png", "gate", "#00FFFF", "GATE")
        load_icon("key.png", "key", "#FFFF00", "KEY")
        load_icon("superitem.png", "item", "#FF00FF", "ITEM")
        load_icon("superitem_key.png", "item_key", "#FF9900", "KEY")
        load_icon("gem.png", "gem", "#00FF00", "GEM")

        for i in range(1, 9):
            fac_col = FACTIONS[i][1] if i in FACTIONS and FACTIONS[i][1] else "#FFF"
            load_icon(f"host_{i}.png", f"host_{i}", fac_col, f"HOST\n{i}")

        self.draw_palette()
        self.draw_grid()
        self.update_window_title()

    def load_map(self):
        filename = filedialog.askopenfilename()
        if not filename: return
        try:
            with open(filename, 'r', errors='ignore') as f: raw_text = f.read()

            set_match = re.search(r'set\s*=\s*(\d+)', raw_text, re.IGNORECASE)
            if set_match:
                detected_set_num = int(set_match.group(1))
                new_set_folder = f"set{detected_set_num}"
                if new_set_folder != self.set_folder:
                    if os.path.exists(new_set_folder):
                        self.set_folder = new_set_folder
                        self.reload_assets()
                        messagebox.showinfo("Set Detected", f"Switched to Set {detected_set_num}")
                    else:
                        messagebox.showwarning("Missing Set", f"Map uses Set {detected_set_num}, but folder not found. Displaying current set assets ({self.set_folder.upper()}).")

            clean_text = re.sub(r';.*', '', raw_text)
            clean_text = clean_text.replace('=', ' = ')
            tokens = clean_text.split()

            w, h = 0, 0
            temp_iter = iter(tokens)
            while True:
                try:
                    tok = next(temp_iter)
                    if tok.lower() == 'typ_map':
                        nxt = next(temp_iter)
                        if nxt == '=': w = int(next(temp_iter)); h = int(next(temp_iter))
                        else: w = int(nxt); h = int(next(temp_iter))
                        break
                except StopIteration: break

            if w == 0 or h == 0: messagebox.showerror("Error", "Could not determine map size"); return
            self.mw, self.mh = w, h; self.reset_map(confirm=False)

            iterator = iter(tokens)
            grids_loaded = {}
            current_gate = None; current_item = None; current_gem = None; current_squad = None; current_host = None
            current_action_context = None

            reading_level = False
            reading_mb = False
            reading_db = False

            def get_val(itr):
                v = next(itr); return next(itr) if v == '=' else v

            while True:
                try:
                    token = next(iterator)
                    token_lower = token.lower()

                    if token_lower == 'begin_squad':
                        current_squad = {'owner':1, 'veh':1, 'num':1, 'hidden':False, 'custom_name':None, 'x':-1, 'y':-1}

                    elif token_lower == 'begin_robo':
                        current_host = {'owner':1, 'veh':56, 'energy':500000, 'pos_y':-330, 'custom_name':None, 'x':-1, 'y':-1, 'hidden':False}

                    elif token_lower == 'begin_level': reading_level = True
                    elif token_lower == 'begin_mbmap': reading_mb = True
                    elif token_lower == 'begin_dbmap': reading_db = True

                    elif token_lower == 'begin_gate':
                        idx = -1
                        for i in range(1, 9):
                            if self.gates[i]['x'] == -1: idx = i; break
                        if idx != -1: current_gate = self.gates[idx]; self.visible_gate_slots = max(self.visible_gate_slots, idx)

                    elif token_lower == 'begin_item':
                         idx = -1
                         for i in range(1, 9):
                             if self.items[i]['x'] == -1: idx = i; break
                         if idx != -1: current_item = self.items[idx]; self.visible_item_slots = max(self.visible_item_slots, idx)

                    elif token_lower == 'begin_gem':
                        idx = -1
                        for i in range(1, 9):
                            if self.gems[i]['x'] == -1: idx = i; break
                        if idx != -1:
                            current_gem = self.gems[idx]
                            self.visible_gem_slots = max(self.visible_gem_slots, idx)
                            current_gem['actions'] = []
                            current_action_context = None

                    elif current_gem:
                        if token_lower == 'end':
                            if current_action_context:
                                current_action_context = None
                            else:
                                current_gem = None
                        elif token_lower == 'sec_x': current_gem['x'] = int(get_val(iterator))
                        elif token_lower == 'sec_y': current_gem['y'] = int(get_val(iterator))
                        elif token_lower == 'building': current_gem['blg'] = int(get_val(iterator))
                        elif token_lower == 'type': current_gem['type'] = int(get_val(iterator))
                        elif token_lower.startswith('modify_'):
                            act_type = token_lower
                            act_id = int(get_val(iterator))
                            current_action_context = (act_type, act_id)
                        elif token_lower in ['enable', 'add_energy', 'add_shield', 'num_weapons'] and current_action_context:
                            param = token_lower
                            val = get_val(iterator)
                            current_gem['actions'].append({'target_type': current_action_context[0],'id': current_action_context[1],'param': param,'val': val})

                    elif token_lower == 'end':
                        if current_squad:
                            if current_squad['x'] != -1: self.squads.append(current_squad)
                            current_squad = None
                        elif current_host:
                            if current_host['x'] != -1: self.host_stations.append(current_host)
                            current_host = None
                        elif current_gate: current_gate = None
                        elif current_item: current_item = None
                        if reading_level: reading_level = False
                        if reading_mb: reading_mb = False
                        if reading_db: reading_db = False

                    elif reading_level:
                        if token_lower == 'sky':
                            self.lvl_info['sky'] = get_val(iterator)
                        elif token_lower == 'title_default':
                            self.lvl_info['title'] = get_val(iterator)
                        elif token_lower == 'ambiencetrack':
                            raw_music = get_val(iterator)
                            if '_' in raw_music:
                                self.lvl_info['music'] = raw_music.split('_')[0]
                            else:
                                self.lvl_info['music'] = raw_music
                        elif token_lower == 'movie':
                             raw_mov = get_val(iterator)
                             self.lvl_info['movie'] = raw_mov.replace(':', '/')
                    elif reading_mb:
                        if token_lower == 'name':
                            self.lvl_info['mbmap'] = get_val(iterator)
                    elif reading_db:
                        if token_lower == 'name':
                            self.lvl_info['dbmap'] = get_val(iterator)

                    elif current_squad:
                        if token_lower == 'owner': current_squad['owner'] = int(get_val(iterator))
                        elif token_lower == 'vehicle': current_squad['veh'] = int(get_val(iterator))
                        elif token_lower == 'num': current_squad['num'] = int(get_val(iterator))
                        elif token_lower == 'mb_status':
                             val = get_val(iterator)
                             if val.lower() == 'unknown': current_squad['hidden'] = True
                        elif token_lower == 'pos_x':
                             val = int(get_val(iterator));
                             try: new_x, _ = self.world_to_grid(val, 0); current_squad['x'] = max(0, min(self.mw-1, new_x))
                             except: current_squad['x'] = 0
                        elif token_lower == 'pos_z':
                             val = int(get_val(iterator));
                             try: _, new_y = self.world_to_grid(0, val); current_squad['y'] = max(0, min(self.mh-1, new_y))
                             except: current_squad['y'] = 0

                    elif current_host:
                        if token_lower == 'owner': current_host['owner'] = int(get_val(iterator))
                        elif token_lower == 'vehicle': current_host['veh'] = int(get_val(iterator))
                        elif token_lower == 'energy': current_host['energy'] = int(get_val(iterator))
                        elif token_lower == 'pos_y': current_host['pos_y'] = int(get_val(iterator))
                        elif token_lower == 'mb_status':
                             val = get_val(iterator)
                             if val.lower() == 'unknown': current_host['hidden'] = True
                        elif token_lower == 'pos_x':
                             val = int(get_val(iterator));
                             try: new_x, _ = self.world_to_grid(val, 0); current_host['x'] = max(0, min(self.mw-1, new_x))
                             except: current_host['x'] = 0
                        elif token_lower == 'pos_z':
                             val = int(get_val(iterator));
                             try: _, new_y = self.world_to_grid(0, val); current_host['y'] = max(0, min(self.mh-1, new_y))
                             except: current_host['y'] = 0

                    elif current_gate:
                         if token_lower == 'sec_x': current_gate['x'] = int(get_val(iterator))
                         elif token_lower == 'sec_y': current_gate['y'] = int(get_val(iterator))
                         elif token_lower == 'target_level': current_gate['target'] = int(get_val(iterator))
                         elif token_lower == 'closed_bp': current_gate['closed_bp'] = int(get_val(iterator))
                         elif token_lower == 'opened_bp': current_gate['opened_bp'] = int(get_val(iterator))
                         elif token_lower == 'keysec_x':
                             kx = int(get_val(iterator))
                             key_token = next(iterator)
                             ky = int(get_val(iterator)) if key_token.lower() == 'keysec_y' else 0
                             current_gate['keys'].append((kx, ky))

                    elif current_item:
                         if token_lower == 'sec_x': current_item['x'] = int(get_val(iterator))
                         elif token_lower == 'sec_y': current_item['y'] = int(get_val(iterator))
                         elif token_lower == 'type': current_item['type'] = int(get_val(iterator))
                         elif token_lower == 'inactive_bp': current_item['inactive_bp'] = int(get_val(iterator))
                         elif token_lower == 'active_bp': current_item['active_bp'] = int(get_val(iterator))
                         elif token_lower == 'trigger_bp': current_item['trigger_bp'] = int(get_val(iterator))
                         elif token_lower == 'countdown': current_item['countdown'] = int(get_val(iterator))
                         elif token_lower == 'keysec_x':
                             kx = int(get_val(iterator))
                             key_token = next(iterator)
                             ky = int(get_val(iterator)) if key_token.lower() == 'keysec_y' else 0
                             current_item['keys'].append((kx, ky))

                    elif token_lower in ['typ_map', 'own_map', 'hgt_map', 'blg_map']:
                        key_map = token_lower; v1 = next(iterator)
                        if v1 == '=': v1 = next(iterator)
                        next(iterator)
                        data_tokens = []
                        target_count = w * h
                        for _ in range(target_count): data_tokens.append(next(iterator))
                        matrix = []
                        for r in range(h):
                            row_tokens = data_tokens[r*w : (r+1)*w]
                            if 'own' in key_map: row = [int(x) for x in row_tokens]
                            elif 'hgt' in key_map:
                                row = [];
                                for x in row_tokens:
                                    try: row.append(int(x, 16))
                                    except: row.append(0)
                            else: row = row_tokens
                            matrix.append(row)
                        grids_loaded[key_map] = matrix

                except StopIteration: break

            self.grids['type'] = grids_loaded.get('typ_map', [['00']*w for _ in range(h)])
            self.grids['own'] = grids_loaded.get('own_map', [[0]*w for _ in range(h)])
            self.grids['hgt'] = grids_loaded.get('hgt_map', [[DEFAULT_HGT]*w for _ in range(h)])
            self.grids['blg'] = grids_loaded.get('blg_map', [['00']*w for _ in range(h)])
            self.set_mode("TYPE"); self.refresh_squad_list(); self.refresh_host_list()
            self.current_filename = os.path.basename(filename)
            self.update_window_title()
            messagebox.showinfo("Success", f"Map Loaded: {w}x{h}")

        except Exception as e: messagebox.showerror("Error", f"Failed to load: {str(e)}")

    def save_map(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension=".ldf", initialfile="l0101.ldf")
        if not f: return

        self.current_filename = os.path.basename(f.name)
        self.update_window_title()

        def w(txt): f.write(txt + "\n")
        w("; --- Generated by Sektor v14.1 (DRONES + HOST) ---")
        w(";------------------------------------------------------------")
        w("begin_level")
        w(f"   set = {self.set_folder.replace('set','')}")
        w(f"   sky = {self.lvl_info['sky']}")
        w(f"   title_default = {self.lvl_info['title']}")
        w("   slot0 = palette/standard.pal")
        
        if self.lvl_info.get('music') and self.lvl_info['music'] != "None":
            w(f"   ambiencetrack = {self.lvl_info['music']}")
        
        if self.lvl_info.get('movie') and self.lvl_info['movie'] != "None":
            w(f"   movie = {self.lvl_info['movie']}")

        w("end")
        w(";------------------------------------------------------------")
        w("begin_mbmap"); w(f"   name          =  {self.lvl_info.get('mbmap', 'MB_53.IFF')}"); w("end")
        w("begin_dbmap"); w(f"   name          =  {self.lvl_info.get('dbmap', 'DB_53.IFF')}"); w("end")
        w(";------------------------------------------------------------")
        for i in range(1, self.visible_gate_slots + 1):
            g = self.gates[i]
            if g['x'] != -1:
                w("begin_gate"); w(f"   sec_x = {g['x']}\n   sec_y = {g['y']}"); w(f"   target_level = {g['target']}")
                w(f"   closed_bp = {g['closed_bp']}"); w(f"   opened_bp = {g['opened_bp']}"); w("   mb_status = unknown")
                for kx, ky in g['keys']: w(f"   keysec_x = {kx}\n   keysec_y = {ky}")
                w("end"); w(";------------------------------------------------------------")
        for i in range(1, self.visible_item_slots + 1):
            it = self.items[i]
            if it['x'] != -1:
                w("begin_item"); w(f"   sec_x = {it['x']}\n   sec_y = {it['y']}"); w(f"   inactive_bp = {it['inactive_bp']}"); w(f"   active_bp = {it['active_bp']}")
                w(f"   trigger_bp = {it['trigger_bp']}"); w(f"   type = {it['type']}"); w(f"   countdown = {it['countdown']}")
                for kx, ky in it['keys']: w(f"   keysec_x = {kx}\n   keysec_y = {ky}")
                w("end"); w(";------------------------------------------------------------")
        for i in range(1, self.visible_gem_slots + 1):
            gm = self.gems[i]
            if gm['x'] != -1:
                w("begin_gem"); w(f"   sec_x = {gm['x']}\n   sec_y = {gm['y']}"); w(f"   building = {gm['blg']}"); w(f"   type = {gm['type']}")
                grouped = {}
                for a in gm['actions']:
                    full_type = a['target_type']; key = (full_type, a['id']);
                    if key not in grouped: grouped[key] = []
                    grouped[key].append(f"      {a['param']} = {a['val']}")
                if grouped:
                    w("   begin_action")
                    for (t_type, t_id), lines in grouped.items(): w(f"      {t_type} {t_id}"); [w(l) for l in lines]; w("      end")
                    w("   end_action")
                w("end"); w(";------------------------------------------------------------")

        for h in self.host_stations:
             w("begin_robo")
             w(f"   owner = {h['owner']}")
             if h['custom_name']: w(f"   vehicle = {h['veh']} ; {h['custom_name']}")
             else: w(f"   vehicle = {h['veh']} ; {self.defs['host'].get(h['veh'],'')}")

             final_x, final_z = self.grid_to_world(h['x'], h['y'])
             w(f"   pos_x = {final_x}")
             w(f"   pos_y = {h['pos_y']}")
             w(f"   pos_z = {final_z}")
             w(f"   energy = {h['energy']}")
             
             if h.get('hidden', False): w("   mb_status = unknown")

             w("   reload_const = 576666")
             w("   viewangle = 12")
             w("   con_budget = 97")
             w("   con_delay = 30000")
             w("   def_budget = 97")
             w("   def_delay = 32000")
             w("   rec_budget = 93")
             w("   rec_delay = 23000")
             w("   rob_budget = 93")
             w("   rob_delay = 34000")
             w("   pow_budget = 60")
             w("   pow_delay = 0")
             w("   rad_budget = 0")
             w("   rad_delay = 0")
             w("   saf_budget = 60")
             w("   saf_delay = 33000")
             w("   cpl_budget = 95")
             w("   cpl_delay = 0")
             w("end"); w(";------------------------------------------------------------")

        for s in self.squads:
            w("begin_squad"); w(f"   owner = {s['owner']}")
            if s['custom_name']: w(f"   vehicle = {s['veh']} ; {s['custom_name']}")
            else: w(f"   vehicle = {s['veh']} ; {self.defs['veh'].get(s['veh'],'')}")
            w(f"   num = {s['num']}");
            if s['hidden']: w("   mb_status = unknown")
            final_x, final_z = self.grid_to_world(s['x'], s['y'])
            w(f"   pos_x = {final_x}"); w(f"   pos_z = {final_z}"); w("end")
        w(";------------------------------------------------------------")
        
        # MOD: Tech Range increased to 7 (Drones)
        for i in range(1, 8):
            d = self.tech[i]
            if d['veh'] or d['blg']:
                w(f"begin_enable {i}")
                for v in d['veh']: name = self.custom_tech_names.get(v, self.defs['veh'].get(v, '')); w(f"   vehicle = {v:<4} ; {name}")
                for b in d['blg']: name = self.custom_tech_names.get(b, self.defs['blg'].get(b, '')); w(f"   building = {b:<4} ; {name}")
                w("end")
        w(";------------------------------------------------------------")
        if self.script_content.strip(): w("; --- USER SCRIPT ---"); w(self.script_content); w(";------------------------------------------------------------")
        w("begin_maps")

        map_types = [('typ_map', self.grids['type']),
                     ('own_map', self.grids['own']),
                     ('hgt_map', self.grids['hgt']),
                     ('blg_map', self.grids['blg'])]

        for k, g in map_types:
            w(f"   {k} =")
            w(f"      {self.mw} {self.mh}")
            for r in g:
                if 'own' in k:
                    fmt = lambda x: f"{x:02d}"
                elif 'hgt' in k:
                    fmt = lambda x: f"{x:02x}"
                else:
                    fmt = lambda x: str(x)

                row_str = " ".join([fmt(x) for x in r])
                w(f"      {row_str}")

        w("end"); f.close(); messagebox.showinfo("Saved", f"Map saved to:\n{f.name}")

if __name__ == "__main__":
    root = tk.Tk()
    try: root.state('zoomed')
    except: pass
    SektorEditor(root)
    root.mainloop()

