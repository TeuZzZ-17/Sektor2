import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import copy
import re
import platform
import subprocess

from sektor_constants import *

class UIMixin:

    GEM_MODEL_LABELS = {
        4: "04 - gem0",
        7: "07 - gem_with_flak1",
        9: "09 - gem_with_flak2",
        15: "15 - gem_weapon_power",
        16: "16 - gem_new_building",
        50: "50 - gem_more_shield",
        51: "51 - gem_heavy_weapon",
        58: "58 - fuck_gem_sectors",
        60: "60 - gem_more_roboflak",
        61: "61 - gem_power_roboflak",
        65: "65 - gem_more_shield",
    }
    GEM_MODEL_VALUES = [
        "04 - gem0",
        "07 - gem_with_flak1",
        "09 - gem_with_flak2",
        "15 - gem_weapon_power",
        "16 - gem_new_building",
        "50 - gem_more_shield",
        "51 - gem_heavy_weapon",
        "58 - fuck_gem_sectors",
        "60 - gem_more_roboflak",
        "61 - gem_power_roboflak",
        "65 - gem_more_shield",
    ]

    FACTION_DISPLAY_NAMES = {
        0: "Neutral",
        1: "Resistance",
        2: "Sulgogar",
        3: "Mykon",
        4: "Taerkasten",
        5: "Black Sect",
        6: "Ghorkov",
        7: "Drones",
    }

    HOST_PLAYER_OWNER_VALUES = [
        "01 - Resistance",
        "02 - Sulgogar",
        "03 - Mykon",
        "04 - Taerkasten",
        "05 - Black Sect",
        "06 - Ghorkov",
        "07 - Drones",
    ]
    HOST_ENERGY_PRESETS = [
        ("Very Low", 100000),
        ("Low", 300000),
        ("Medium", 500000),
        ("High", 700000),
        ("Very High", 1000000),
    ]
    HOST_ENERGY_PRESET_VALUES = [label for label, value in HOST_ENERGY_PRESETS]

    def get_faction_display_name(self, owner):
        if owner in self.FACTION_DISPLAY_NAMES:
            return self.FACTION_DISPLAY_NAMES[owner]
        return FACTIONS.get(owner, ("Unknown", None))[0].title()

    def format_player_owner_value(self, owner):
        return f"{owner:02d} - {self.get_faction_display_name(owner)}"

    def parse_player_owner_value(self, value):
        owner = self.parse_leading_int(value)
        if owner is None:
            return 1
        return max(1, min(7, owner))

    def host_energy_preset_for_value(self, energy):
        for label, value in self.HOST_ENERGY_PRESETS:
            if energy == value:
                return label
        return ""

    def parse_host_energy_preset_value(self, preset):
        for label, value in self.HOST_ENERGY_PRESETS:
            if preset == label:
                return value
        return None

    def host_energy_band_label(self, energy):
        if 1 <= energy <= 100000:
            return "Very Low"
        if energy <= 400000:
            return "Low"
        if energy <= 600000:
            return "Medium"
        if energy <= 800000:
            return "High"
        if energy <= 1000000:
            return "Very High"
        return "Custom/Extreme"

    def update_host_energy_controls(self, energy=None):
        if energy is None:
            try:
                energy = int(self.e_host_en.get())
            except:
                energy = None
        preset = "" if energy is None else self.host_energy_preset_for_value(energy)
        if hasattr(self, "cb_host_energy_preset") and self.cb_host_energy_preset.winfo_exists():
            self.cb_host_energy_preset.set(preset)

    def format_gem_model_value(self, model_id):
        return self.GEM_MODEL_LABELS.get(model_id, str(model_id))

    def parse_gem_model_value(self, value):
        match = re.match(r'^\s*(\d+)', str(value))
        if not match:
            return None
        return int(match.group(1))

    def format_item_type_value(self, type_id):
        if type_id == 1:
            return "Default"
        return str(type_id)

    def parse_item_type_value(self, value):
        value = str(value).strip()
        if value.lower() == "default":
            return 1
        return self.parse_leading_int(value)

    def parse_leading_int(self, value):
        match = re.match(r'^\s*(\d+)', str(value))
        if not match:
            return None
        return int(match.group(1))

    def definition_combo_values(self, kind):
        return [
            f"{item_id} - {name}"
            for item_id, name in sorted(self.defs.get(kind, {}).items())
        ]

    def format_definition_value(self, kind, item_id):
        name = self.defs.get(kind, {}).get(item_id)
        if name:
            return f"{item_id} - {name}"
        return str(item_id)

    def build_gui(self):
        # MOD: Removed PanedWindow to prevent Sash/Button glitch. Using Frames.
        self.f_main = tk.Frame(self.root, bg="#222")
        self.f_main.pack(fill=tk.BOTH, expand=True)

        self.f_left = tk.Frame(self.f_main, bg="#1a1a1a", width=self.left_panel_width)
        self.f_left.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.f_left.pack_propagate(False) # Force width

        self.left_resize_handle = tk.Frame(
            self.f_main,
            width=self.left_resize_handle_width,
            bg="#0b1f1f",
            cursor="sb_h_double_arrow"
        )
        self.left_resize_handle.pack(side=tk.LEFT, fill=tk.Y)
        self.left_resize_grip = tk.Frame(self.left_resize_handle, bg="#19caca", width=2)
        self.left_resize_grip.pack(fill=tk.Y, expand=True, padx=4, pady=2)
        self.left_resize_handle.bind("<Enter>", lambda e: self.left_resize_handle.config(bg="#103333"))
        self.left_resize_handle.bind("<Leave>", lambda e: self.left_resize_handle.config(bg="#0b1f1f"))
        self.left_resize_handle.bind("<ButtonPress-1>", self.start_left_panel_resize)
        self.left_resize_handle.bind("<B1-Motion>", self.do_left_panel_resize)
        self.left_resize_handle.bind("<ButtonRelease-1>", self.stop_left_panel_resize)
        self.left_resize_grip.bind("<ButtonPress-1>", self.start_left_panel_resize)
        self.left_resize_grip.bind("<B1-Motion>", self.do_left_panel_resize)
        self.left_resize_grip.bind("<ButtonRelease-1>", self.stop_left_panel_resize)

        self.f_right = tk.Frame(self.f_main, bg="#000")
        self.f_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- LEFT PANEL ---
        tb_pal = tk.Frame(self.f_left, bg="#2a2a2a", height=36); tb_pal.pack(fill=tk.X)
        self.lbl_sel = tk.Label(tb_pal, text="SEL: 00", bg="#2a2a2a", fg="#00FFFF", font=("Courier", 11, "bold"), width=10, anchor="w")
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

        self.cnt_frame = tk.Frame(self.f_left, bg="#1a1a1a")
        self.cnt_frame.pack(fill=tk.BOTH, expand=True)
        self.cv_pal = tk.Canvas(self.cnt_frame, bg="#1a1a1a", highlightthickness=0)

        self.sb_pal = tk.Scrollbar(
            self.cnt_frame,
            command=self.cv_pal.yview,
            bg="#00B8B8",
            activebackground="#3DF0F0",
            troughcolor="#0f1f1f",
            width=18,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            elementborderwidth=1,
            activerelief=tk.FLAT,
            takefocus=0
        )
        self.cv_pal.config(yscrollcommand=self.sb_pal.set)
        self.cv_pal.bind("<Configure>", self.draw_palette)
        self.bind_palette_scroll_and_zoom()

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
        tb_top = tk.Frame(self.f_right, bg="#2a2a2a")
        tb_top.pack(fill=tk.X)
        tb_modes = tk.Frame(tb_top, bg="#2a2a2a", height=28)
        tb_modes.pack(fill=tk.X)
        tb_actions = tk.Frame(tb_top, bg="#242424", height=30)
        tb_actions.pack(fill=tk.X)

        tk.Label(tb_modes, text="MODE:", bg="#2a2a2a", fg="#aaa", font=("Arial", 8, "bold")).pack(side=tk.LEFT, padx=(5,3))
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
            b = tk.Button(
                tb_modes,
                text=txt,
                bg="#444",
                fg="white",
                command=lambda x=m: self.set_mode(x),
                font=("Arial", 8),
                padx=3,
                pady=1
            )
            b.pack(side=tk.LEFT, padx=1, pady=2)
            self.btns[m] = (b, col)

        self.btn_undo = tk.Button(tb_actions, text="< UNDO", command=self.undo, bg="#333", fg="white", activebackground="#FFFFFF", activeforeground="black", font=("Arial",8), padx=4, pady=1)
        self.btn_undo.pack(side=tk.LEFT, padx=1, pady=2)
        self.btn_redo = tk.Button(tb_actions, text="REDO >", command=self.redo, bg="#333", fg="white", activebackground="#FFFFFF", activeforeground="black", font=("Arial",8), padx=4, pady=1)
        self.btn_redo.pack(side=tk.LEFT, padx=1, pady=2)

        actions = [("RESET", lambda: self.reset_map(True), "#800000"),
            ("RESIZE", self.resize_map_dialog, "#663300"),
            ("FILL", self.fill_map, "#333")]
        for t, cmd, bg in actions:
            tk.Button(tb_actions, text=t, command=cmd, bg=bg, fg="white", font=("Arial",8), padx=4, pady=1).pack(side=tk.LEFT, padx=1, pady=2)

        self.btn_cl = tk.Button(tb_actions, text="CLEAR VIEW", command=self.toggle_clear, bg="#444", fg="white", font=("Arial",8), padx=4, pady=1)
        self.btn_cl.pack(side=tk.LEFT, padx=(4,2), pady=2)

        io_btns = [("CHANGE LEVEL INFO", self.edit_info, "#4B0082"), ("LOAD MAP", self.load_map, "#CC0000"), ("SAVE MAP", self.save_map, "#006600")]
        for t, cmd, bg in io_btns:
            tk.Button(tb_actions, text=t, command=cmd, bg=bg, fg="white", font=("Arial",8,"bold"), padx=4, pady=1).pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_new_map = tk.Button(
            tb_actions,
            text="NEW MAP",
            command=self.new_map_dialog,
            bg="#2FA8FF",
            fg="white",
            activebackground="#FFFFFF",
            activeforeground="black",
            font=("Arial",8,"bold"),
            padx=4,
            pady=1
        )
        self.btn_new_map.pack(side=tk.LEFT, padx=2, pady=2)

        # MAP CONTAINER (Panning without visible map scrollbars)
        f_map_container = tk.Frame(self.f_right, bg="#000")
        f_map_container.pack(fill=tk.BOTH, expand=True)

        self.cv_map = tk.Canvas(f_map_container, bg="#000", highlightthickness=0)
        self.cv_map.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.cv_map.bind("<Configure>", self.on_map_canvas_configure)

        self.bind_scroll(self.cv_map)
        self.cv_map.bind("<Button-1>", self.on_map_left_press)
        self.cv_map.bind("<B1-Motion>", self.on_map_left_drag)
        self.cv_map.bind("<ButtonRelease-1>", self.on_map_left_release)
        self.cv_map.bind("<Leave>", self.clear_hover_overlay)
        self.cv_map.bind("<Button-3>", self.on_right_click); self.cv_map.bind("<B3-Motion>", self.on_right_click)
        self.cv_map.bind("<ButtonRelease-3>", self.on_map_right_release)
        self.cv_map.bind("<ButtonPress-2>", self.start_map_pan_middle)
        self.cv_map.bind("<B2-Motion>", self.drag_map_pan)
        self.cv_map.bind("<ButtonRelease-2>", self.stop_map_pan)
        self.cv_map.bind("<Control-Button-2>", self.pick)
        self.root.bind_all("<KeyPress-space>", self.on_space_pan_press)
        self.root.bind_all("<KeyRelease-space>", self.on_space_pan_release)
        self.root.bind_all("<Control-z>", self.undo)
        self.root.bind_all("<Control-y>", self.redo)
        self.root.bind_all("<Control-Shift-Z>", self.redo)
        self.update_history_buttons()

    def update_window_title(self):
        title = f"{APP_NAME} - Env: {self.set_folder.upper()}"
        if getattr(self, 'current_filepath', None):
            title += f" - [{self.current_filepath}]"
        elif self.current_filename:
            title += f" - [{self.current_filename}]"
        self.root.title(title)

    def set_mode(self, m):
        old_mode = getattr(self, 'mode', None)
        if (
            old_mode == "SCRIPT" and
            m != "SCRIPT" and
            not getattr(self, '_restoring_snapshot', False) and
            not getattr(self, '_suppress_script_sync', False)
        ):
            self.sync_script_widget_to_data(push_undo=True)

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
            if m == "TYPE": self.lbl_custom_title.config(text="Sector Hex:")
            else: self.lbl_custom_title.config(text="Building Hex:")
            
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
            self.refresh_palette_layout(force_full=True)

        self.upd_lbl()
        self.draw_grid()

    def sync_script_widget_to_data(self, push_undo=False):
        txt = getattr(self, 'script_text_widget', None)
        if not txt:
            return False
        try:
            if not txt.winfo_exists():
                return False
            new_script = txt.get("1.0", "end-1c")
        except tk.TclError:
            return False

        if new_script == self.script_content:
            return False
        if push_undo:
            self.push_undo_snapshot()
        self.script_content = new_script
        self.dirty = True
        return True

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

    def start_left_panel_resize(self, event):
        self._left_resizing = True
        self._left_resize_start_x = event.x_root
        self._left_resize_start_width = self.f_left.winfo_width()
        self.left_resize_handle.config(bg="#145050")

    def do_left_panel_resize(self, event):
        if not self._left_resizing:
            return

        dx = event.x_root - self._left_resize_start_x
        max_dynamic = self.f_main.winfo_width() - self.left_resize_handle_width - self.min_map_area_width
        max_allowed = min(self.left_panel_max_width, max_dynamic)
        if max_allowed < self.left_panel_min_width:
            max_allowed = self.left_panel_min_width
        new_width = max(self.left_panel_min_width, min(max_allowed, self._left_resize_start_width + dx))

        if new_width != self.left_panel_width:
            self.left_panel_width = new_width
            self.f_left.config(width=new_width)
            self.schedule_palette_resize_refresh()

    def stop_left_panel_resize(self, event):
        self._left_resizing = False
        self.left_resize_handle.config(bg="#103333")
        self.refresh_palette_layout(force_full=True)
        self.refresh_map_layout(force_full=True)

    def schedule_palette_resize_refresh(self):
        if self._palette_resize_refresh_pending:
            return
        self._palette_resize_refresh_pending = True
        self.root.after_idle(self.refresh_palette_layout)

    def refresh_palette_layout(self, force_full=False):
        self._palette_resize_refresh_pending = False
        if not hasattr(self, "cv_pal"):
            return

        y_fraction = 0.0
        try:
            y_fraction = self.cv_pal.yview()[0]
        except:
            pass

        if force_full:
            self.root.update_idletasks()

        container_w = self.cnt_frame.winfo_width()
        sb_w = self.sb_pal.winfo_width() if self.sb_pal.winfo_ismapped() else 0
        target_w = max(120, container_w - sb_w - 2)
        self.cv_pal.config(width=target_w)

        self.draw_palette()
        try:
            self.cv_pal.yview_moveto(max(0.0, min(1.0, y_fraction)))
        except:
            pass

    def on_map_canvas_configure(self, event=None):
        self.schedule_map_layout_refresh()

    def schedule_map_layout_refresh(self):
        if self._map_layout_refresh_pending:
            return
        self._map_layout_refresh_pending = True
        self.root.after_idle(self.refresh_map_layout)

    def refresh_map_layout(self, force_full=False):
        self._map_layout_refresh_pending = False
        if not hasattr(self, "cv_map"):
            return

        x_frac = 0.0
        y_frac = 0.0
        try:
            x_frac = self.cv_map.xview()[0]
            y_frac = self.cv_map.yview()[0]
        except:
            pass

        if force_full:
            self.root.update_idletasks()

        self.draw_grid()

        total_w = max(1, self.mw * self.zoom_m)
        total_h = max(1, self.mh * self.zoom_m)
        view_w = max(1, self.cv_map.winfo_width())
        view_h = max(1, self.cv_map.winfo_height())

        if total_w <= view_w:
            self.cv_map.xview_moveto(0.0)
        else:
            self.cv_map.xview_moveto(max(0.0, min(1.0, x_frac)))

        if total_h <= view_h:
            self.cv_map.yview_moveto(0.0)
        else:
            self.cv_map.yview_moveto(max(0.0, min(1.0, y_frac)))

    def build_height_input_panel(self):
        p = self.panels['HGT_INPUT']
        for w in p.winfo_children(): w.destroy()
        tk.Label(p, text="HEIGHT EDITOR (0 - 60)", bg="#660066", fg="white", font=("Arial",12,"bold")).pack(fill=tk.X, pady=(10,20))

        f = tk.Frame(p, bg="#1a1a1a"); f.pack(pady=10)

        current_user_val = self.sel['hgt'] - HGT_MIN

        def adj_hgt(d):
            new_val = max(HGT_MIN, min(HGT_MAX, self.sel['hgt'] + d))
            self.sel['hgt'] = new_val
            self.update_height_ui_after_value_change()

        tk.Button(f, text="<", command=lambda: adj_hgt(-1), bg="#333", fg="white", font=("bold", 14), width=3).pack(side=tk.LEFT, padx=10)

        self.hgt_entry = tk.Entry(f, width=5, font=("Courier", 24, "bold"), justify='center', bg="#222", fg="#00FFFF", insertbackground="white")
        self.hgt_entry.pack(side=tk.LEFT, padx=10, ipady=4)
        self.hgt_entry.insert(0, str(current_user_val))

        def manual_entry(e):
             self.process_height_input(e)
             self.update_height_ui_after_value_change(update_entry=False)

        self.hgt_entry.bind("<KeyRelease>", manual_entry)

        tk.Button(f, text=">", command=lambda: adj_hgt(1), bg="#333", fg="white", font=("bold", 14), width=3).pack(side=tk.LEFT, padx=10)

        self.lbl_hgt_hex = tk.Label(p, text=f"real hex output: {self.sel['hgt']:02X}", bg="#1a1a1a", fg="#888", font=("Courier", 10, "bold"))
        self.lbl_hgt_hex.pack(pady=(0, 10))

        self.height_slider_canvas = tk.Canvas(p, width=HEIGHT_SLIDER_W, height=HEIGHT_SLIDER_H, bg=HEIGHT_PANEL_BG, highlightthickness=0)
        self.height_slider_canvas.pack(pady=(0, 20))
        self.height_slider_canvas.bind("<Button-1>", self.on_height_slider_drag)
        self.height_slider_canvas.bind("<B1-Motion>", self.on_height_slider_drag)
        self.draw_height_slider()

        self.build_height_legend(p)

    def get_selected_editor_height(self):
        try:
            return max(EDITOR_HEIGHT_MIN, min(EDITOR_HEIGHT_MAX, int(self.sel['hgt']) - HGT_MIN))
        except:
            return EDITOR_HEIGHT_BASE

    def draw_height_slider(self):
        if not hasattr(self, "height_slider_canvas") or not self.height_slider_canvas.winfo_exists():
            return

        cv = self.height_slider_canvas
        cv.delete("all")

        w, h = HEIGHT_SLIDER_W, HEIGHT_SLIDER_H
        top_y, bottom_y = HEIGHT_SLIDER_TOP_Y, HEIGHT_SLIDER_BOTTOM_Y
        center_y = (top_y + bottom_y) // 2
        track_w = HEIGHT_SLIDER_TRACK_W
        x0 = (w - track_w) // 2
        x1 = x0 + track_w
        selected_height = self.get_selected_editor_height()
        delta = selected_height - EDITOR_HEIGHT_BASE

        high_color = HEIGHT_HIGH_COLOR
        low_color = HEIGHT_LOW_COLOR
        base_color = HEIGHT_BASE_COLOR
        bg_color = "#0D1114"
        track_color = "#242B30"

        cv.create_rectangle(x0 - 12, top_y, x1 + 12, bottom_y, fill=bg_color, outline="#4A565D", width=1)
        cv.create_rectangle(x0, top_y + 8, x1, bottom_y - 8, fill=track_color, outline="#111", width=1)

        half_h = max(1, ((bottom_y - top_y) // 2) - 8)
        fill_len = int((abs(delta) / EDITOR_HEIGHT_BASE) * half_h)
        if delta != 0:
            fill_len = max(1, fill_len)

        if delta > 0:
            cv.create_rectangle(x0 + 2, center_y - fill_len, x1 - 2, center_y, fill=high_color, outline="")
        elif delta < 0:
            cv.create_rectangle(x0 + 2, center_y, x1 - 2, center_y + fill_len, fill=low_color, outline="")

        tick_45 = self.height_slider_y_from_value(45)
        tick_15 = self.height_slider_y_from_value(15)
        cv.create_line(x0 - 8, tick_45, x1 + 8, tick_45, fill="#627078", width=1)
        cv.create_line(x0 - 8, tick_15, x1 + 8, tick_15, fill="#627078", width=1)

        marker_y = self.height_slider_y_from_value(selected_height)
        cv.create_line(x0 - 18, center_y, x1 + 18, center_y, fill=base_color, width=3)
        cv.create_rectangle(x0 - 10, marker_y - 5, x1 + 10, marker_y + 5, fill="#F7F7F7", outline="#000", width=1)

        label_x = x1 + 34
        cv.create_text(label_x, top_y, text="60", fill=high_color, font=("Arial", 10, "bold"))
        cv.create_text(label_x, center_y, text="30", fill=base_color, font=("Arial", 10, "bold"))
        cv.create_text(label_x, bottom_y, text="0", fill=low_color, font=("Arial", 10, "bold"))

    def build_height_legend(self, parent):
        legend = tk.Frame(parent, bg=HEIGHT_PANEL_BG)
        legend.pack(pady=(0, 12))

        rows = [
            (HEIGHT_HIGH_COLOR, "HIGHER"),
            (HEIGHT_BASE_COLOR, "BASE 30"),
            (HEIGHT_LOW_COLOR, "LOWER"),
        ]
        for color, text in rows:
            row = tk.Frame(legend, bg=HEIGHT_PANEL_BG)
            row.pack(anchor=tk.W, pady=1)
            swatch = tk.Canvas(row, width=24, height=10, bg=HEIGHT_PANEL_BG, highlightthickness=0)
            swatch.pack(side=tk.LEFT, padx=(0, 6))
            y = 5
            swatch.create_line(2, y, 22, y, fill=color, width=4)
            tk.Label(row, text=text, bg="#1a1a1a", fg="#BBBBBB", font=("Arial", 8, "bold")).pack(side=tk.LEFT)

    def get_height_slider_track_bounds(self):
        w = HEIGHT_SLIDER_W
        top_y, bottom_y = HEIGHT_SLIDER_TOP_Y, HEIGHT_SLIDER_BOTTOM_Y
        track_w = HEIGHT_SLIDER_TRACK_W
        x0 = (w - track_w) // 2
        x1 = x0 + track_w
        return x0 - 12, top_y, x1 + 12, bottom_y

    def height_slider_y_from_value(self, value):
        top_y, bottom_y = HEIGHT_SLIDER_TOP_Y, HEIGHT_SLIDER_BOTTOM_Y
        value = max(EDITOR_HEIGHT_MIN, min(EDITOR_HEIGHT_MAX, int(value)))
        ratio = value / EDITOR_HEIGHT_MAX
        return int(bottom_y - (ratio * (bottom_y - top_y)))

    def height_from_slider_y(self, y):
        top_y, bottom_y = HEIGHT_SLIDER_TOP_Y, HEIGHT_SLIDER_BOTTOM_Y
        y = max(top_y, min(bottom_y, int(y)))
        ratio = (bottom_y - y) / (bottom_y - top_y)
        return max(EDITOR_HEIGHT_MIN, min(EDITOR_HEIGHT_MAX, round(ratio * EDITOR_HEIGHT_MAX)))

    def on_height_slider_drag(self, event):
        track_x0, track_y0, track_x1, track_y1 = self.get_height_slider_track_bounds()
        if event.x < track_x0 or event.x > track_x1 or event.y < track_y0 or event.y > track_y1:
            return

        new_value = self.height_from_slider_y(event.y)
        new_hgt = new_value + HGT_MIN
        if new_hgt != self.sel['hgt']:
            self.sel['hgt'] = new_hgt
            self.update_height_ui_after_value_change()

    def update_height_ui_after_value_change(self, update_entry=True):
        user_val = self.get_selected_editor_height()
        if update_entry and hasattr(self, 'hgt_entry') and self.hgt_entry.winfo_exists():
            self.hgt_entry.delete(0, tk.END)
            self.hgt_entry.insert(0, str(user_val))
        if hasattr(self, 'lbl_hgt_hex') and self.lbl_hgt_hex.winfo_exists():
            self.lbl_hgt_hex.config(text=f"real hex output: {self.sel['hgt']:02X}")
        self.draw_height_slider()

    def process_height_input(self, event=None):
        val_str = self.hgt_entry.get().strip()
        if not val_str.isdigit(): return
        try:
            val = int(val_str)
            val = max(EDITOR_HEIGHT_MIN, min(EDITOR_HEIGHT_MAX, val))
            self.sel['hgt'] = val + HGT_MIN
        except ValueError: pass

    def build_gate_ui(self):
        panel = self.panels['GATE']
        for w in panel.winfo_children(): w.destroy()
        p = tk.Frame(panel, bg="#1a1a1a")
        p.pack(anchor=tk.NW, padx=5, pady=0)

        f_slots = tk.Frame(p, bg="#1a1a1a"); f_slots.pack(fill=tk.X, pady=5)

        for i in range(1, self.visible_gate_slots + 1):
            bg = "#00FFFF" if i == self.current_gate_slot else "#333"
            fg = "black" if i == self.current_gate_slot else "white"
            tk.Button(f_slots, text=str(i), bg=bg, fg=fg, width=2, command=lambda x=i: self.select_gate_slot(x)).pack(side=tk.LEFT, padx=1)

        if self.visible_gate_slots < MAX_SPECIAL_SLOTS:
            def add_slot():
                self.push_undo_snapshot()
                self.visible_gate_slots += 1; self.build_gate_ui()
            tk.Button(f_slots, text="+", bg="#008888", fg="white", width=2, command=add_slot).pack(side=tk.LEFT, padx=5)

        if self.visible_gate_slots > 1:
            def rem_slot():
                self.push_undo_snapshot()
                idx = self.visible_gate_slots
                old_cell = self.get_special_cell(self.gates[idx])
                self.clear_special_auto_visual("GATE", self.gates[idx])
                self.gates[idx] = {'active': False, 'x': -1, 'y': -1, 'keys': [], 'target': 0, 'closed_bp': 25, 'opened_bp': 26, 'hidden': False}
                self.visible_gate_slots -= 1
                if self.current_gate_slot > self.visible_gate_slots: self.current_gate_slot = self.visible_gate_slots
                self.build_gate_ui(); self.redraw_cells(old_cell)
            tk.Button(f_slots, text="-", bg="#880000", fg="white", width=2, command=rem_slot).pack(side=tk.LEFT, padx=2)

        g_data = self.gates[self.current_gate_slot]

        # --- PRESET DROPDOWN (GATE) ---
        f_pre = tk.Frame(p, bg="#1a1a1a"); f_pre.pack(fill=tk.X, pady=(10,2))
        tk.Label(f_pre, text="Road Preset:", bg="#1a1a1a", fg="#aaa").pack(side=tk.LEFT, padx=5)
        
        gate_preset_values = ["With Roads (5/6)", "No Road (25/26)"]
        cb_gate_preset = ttk.Combobox(f_pre, values=gate_preset_values, state="readonly", width=22)
        cb_gate_preset.pack(side=tk.LEFT, padx=5)
        
        if g_data['closed_bp'] == 5 and g_data['opened_bp'] == 6:
            cb_gate_preset.set("With Roads (5/6)")
        elif g_data['closed_bp'] == 25 and g_data['opened_bp'] == 26:
             cb_gate_preset.set("No Road (25/26)")
        else:
             cb_gate_preset.set("") 

        def on_gate_preset_select(event):
            val = cb_gate_preset.get()
            old_closed = g_data['closed_bp']
            old_opened = g_data['opened_bp']
            old_cell = self.get_special_cell(g_data)
            old_visual = self.get_special_auto_visual("GATE", g_data)
            if "With Roads" in val:
                new_closed, new_opened = 5, 6
            elif "No Road" in val:
                new_closed, new_opened = 25, 26
            else:
                return
            if new_closed != old_closed or new_opened != old_opened:
                self.push_undo_snapshot()
                g_data['closed_bp'] = new_closed
                g_data['opened_bp'] = new_opened
                self.sync_special_auto_visual("GATE", g_data, old_cell=old_cell, old_visual=old_visual)
            self.build_gate_ui() 
            self.draw_grid()

        cb_gate_preset.bind("<<ComboboxSelected>>", on_gate_preset_select)
        
        tk.Label(p, text="(Custom values allowed)", fg="#777", bg="#1a1a1a", font=("Arial", 7)).pack(anchor=tk.W, pady=(0,5))

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
                new_target = int(e_tgt.get())
                new_closed = int(e_cls.get())
                new_opened = int(e_opn.get())
                if new_target != g_data['target'] or new_closed != g_data['closed_bp'] or new_opened != g_data['opened_bp']:
                    old_cell = self.get_special_cell(g_data)
                    old_visual = self.get_special_auto_visual("GATE", g_data)
                    visual_changed = new_closed != g_data['closed_bp'] or new_opened != g_data['opened_bp']
                    self.push_undo_snapshot()
                    g_data['target'] = new_target
                    g_data['closed_bp'] = new_closed
                    g_data['opened_bp'] = new_opened
                    if visual_changed:
                        self.sync_special_auto_visual("GATE", g_data, old_cell=old_cell, old_visual=old_visual)
                
                if g_data['closed_bp'] == 5 and g_data['opened_bp'] == 6: cb_gate_preset.set("With Roads (5/6)")
                elif g_data['closed_bp'] == 25 and g_data['opened_bp'] == 26: cb_gate_preset.set("No Road (25/26)")
                else: cb_gate_preset.set("")
                self.upd_lbl()
                self.draw_grid()
            except: pass
        e_tgt.bind("<KeyRelease>", upd_g); e_cls.bind("<KeyRelease>", upd_g); e_opn.bind("<KeyRelease>", upd_g)

        f_opt = tk.Frame(p, bg="#1a1a1a"); f_opt.pack(fill=tk.X, pady=(4, 2))
        self.var_gate_hid = tk.BooleanVar(value=g_data.get('hidden', False))
        def tog_gate_hid():
            val = self.var_gate_hid.get()
            if g_data.get('hidden', False) != val:
                self.push_undo_snapshot()
                g_data['hidden'] = val
                self.dirty = True
        tk.Checkbutton(f_opt, text="Hide in Briefing", variable=self.var_gate_hid, command=tog_gate_hid, bg="#1a1a1a", fg="white", selectcolor="#444").pack(anchor=tk.W, padx=5)

        def set_t(t): self.gate_tool=t
        tk.Button(p, text="[ PLACE BEAMGATE ]", command=lambda: set_t("GATE"), bg="#00FFFF", fg="black", width=24).pack(anchor=tk.CENTER, pady=5)
        tk.Button(p, text="[ PLACE KEYSECT ]", command=lambda: set_t("KEY"), bg="#FFFF00", fg="black", width=24).pack(anchor=tk.CENTER, pady=2)
        self.upd_lbl()
        self.draw_grid()

    def select_gate_slot(self, slot):
        self.current_gate_slot = slot; self.build_gate_ui()

    def build_item_ui(self):
        panel = self.panels['ITEM']
        for w in panel.winfo_children(): w.destroy()
        p = tk.Frame(panel, bg="#1a1a1a")
        p.pack(anchor=tk.NW, padx=5, pady=0)

        f_slots = tk.Frame(p, bg="#1a1a1a"); f_slots.pack(fill=tk.X, pady=5)

        for i in range(1, self.visible_item_slots + 1):
            bg = "#FF00FF" if i == self.current_item_slot else "#333"
            fg = "white"
            tk.Button(f_slots, text=str(i), bg=bg, fg=fg, width=2, command=lambda x=i: self.select_item_slot(x)).pack(side=tk.LEFT, padx=1)

        if self.visible_item_slots < MAX_SPECIAL_SLOTS:
            def add_slot():
                self.push_undo_snapshot()
                self.visible_item_slots += 1; self.build_item_ui()
            tk.Button(f_slots, text="+", bg="#880088", fg="white", width=2, command=add_slot).pack(side=tk.LEFT, padx=5)

        if self.visible_item_slots > 1:
            def rem_slot():
                self.push_undo_snapshot()
                idx = self.visible_item_slots
                old_cell = self.get_special_cell(self.items[idx])
                self.clear_special_auto_visual("ITEM", self.items[idx])
                self.items[idx] = {'active': False, 'x': -1, 'y': -1, 'keys': [], 'countdown': 300000,
                          'inactive_bp': 35, 'active_bp': 36, 'trigger_bp': 37, 'type': 1, 'hidden': False}
                self.visible_item_slots -= 1
                if self.current_item_slot > self.visible_item_slots: self.current_item_slot = self.visible_item_slots
                self.build_item_ui(); self.redraw_cells(old_cell)
            tk.Button(f_slots, text="-", bg="#880000", fg="white", width=2, command=rem_slot).pack(side=tk.LEFT, padx=2)

        i_data = self.items[self.current_item_slot]
        
        # --- PRESET DROPDOWN (ITEM) ---
        f_pre = tk.Frame(p, bg="#1a1a1a"); f_pre.pack(anchor=tk.W, pady=(10,2))
        tk.Label(f_pre, text="Model Preset:", bg="#1a1a1a", fg="#aaa", width=12, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        
        preset_values = ["Standard (35/36/37)", "Parasite (68/69/70)"]
        cb_preset = ttk.Combobox(f_pre, values=preset_values, state="readonly", width=20)
        cb_preset.pack(side=tk.LEFT)
        
        if i_data['inactive_bp'] == 35 and i_data['active_bp'] == 36 and i_data['trigger_bp'] == 37:
             cb_preset.set("Standard (35/36/37)")
        elif i_data['inactive_bp'] == 68 and i_data['active_bp'] == 69 and i_data['trigger_bp'] == 70:
             cb_preset.set("Parasite (68/69/70)")
        else:
             cb_preset.set("") 

        def on_preset_select(event):
            val = cb_preset.get()
            old_vals = (i_data['inactive_bp'], i_data['active_bp'], i_data['trigger_bp'])
            old_cell = self.get_special_cell(i_data)
            old_visual = self.get_special_auto_visual("ITEM", i_data)
            if "Standard" in val:
                new_vals = (35, 36, 37)
            elif "Parasite" in val:
                new_vals = (68, 69, 70)
            else:
                return
            if new_vals != old_vals:
                self.push_undo_snapshot()
                i_data['inactive_bp'], i_data['active_bp'], i_data['trigger_bp'] = new_vals
                self.sync_special_auto_visual("ITEM", i_data, old_cell=old_cell, old_visual=old_visual)
            self.build_item_ui() 
            self.draw_grid()

        cb_preset.bind("<<ComboboxSelected>>", on_preset_select)
        
        tk.Label(p, text="(Custom values allowed)", fg="#777", bg="#1a1a1a", font=("Arial", 7)).pack(anchor=tk.W, pady=(0,5))
        
        f = tk.Frame(p, bg="#1a1a1a"); f.pack(fill=tk.X, pady=5)

        tk.Label(f, text="Timer:", fg="white", bg="#1a1a1a", width=8).grid(row=0, column=0, sticky="e")
        e_cnt = tk.Entry(f, width=6); e_cnt.grid(row=0, column=1, sticky="w"); e_cnt.insert(0, str(i_data['countdown']))

        lbl_mins = tk.Label(f, text="", bg="#1a1a1a", fg="#00FF00", font=("Arial", 8))
        lbl_mins.grid(row=0, column=2, padx=2, sticky="w")

        tk.Label(f, text="Type:", fg="white", bg="#1a1a1a", width=5).grid(row=0, column=3, sticky="e")
        e_typ = ttk.Combobox(f, values=["Default"], width=8)
        e_typ.grid(row=0, column=4, sticky="w")
        e_typ.insert(0, self.format_item_type_value(i_data['type']))

        tk.Label(f, text="Off Model:", fg="white", bg="#1a1a1a", width=8).grid(row=1, column=0, sticky="e")
        e_ina = tk.Entry(f, width=5); e_ina.grid(row=1, column=1, sticky="w"); e_ina.insert(0, str(i_data['inactive_bp']))

        tk.Label(f, text="On:", fg="white", bg="#1a1a1a", width=5).grid(row=1, column=3, sticky="e")
        e_act = tk.Entry(f, width=5); e_act.grid(row=1, column=4, sticky="w"); e_act.insert(0, str(i_data['active_bp']))

        tk.Label(f, text="Trigger:", fg="white", bg="#1a1a1a", width=8).grid(row=2, column=0, sticky="e")
        e_trg = tk.Entry(f, width=5); e_trg.grid(row=2, column=1, sticky="w"); e_trg.insert(0, str(i_data['trigger_bp']))

        def upd(ev=None):
            try:
                new_countdown = int(e_cnt.get())
                new_type = self.parse_item_type_value(e_typ.get())
                if new_type is None:
                    raise ValueError
                new_inactive = int(e_ina.get())
                new_active = int(e_act.get())
                new_trigger = int(e_trg.get())
                if (
                    new_countdown != i_data['countdown'] or
                    new_type != i_data['type'] or
                    new_inactive != i_data['inactive_bp'] or
                    new_active != i_data['active_bp'] or
                    new_trigger != i_data['trigger_bp']
                ):
                    old_cell = self.get_special_cell(i_data)
                    old_visual = self.get_special_auto_visual("ITEM", i_data)
                    visual_changed = (
                        new_inactive != i_data['inactive_bp'] or
                        new_active != i_data['active_bp'] or
                        new_trigger != i_data['trigger_bp']
                    )
                    self.push_undo_snapshot()
                    i_data['countdown'] = new_countdown
                    i_data['type'] = new_type
                    i_data['inactive_bp'] = new_inactive
                    i_data['active_bp'] = new_active
                    i_data['trigger_bp'] = new_trigger
                    if visual_changed:
                        self.sync_special_auto_visual("ITEM", i_data, old_cell=old_cell, old_visual=old_visual)
                val = i_data['countdown']
                lbl_mins.config(text=f"{val/60000:.1f}m")
                
                if i_data['inactive_bp'] == 35 and i_data['active_bp'] == 36 and i_data['trigger_bp'] == 37:
                    cb_preset.set("Standard (35/36/37)")
                elif i_data['inactive_bp'] == 68 and i_data['active_bp'] == 69 and i_data['trigger_bp'] == 70:
                    cb_preset.set("Parasite (68/69/70)")
                else:
                    cb_preset.set("")
                    
                self.upd_lbl()
                self.draw_grid()
            except: lbl_mins.config(text=f"ERR")
        upd();
        for e in [e_cnt, e_typ, e_ina, e_act, e_trg]: e.bind("<KeyRelease>", upd)
        e_typ.bind("<<ComboboxSelected>>", upd)

        f_opt = tk.Frame(p, bg="#1a1a1a"); f_opt.pack(fill=tk.X, pady=(4, 2))
        self.var_item_hid = tk.BooleanVar(value=i_data.get('hidden', False))
        def tog_item_hid():
            val = self.var_item_hid.get()
            if i_data.get('hidden', False) != val:
                self.push_undo_snapshot()
                i_data['hidden'] = val
                self.dirty = True
        tk.Checkbutton(f_opt, text="Hide in Briefing", variable=self.var_item_hid, command=tog_item_hid, bg="#1a1a1a", fg="white", selectcolor="#444").pack(anchor=tk.W, padx=5)

        def set_t(t): self.item_tool=t
        f_place = tk.Frame(p, bg="#1a1a1a"); f_place.pack(anchor=tk.W, pady=(5, 0))
        tk.Button(f_place, text="[ PLACE BOMB ]", command=lambda: set_t("ITEM"), bg="#FF00FF", fg="black", width=24).pack(anchor=tk.W, pady=(0, 2))
        tk.Button(f_place, text="[ PLACE KEYSECT ]", command=lambda: set_t("KEY"), bg="#FF9900", fg="black", width=24).pack(anchor=tk.W)
        self.upd_lbl()
        self.draw_grid()

    def select_item_slot(self, slot):
        self.current_item_slot = slot; self.build_item_ui()

    def build_gem_ui(self):
        panel = self.panels['GEM']
        for w in panel.winfo_children(): w.destroy()
        p = tk.Frame(panel, bg="#1a1a1a")
        p.pack(fill=tk.X, anchor=tk.NW, padx=5, pady=0)

        # 1. SLOTS
        f_slots = tk.Frame(p, bg="#1a1a1a"); f_slots.pack(fill=tk.X, pady=5)
        for i in range(1, self.visible_gem_slots + 1):
            bg = "#00FF00" if i == self.current_gem_slot else "#333"
            fg = "black" if i == self.current_gem_slot else "white"
            tk.Button(f_slots, text=str(i), bg=bg, fg=fg, width=2, command=lambda x=i: self.select_gem_slot(x)).pack(side=tk.LEFT, padx=1)

        if self.visible_gem_slots < MAX_SPECIAL_SLOTS:
            def add_slot():
                self.push_undo_snapshot()
                self.visible_gem_slots += 1; self.build_gem_ui()
            tk.Button(f_slots, text="+", bg="#005500", fg="white", width=2, command=add_slot).pack(side=tk.LEFT, padx=5)

        if self.visible_gem_slots > 1:
            def rem_slot():
                self.push_undo_snapshot()
                idx = self.visible_gem_slots
                self.gems[idx] = {'x': -1, 'y': -1, 'blg': 50, 'type': 3, 'actions': [], 'hidden': False}
                self.visible_gem_slots -= 1
                if self.current_gem_slot > self.visible_gem_slots: self.current_gem_slot = self.visible_gem_slots
                self.build_gem_ui(); self.draw_grid()
            tk.Button(f_slots, text="-", bg="#880000", fg="white", width=2, command=rem_slot).pack(side=tk.LEFT, padx=2)

        data = self.gems[self.current_gem_slot]

        # 2. PROPERTIES (MODEL & TYPE)
        f_prop = tk.Frame(p, bg="#1a1a1a"); f_prop.pack(anchor=tk.W, pady=10)

        tk.Label(f_prop, text="Gem Model:", fg="white", bg="#1a1a1a").grid(row=0, column=0, sticky="e", padx=5, pady=2)

        cb_gem_model = ttk.Combobox(f_prop, values=self.GEM_MODEL_VALUES, width=20)
        cb_gem_model.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        cb_gem_model.set(self.format_gem_model_value(data['blg']))

        def apply_gem_model_from_combo(show_warning=False):
            new_blg = self.parse_gem_model_value(cb_gem_model.get())
            if new_blg is None:
                if show_warning:
                    messagebox.showwarning("Invalid Gem Model", "Enter a numeric building model ID, for example: 65")
                    cb_gem_model.set(self.format_gem_model_value(data['blg']))
                return
            if new_blg != data['blg']:
                self.push_undo_snapshot()
                data['blg'] = new_blg
                self.dirty = True
            if cb_gem_model.get().strip().isdigit() or new_blg in self.GEM_MODEL_LABELS:
                cb_gem_model.set(self.format_gem_model_value(new_blg))

        cb_gem_model.bind("<<ComboboxSelected>>", lambda e: apply_gem_model_from_combo(show_warning=True))
        cb_gem_model.bind("<Return>", lambda e: apply_gem_model_from_combo(show_warning=True))
        cb_gem_model.bind("<FocusOut>", lambda e: apply_gem_model_from_combo(show_warning=True))
        cb_gem_model.bind("<KeyRelease>", lambda e: apply_gem_model_from_combo(show_warning=False))
        tk.Label(f_prop, text="(Custom values allowed)", fg="#777", bg="#1a1a1a", font=("Arial", 7)).grid(row=1, column=1, sticky="w", padx=5, pady=(0,5))

        # TYPE DROPDOWN
        tk.Label(f_prop, text="Type:", fg="white", bg="#1a1a1a").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        type_map = {1: "1 (Weapon/Pwr)", 2: "2 (Shield)", 3: "3 (Tech/Unlock)"}
        rev_map = {v: k for k, v in type_map.items()}
        current_display = type_map.get(data['type'], "3 (Tech/Unlock)")
        type_var = tk.StringVar(value=current_display)
        def upd_t(val):
             new_type = rev_map.get(val, 3)
             if new_type != data['type']:
                 self.push_undo_snapshot()
                 data['type'] = new_type
             self.upd_lbl(); self.draw_grid()
        om = ttk.OptionMenu(f_prop, type_var, current_display, *type_map.values(), command=upd_t)
        om.config(width=16)
        om.grid(row=2, column=1, sticky="w", padx=5, pady=2)

        f_opt = tk.Frame(p, bg="#1a1a1a"); f_opt.pack(fill=tk.X, pady=(0, 6))
        self.var_gem_hid = tk.BooleanVar(value=data.get('hidden', False))
        def tog_gem_hid():
            val = self.var_gem_hid.get()
            if data.get('hidden', False) != val:
                self.push_undo_snapshot()
                data['hidden'] = val
                self.dirty = True
        tk.Checkbutton(f_opt, text="Hide in Briefing", variable=self.var_gem_hid, command=tog_gem_hid, bg="#1a1a1a", fg="white", selectcolor="#444").pack(anchor=tk.W, padx=5)

        # 3. ACTIONS
        tk.Label(p, text="--- ACTIONS ---", fg="#00FF00", bg="#1a1a1a", font=("bold")).pack(anchor=tk.W, pady=(15,5))
        f_act = tk.Frame(p, bg="#1a1a1a"); f_act.pack(anchor=tk.W)

        # Define Variables first
        tgt_type_var = tk.StringVar(value="modify_vehicle")

        tk.Label(f_act, text="Modify:", fg="white", bg="#1a1a1a").grid(row=0, column=0, sticky="w", padx=5)

        # Dropdown Modify
        om_mod = ttk.OptionMenu(f_act, tgt_type_var, "modify_vehicle", "modify_vehicle", "modify_building", "modify_weapon")
        om_mod.config(width=17)
        om_mod.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 4))

        tk.Label(f_act, text="ID:", fg="white", bg="#1a1a1a").grid(row=2, column=0, sticky="w", padx=5)
        cb_target_id = ttk.Combobox(f_act, width=24)
        cb_target_id.grid(row=3, column=0, sticky="w", padx=5, pady=(0, 4))

        tk.Label(f_act, text="Do:", fg="white", bg="#1a1a1a").grid(row=4, column=0, sticky="w", padx=5)

        param_combo = ttk.Combobox(f_act, values=["enable", "add_energy", "add_shield", "num_weapons"], width=17)
        param_combo.set("enable")
        param_combo.grid(row=5, column=0, sticky="w", padx=5, pady=(0, 4))

        tk.Label(f_act, text="Val:", fg="white", bg="#1a1a1a").grid(row=6, column=0, sticky="w", padx=5)
        e_val = tk.Entry(f_act, width=8); e_val.grid(row=7, column=0, sticky="w", padx=5)
        e_val.insert(0,"0")

        # Custom Definition Note
        tk.Label(f_act, text="Custom definition allowed", fg="#777", bg="#1a1a1a", font=("Arial", 7)).grid(row=8, column=0, sticky="w", padx=5, pady=(0,5))

        # LOGIC FOR AUTO-UPDATE (action controls only)
        def on_modify_change(*args):
            sel = tgt_type_var.get()
            values = []
            if sel == "modify_vehicle":
                param_combo['values'] = ["enable", "add_energy", "add_shield", "num_weapons"]
                param_combo.set("enable")
                values = self.definition_combo_values('veh')
            elif sel == "modify_building":
                param_combo['values'] = ["enable"]
                param_combo.set("enable")
                values = self.definition_combo_values('blg')
            elif sel == "modify_weapon":
                param_combo['values'] = ["add_energy"]
                param_combo.set("add_energy")
                values = self.definition_combo_values('weapon')
            cb_target_id['values'] = values
            cb_target_id.set(values[0] if values else "0")
            self.upd_lbl()
            self.draw_grid()

        tgt_type_var.trace("w", on_modify_change)
        on_modify_change()

        # LISTBOX & SCROLLBAR
        lb_frame = tk.Frame(p); lb_frame.pack(anchor=tk.W, padx=0, pady=5)
        lb = tk.Listbox(lb_frame, height=5, width=32, bg="#222", fg="white", selectbackground="#008888", selectforeground="white", font=("Courier", 9))
        lb.pack(side=tk.LEFT)
        sb = tk.Scrollbar(
            lb_frame,
            command=lb.yview,
            bg="#00B8B8",
            activebackground="#3DF0F0",
            troughcolor="#0f1f1f",
            width=16,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            elementborderwidth=1,
            activerelief=tk.FLAT
        ); sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.config(yscrollcommand=sb.set)

        def refresh_list():
            lb.delete(0, tk.END)
            for a in data['actions']:
                tgt = a['target_type'].replace("modify_", "")
                lb.insert(tk.END, f"{tgt}{a['id']}:{a['param']}={a['val']}")

        def add_action():
            try:
                tid = self.parse_leading_int(cb_target_id.get())
                if tid is None:
                    raise ValueError
                val = e_val.get()
                prm = param_combo.get().strip()
                if not prm: return
                self.push_undo_snapshot()
                action = {'target_type': tgt_type_var.get(), 'id': tid, 'param': prm, 'val': val}
                data['actions'].append(action)
                refresh_list()
            except: messagebox.showerror("Error", "Invalid ID")

        def del_action():
            sel = lb.curselection()
            if sel:
                self.push_undo_snapshot()
                data['actions'].pop(sel[0]); refresh_list()

        refresh_list()
        f_btns = tk.Frame(p, bg="#1a1a1a"); f_btns.pack(anchor=tk.W, pady=2)
        tk.Button(f_btns, text="ADD", command=add_action, bg="#005500", fg="white", width=8).pack(side=tk.LEFT, padx=10)
        tk.Button(f_btns, text="DEL", command=del_action, bg="#550000", fg="white", width=8).pack(side=tk.RIGHT, padx=10)

        # 4. PLACE BUTTON
        f_place = tk.Frame(p, bg="#1a1a1a")
        f_place.pack(anchor=tk.W, padx=5, pady=10)
        tk.Button(f_place, text="[ PLACE GEM ON MAP ]", command=lambda: self.set_gem_tool(), bg="#00FF00", fg="black", width=24).pack()
        self.upd_lbl()
        self.draw_grid()

    def select_gem_slot(self, slot):
        self.current_gem_slot = slot; self.build_gem_ui()

    def set_gem_tool(self):
        if not self.gems[self.current_gem_slot]['actions']:
             messagebox.showinfo("Error", "Define actions in the Upgrade panel first.")
             return
        self.gem_tool = "GEM"

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
                cell = self.get_squad_cell(self.current_squad_index)
                if self.squads[self.current_squad_index]['owner'] != f:
                    self.push_undo_snapshot()
                self.squads[self.current_squad_index]['owner'] = f
                self.refresh_squad_list(redraw=False)
                self.redraw_cells(cell)
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
                cell = self.get_squad_cell(self.current_squad_index)
                val = self.cb_veh.get().strip()
                match = re.match(r'^(\d+)\s*-\s*(.*)$', val)
                old_veh = self.squads[self.current_squad_index]['veh']
                old_name = self.squads[self.current_squad_index]['custom_name']
                changed = False
                if match:
                    new_veh = int(match.group(1))
                    new_name = match.group(2).strip() if match.group(2) else old_name
                    changed = (new_veh != old_veh) or (new_name != old_name)
                    if changed:
                        self.push_undo_snapshot()
                    self.squads[self.current_squad_index]['veh'] = new_veh
                    if match.group(2): self.squads[self.current_squad_index]['custom_name'] = new_name
                else:
                    try: 
                        new_veh = int(val)
                        changed = (new_veh != old_veh) or ("Custom_Unit" != old_name)
                        if changed:
                            self.push_undo_snapshot()
                        self.squads[self.current_squad_index]['veh'] = new_veh
                        self.squads[self.current_squad_index]['custom_name'] = "Custom_Unit"
                    except: pass
                self.refresh_squad_list(redraw=False)
                self.redraw_cells(cell)
        self.cb_veh.bind("<<ComboboxSelected>>", on_veh_change)
        self.cb_veh.bind("<KeyRelease>", on_veh_change)

        tk.Label(p, text="To customize: Type 'ID - Name' directly above", fg="#aaa", bg="#1a1a1a", font=("Arial", 8, "italic")).pack(anchor=tk.W, padx=5, pady=(0,5))

        f_cnt = tk.Frame(p, bg="#1a1a1a"); f_cnt.pack(fill=tk.X, pady=2)
        tk.Label(f_cnt, text="Count:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)
        self.e_squad_cnt = tk.Entry(f_cnt, width=5); self.e_squad_cnt.pack(side=tk.LEFT, padx=5)
        self.e_squad_cnt.insert(0, str(self.current_squad_data['num']))

        def upd_cnt(ev):
            val = 1
            try: val = int(self.e_squad_cnt.get())
            except: pass
            
            if self.current_squad_index != -1:
                cell = self.get_squad_cell(self.current_squad_index)
                if self.squads[self.current_squad_index]['num'] != val:
                    self.push_undo_snapshot()
                self.squads[self.current_squad_index]['num'] = val
                self.refresh_squad_list(redraw=False)
                self.redraw_cells(cell)
            else:
                self.current_squad_data['num'] = val
        self.e_squad_cnt.bind("<KeyRelease>", upd_cnt)

        # --- HIDDEN CHECKBOX ---
        f_opt = tk.Frame(p, bg="#1a1a1a"); f_opt.pack(fill=tk.X, pady=5)
        self.var_squad_hid = tk.BooleanVar(value=self.current_squad_data['hidden'])
        
        def tog_hid():
            val = self.var_squad_hid.get()
            if self.current_squad_index != -1:
                cell = self.get_squad_cell(self.current_squad_index)
                if self.squads[self.current_squad_index]['hidden'] != val:
                    self.push_undo_snapshot()
                self.squads[self.current_squad_index]['hidden'] = val
                self.refresh_squad_list(redraw=False)
                self.redraw_cells(cell)
            else:
                self.current_squad_data['hidden'] = val

        tk.Checkbutton(f_opt, text="Hide in Briefing", variable=self.var_squad_hid, command=tog_hid, bg="#1a1a1a", fg="white", selectcolor="#444").pack(anchor=tk.W, padx=5)

        f_list = tk.Frame(p, bg="#1a1a1a"); f_list.pack(fill=tk.BOTH, expand=True, padx=5)
        tk.Label(f_list, text="Left-Click map to place", bg="#1a1a1a", fg="white").pack(anchor=tk.W)
        tk.Label(f_list, text="Right-Click map to remove", bg="#1a1a1a", fg="white").pack(anchor=tk.W)

        self.lb_squads = tk.Listbox(f_list, bg="#222", fg="white", height=10,
                                    selectbackground="#008888", selectforeground="white")
        self.lb_squads.pack(fill=tk.BOTH, expand=True)
        self.lb_squads.bind('<<ListboxSelect>>', self.on_squad_select)

        def delete_selected_squad():
            sel = self.lb_squads.curselection()
            if not sel: return
            idx = sel[0]
            cell = self.get_squad_cell(idx)
            self.push_undo_snapshot()
            self.squads.pop(idx)
            self.current_squad_index = -1 
            self.invalidate_render_indexes()
            self.refresh_squad_list(redraw=False)
            self.redraw_cells(cell)
            self.var_squad_hid.set(self.current_squad_data['hidden'])

        tk.Button(f_list, text="[ DELETE SELECTED SQUAD ]", command=delete_selected_squad, bg="#880000", fg="white", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=5)
        self.refresh_squad_list()

    def on_squad_select(self, evt):
        previous_cell = self.get_squad_cell(self.current_squad_index)
        sel = self.lb_squads.curselection()
        if sel:
            idx = sel[0]
            self.current_squad_index = idx
            s = self.squads[idx]
            selected_cell = self.get_squad_cell(idx)
            
            self.var_squad_hid.set(s['hidden'])
            self.e_squad_cnt.delete(0, tk.END)
            self.e_squad_cnt.insert(0, str(s['num']))
            vname = s['custom_name'] if s['custom_name'] else self.defs['veh'].get(s['veh'], "Unknown")
            self.cb_veh.set(f"{s['veh']} - {vname}")
            f = s['owner']
            self.btn_squad_fac.config(text=f"{f} ({FACTIONS[f][0]})", fg=FACTIONS[f][1] if FACTIONS[f][1] else "white")

        else:
            self.current_squad_index = -1
            selected_cell = None
        
        self.redraw_cells(previous_cell, selected_cell)

    def refresh_squad_list(self, redraw=True):
        if not hasattr(self, 'lb_squads') or not self.lb_squads.winfo_exists(): return
        self.lb_squads.delete(0, tk.END)
        for i, s in enumerate(self.squads):
            vname = s['custom_name'] if s['custom_name'] else self.defs['veh'].get(s['veh'], "Unknown")
            faction_name = self.get_faction_display_name(s['owner'])
            hidden_tag = " (Hidden)" if s.get('hidden', False) else ""
            txt = f"{i}: {faction_name} (ID:{s['owner']}), {vname} (ID:{s['veh']}), Num: {s['num']}{hidden_tag}"
            self.lb_squads.insert(tk.END, txt)

            color = FACTION_TEXT_COLORS.get(s['owner'], "#FFFFFF")
            self.lb_squads.itemconfig(i, {'fg': color})
            
            if i == self.current_squad_index:
                self.lb_squads.selection_set(i)
                self.lb_squads.activate(i)

        if redraw:
            self.draw_grid()

    def build_host_ui(self):
        p = self.panels['HOST']
        for w in p.winfo_children(): w.destroy()

        tk.Label(p, text="HOST STATION PLACER", bg="#FFD700", fg="black", font=("bold", 12)).pack(fill=tk.X, pady=(10,5))

        # Faction
        f_fac = tk.Frame(p, bg="#1a1a1a"); f_fac.pack(fill=tk.X, pady=2)
        tk.Label(f_fac, text="Owner:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        self.btn_host_fac = tk.Menubutton(f_fac, text="", bg="#333", fg="white", relief="raised", width=18)
        self.btn_host_fac.pack(side=tk.LEFT, padx=5)

        def set_host_fac(f):
            if self.current_host_index != -1:
                cell = self.get_host_cell(self.current_host_index)
                if self.host_stations[self.current_host_index]['owner'] != f:
                    self.push_undo_snapshot()
                self.host_stations[self.current_host_index]['owner'] = f
                self.refresh_host_list(redraw=False)
                self.redraw_cells(cell)
            else:
                self.current_host_data['owner'] = f
            
            self.btn_host_fac.config(text=self.format_player_owner_value(f), fg=FACTIONS[f][1] if FACTIONS[f][1] else "white")

        menu = tk.Menu(self.btn_host_fac, tearoff=0)
        self.btn_host_fac.configure(menu=menu)
        for i in range(1, 8):
            menu.add_command(label=self.format_player_owner_value(i), command=lambda x=i: set_host_fac(x))
        
        curr = self.current_host_data['owner']
        self.btn_host_fac.config(text=self.format_player_owner_value(curr), fg=FACTIONS[curr][1] if FACTIONS[curr][1] else "white")

        def set_player_owner(new_owner):
            old_owner = getattr(self, 'player_owner', 1)
            if new_owner != old_owner:
                self.push_undo_snapshot()
                self.player_owner = new_owner
                self.dirty = True
                self.refresh_host_list(redraw=False)
            else:
                self.player_owner = new_owner
            if hasattr(self, "btn_player_owner") and self.btn_player_owner.winfo_exists():
                self.btn_player_owner.config(
                    text=self.format_player_owner_value(self.player_owner),
                    fg=FACTIONS[self.player_owner][1] if FACTIONS[self.player_owner][1] else "white"
                )

        # Vehicle Type
        f_veh = tk.Frame(p, bg="#1a1a1a"); f_veh.pack(fill=tk.X, pady=2)
        tk.Label(f_veh, text="Station Type:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        host_list = []
        sorted_hosts = sorted(self.defs['host'].items())
        for vid, name in sorted_hosts:
            host_list.append(f"{vid} - {name}")

        self.cb_host = ttk.Combobox(f_veh, values=host_list, width=23)
        self.cb_host.pack(side=tk.LEFT, padx=5)
        
        curr_v = self.current_host_data['veh']
        self.cb_host.set(f"{curr_v} - {self.defs['host'].get(curr_v, 'Unknown')}")

        def on_host_change(ev):
            if self.current_host_index != -1:
                cell = self.get_host_cell(self.current_host_index)
                val = self.cb_host.get().strip()
                match = re.match(r'^(\d+)\s*-\s*(.*)$', val)
                old_veh = self.host_stations[self.current_host_index]['veh']
                old_name = self.host_stations[self.current_host_index]['custom_name']
                if match:
                    new_veh = int(match.group(1))
                    new_name = match.group(2).strip() if match.group(2) else old_name
                    if new_veh != old_veh or new_name != old_name:
                        self.push_undo_snapshot()
                    self.host_stations[self.current_host_index]['veh'] = new_veh
                    if match.group(2): self.host_stations[self.current_host_index]['custom_name'] = new_name
                else:
                    try: 
                        new_veh = int(val)
                        if new_veh != old_veh or old_name != "Custom_Host":
                            self.push_undo_snapshot()
                        self.host_stations[self.current_host_index]['veh'] = new_veh
                        self.host_stations[self.current_host_index]['custom_name'] = "Custom_Host"
                    except: pass
                self.refresh_host_list(redraw=False)
                self.redraw_cells(cell)
        self.cb_host.bind("<<ComboboxSelected>>", on_host_change)
        self.cb_host.bind("<KeyRelease>", on_host_change)

        tk.Label(p, text="To customize: Type 'ID - Name' directly above", fg="#aaa", bg="#1a1a1a", font=("Arial", 8, "italic")).pack(anchor=tk.W, padx=5, pady=(0,5))

        # Energy & Altitude
        f_stats = tk.Frame(p, bg="#1a1a1a"); f_stats.pack(fill=tk.X, pady=2)

        tk.Label(f_stats, text="Energy:", fg="white", bg="#1a1a1a").grid(row=0, column=0, padx=5, sticky="e")
        self.e_host_en = tk.Entry(f_stats, width=10)
        self.e_host_en.grid(row=0, column=1, padx=5, sticky="w")
        self.e_host_en.insert(0, str(self.current_host_data['energy']))

        self.cb_host_energy_preset = ttk.Combobox(f_stats, values=self.HOST_ENERGY_PRESET_VALUES, state="readonly", width=10)
        self.cb_host_energy_preset.grid(row=0, column=2, padx=5, sticky="w")

        tk.Label(f_stats, text="Altitude (Y):", fg="white", bg="#1a1a1a").grid(row=1, column=0, padx=5, pady=(4, 0), sticky="e")
        self.e_host_y = tk.Entry(f_stats, width=6)
        self.e_host_y.grid(row=1, column=1, padx=5, pady=(4, 0), sticky="w")
        self.e_host_y.insert(0, str(self.current_host_data['pos_y']))

        tk.Label(f_stats, text="(Default: -330)", fg="#888", bg="#1a1a1a", font=("Arial", 8)).grid(row=1, column=2, padx=5, pady=(4, 0), sticky="w")

        def upd_host_stats(ev=None):
            if self.current_host_index != -1:
                try:
                    cell = self.get_host_cell(self.current_host_index)
                    new_energy = int(self.e_host_en.get())
                    new_pos_y = int(self.e_host_y.get())
                    curr = self.host_stations[self.current_host_index]
                    if curr['energy'] != new_energy or curr['pos_y'] != new_pos_y:
                        self.push_undo_snapshot()
                    self.host_stations[self.current_host_index]['energy'] = new_energy
                    self.host_stations[self.current_host_index]['pos_y'] = new_pos_y
                    self.refresh_host_list(redraw=False)
                    self.redraw_cells(cell)
                    self.update_host_energy_controls(new_energy)
                except: pass
            else:
                try:
                    new_energy = int(self.e_host_en.get())
                    self.current_host_data['energy'] = new_energy
                    self.current_host_data['pos_y'] = int(self.e_host_y.get())
                    self.update_host_energy_controls(new_energy)
                except: pass
        self.e_host_en.bind("<KeyRelease>", upd_host_stats)
        self.e_host_y.bind("<KeyRelease>", upd_host_stats)

        def on_energy_preset_select(event=None):
            val = self.cb_host_energy_preset.get()
            preset_energy = self.parse_host_energy_preset_value(val)
            if preset_energy is None:
                self.update_host_energy_controls()
                return
            self.e_host_en.delete(0, tk.END)
            self.e_host_en.insert(0, str(preset_energy))
            upd_host_stats()

        self.cb_host_energy_preset.bind("<<ComboboxSelected>>", on_energy_preset_select)
        self.update_host_energy_controls(self.current_host_data['energy'])

        # --- HOST HIDE OPTION ---
        f_opt = tk.Frame(p, bg="#1a1a1a"); f_opt.pack(fill=tk.X, pady=5)
        self.var_host_hid = tk.BooleanVar(value=self.current_host_data['hidden'])
        
        def tog_host_hid():
            val = self.var_host_hid.get()
            if self.current_host_index != -1:
                cell = self.get_host_cell(self.current_host_index)
                if self.host_stations[self.current_host_index]['hidden'] != val:
                    self.push_undo_snapshot()
                self.host_stations[self.current_host_index]['hidden'] = val
                self.refresh_host_list(redraw=False)
                self.redraw_cells(cell)
            else:
                self.current_host_data['hidden'] = val

        tk.Checkbutton(f_opt, text="Hide in Briefing", variable=self.var_host_hid, command=tog_host_hid, bg="#1a1a1a", fg="white", selectcolor="#444").pack(side=tk.LEFT, padx=5)

        f_player = tk.Frame(p, bg="#1a1a1a"); f_player.pack(fill=tk.X, pady=(0, 5))
        tk.Label(f_player, text="Player faction:", fg="white", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)
        self.btn_player_owner = tk.Menubutton(f_player, text="", bg="#333", fg="white", relief="raised", width=18)
        self.btn_player_owner.pack(side=tk.LEFT, padx=5)
        player_menu = tk.Menu(self.btn_player_owner, tearoff=0)
        self.btn_player_owner.configure(menu=player_menu)
        for i in range(1, 8):
            player_menu.add_command(label=self.format_player_owner_value(i), command=lambda x=i: set_player_owner(x))
        set_player_owner(getattr(self, 'player_owner', 1))

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
            cell = self.get_host_cell(idx)
            self.push_undo_snapshot()
            self.host_stations.pop(idx)
            self.current_host_index = -1
            self.invalidate_render_indexes()
            self.refresh_host_list(redraw=False)
            self.redraw_cells(cell)
            self.var_host_hid.set(self.current_host_data['hidden'])

        tk.Button(f_list, text="[ DELETE SELECTED HOST ]", command=delete_selected_host, bg="#880000", fg="white", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=5)
        self.refresh_host_list()

    def on_host_select(self, evt):
        previous_cell = self.get_host_cell(self.current_host_index)
        sel = self.lb_hosts.curselection()
        if sel:
            idx = sel[0]
            self.current_host_index = idx
            h = self.host_stations[idx]
            selected_cell = self.get_host_cell(idx)

            self.var_host_hid.set(h['hidden'])
            
            self.e_host_en.delete(0, tk.END); self.e_host_en.insert(0, str(h['energy']))
            self.e_host_y.delete(0, tk.END); self.e_host_y.insert(0, str(h['pos_y']))
            self.update_host_energy_controls(h['energy'])

            vname = h['custom_name'] if h['custom_name'] else self.defs['host'].get(h['veh'], "Unknown")
            self.cb_host.set(f"{h['veh']} - {vname}")

            f = h['owner']
            self.btn_host_fac.config(text=self.format_player_owner_value(f), fg=FACTIONS[f][1] if FACTIONS[f][1] else "white")

        else:
            self.current_host_index = -1
            selected_cell = None
            self.update_host_energy_controls(self.current_host_data['energy'])
        self.redraw_cells(previous_cell, selected_cell)

    def refresh_host_list(self, redraw=True):
        if not hasattr(self, 'lb_hosts') or not self.lb_hosts.winfo_exists(): return
        self.lb_hosts.delete(0, tk.END)
        player_index = -1
        for idx, host in enumerate(self.host_stations):
            if host.get('owner') == getattr(self, 'player_owner', 1):
                player_index = idx
                break
        for i, h in enumerate(self.host_stations):
            vname = h['custom_name']
            if not vname: vname = self.defs['host'].get(h['veh'], "Unknown")

            faction_name = self.get_faction_display_name(h['owner'])
            hidden_tag = " (Hidden)" if h.get('hidden', False) else ""
            player_tag = " [PLAYER]" if i == player_index else ""
            txt = (
                f"{i}:{player_tag} {faction_name} (ID:{h['owner']}), "
                f"{vname} (ID:{h['veh']}), "
                f"HP: {h['energy']}, Altitude (Y): {h.get('pos_y', -330)}"
                f"{hidden_tag}"
            )
            self.lb_hosts.insert(tk.END, txt)

            color = FACTION_TEXT_COLORS.get(h['owner'], "#FFFFFF")
            self.lb_hosts.itemconfig(i, {'fg': color})
            
            if i == self.current_host_index:
                self.lb_hosts.selection_set(i)
                self.lb_hosts.activate(i)

        if redraw:
            self.draw_grid()

    def build_tech_ui(self):
        p = self.panels['TECH']
        for w in p.winfo_children(): w.destroy()
        h = tk.Frame(p, bg="#1a1a1a", height=40); h.pack(fill=tk.X)
        h_inner = tk.Frame(h, bg="#1a1a1a")
        h_inner.pack(anchor=tk.W)
        
        # MOD: Nav Logic Range to 7 (Drones)
        def nav_tech(d):
            self.curr_tech_faction = 1 if self.curr_tech_faction+d > 7 else 7 if self.curr_tech_faction+d < 1 else self.curr_tech_faction+d
            self.update_tech_header(lbl_faction, lbl_num)
            self.draw_tech_list()
            self.upd_lbl()
            
        tk.Button(h_inner, text="<", command=lambda: nav_tech(-1), bg="#333", fg="white", font=("bold",12)).pack(side=tk.LEFT, padx=(10, 2))
        tk.Button(h_inner, text=">", command=lambda: nav_tech(1), bg="#333", fg="white", font=("bold",12)).pack(side=tk.LEFT, padx=(2, 8))
        lbl_num = tk.Label(h_inner, text="01", bg="#333", font=("Arial", 14, "bold"), width=3); lbl_num.pack(side=tk.LEFT, padx=5)

        lbl_faction = tk.Label(h_inner, text="", bg="#1a1a1a", font=("Arial", 12, "bold"), anchor=tk.W, width=14)
        lbl_faction.pack(side=tk.LEFT, padx=5)
        self.update_tech_header(lbl_faction, lbl_num)

        f_cust = tk.Frame(p, bg="#1a1a1a"); f_cust.pack(fill=tk.X, pady=2)
        tk.Label(f_cust, text="Custom ID:", bg="#1a1a1a", fg="#aaa").pack(side=tk.LEFT, padx=5)
        e_cust = tk.Entry(f_cust, width=5); e_cust.pack(side=tk.LEFT)

        tk.Label(f_cust, text="Name:", fg="#aaa", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)
        e_name = tk.Entry(f_cust, width=8); e_name.pack(side=tk.LEFT)

        def add_cust_tech(kind):
            try:
                vid = int(e_cust.get())
                cname = e_name.get().strip()
                lst = self.tech[self.curr_tech_faction][kind]
                changed = False
                if cname and self.custom_tech_names.get(vid) != cname:
                    changed = True
                if vid not in lst:
                    changed = True
                if not changed:
                    return
                self.push_undo_snapshot()
                if cname:
                    self.custom_tech_names[vid] = cname
                if vid not in lst:
                    lst.append(vid)
                self.draw_tech_list()
            except: pass
        tk.Button(f_cust, text="+ VEH", command=lambda: add_cust_tech('veh'), bg="#444", fg="white", font=("Arial",7)).pack(side=tk.LEFT, padx=2)
        tk.Button(f_cust, text="+ BLG", command=lambda: add_cust_tech('blg'), bg="#444", fg="white", font=("Arial",7)).pack(side=tk.LEFT, padx=2)

        self.cv_tech = tk.Canvas(p, bg="#222", highlightthickness=0)
        self.sb_tech = tk.Scrollbar(
            p,
            command=self.cv_tech.yview,
            bg="#00B8B8",
            activebackground="#3DF0F0",
            troughcolor="#0f1f1f",
            width=16,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            elementborderwidth=1,
            activerelief=tk.FLAT
        )
        self.cv_tech.configure(yscrollcommand=self.sb_tech.set)
        self.sb_tech.pack(side=tk.RIGHT, fill=tk.Y); self.cv_tech.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.cv_tech.bind("<Configure>", lambda e: self.draw_tech_list())
        self.bind_scroll(self.cv_tech)
        self.cv_tech.bind("<Button-1>", self.on_tech_click)
        self.cv_tech.bind("<B1-Motion>", self.on_tech_drag)
        self.cv_tech.bind("<ButtonRelease-1>", self.on_tech_release)
        self.cv_tech.bind("<Button-3>", self.on_tech_right_click)
        self.cv_tech.bind("<B3-Motion>", self.on_tech_drag)
        self.cv_tech.bind("<ButtonRelease-3>", self.on_tech_release)

        self.root.after(50, self.draw_tech_list)

    def update_tech_header(self, lbl_name, lbl_n):
        fid = self.curr_tech_faction
        fname, fcolor = FACTIONS[fid]
        if fid == 3:
            fname = "MYKONIAN"
        lbl_name.config(text=fname, fg=fcolor)
        lbl_n.config(text=f"{fid:02d}", fg=fcolor)

    def get_tech_list_items(self):
        items = []
        for uid, name in self.defs['veh'].items():
             if uid in self.custom_tech_names: name = self.custom_tech_names[uid]
             items.append(('veh', uid, name))
        for uid, name in self.defs['blg'].items():
             if uid in self.custom_tech_names: name = self.custom_tech_names[uid]
             items.append(('blg', uid, name))

        fid = self.curr_tech_faction
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
        return items

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

        items = self.get_tech_list_items()
        active_veh = self.tech[fid]['veh']; active_blg = self.tech[fid]['blg']

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
            item_w = max(TECH_ITEM_W, width - 20)
            tag = f"item_{cat}_{uid}"
            self.cv_tech.create_rectangle(x, y, x + item_w, y + TECH_ITEM_H - 4, fill=bg_color, outline=border_color, width=line_w, tags=tag)
            prefix = "vehicle" if cat == "veh" else "building"
            self.cv_tech.create_text(x + 10, y + (TECH_ITEM_H/2) - 3, text=f"{prefix} = {uid} ; {name}", fill=text_color, anchor=tk.W, font=("Courier", 9, "bold" if is_active else "normal"), tags=tag)
        self.cv_tech.config(scrollregion=(0, 0, max(width, TECH_ITEM_W + 20), len(items) * TECH_ITEM_H + 20))

    def on_tech_click(self, e):
        self.start_tech_drag(e, "enable")

    def on_tech_right_click(self, e):
        self.start_tech_drag(e, "disable")
        return "break"

    def start_tech_drag(self, e, action):
        self._tech_drag_active = True
        self._tech_dragging = False
        self._tech_drag_snapshot_taken = False
        self._tech_drag_start = (e.x, e.y)
        self._tech_drag_action = action
        self._last_dragged_id = None

    def on_tech_drag(self, e):
        if not getattr(self, "_tech_drag_active", False):
            return
        start_x, start_y = getattr(self, "_tech_drag_start", (e.x, e.y))
        if abs(e.x - start_x) + abs(e.y - start_y) >= 4:
            self._tech_dragging = True
        if self._tech_dragging:
            self.apply_tech_drag_hit(e.x, e.y)

    def on_tech_release(self, e):
        if getattr(self, "_tech_dragging", False):
            self.apply_tech_drag_hit(e.x, e.y)
        elif getattr(self, "_tech_drag_action", "enable") == "disable":
            self.deactivate_tech_hit(e.x, e.y)
        else:
            self.process_tech_hit(e.x, e.y)
        self._tech_drag_active = False
        self._tech_dragging = False
        self._tech_drag_snapshot_taken = False
        self._tech_drag_action = "enable"
        self._last_dragged_id = None
        if getattr(e, "num", None) == 3:
            return "break"

    def get_tech_hit_item(self, x, y):
        cy = int(self.cv_tech.canvasy(y)); idx = cy // TECH_ITEM_H
        items = self.get_tech_list_items()
        if 0 <= idx < len(items):
            cat, uid, name = items[idx]
            return cat, uid
        return None

    def push_tech_drag_undo_once(self):
        if not getattr(self, "_tech_drag_snapshot_taken", False):
            self.push_undo_snapshot()
            self._tech_drag_snapshot_taken = True

    def apply_tech_drag_hit(self, x, y):
        action = getattr(self, "_tech_drag_action", "enable")
        if action == "disable":
            self.deactivate_tech_hit(x, y)
        else:
            self.activate_tech_hit(x, y)

    def activate_tech_hit(self, x, y):
        hit = self.get_tech_hit_item(x, y)
        if not hit:
            return
        cat, uid = hit
        unique_id = f"{cat}_{uid}"
        if unique_id == self._last_dragged_id:
            return
        self._last_dragged_id = unique_id

        lst = self.tech[self.curr_tech_faction][cat]
        if uid not in lst:
            self.push_tech_drag_undo_once()
            lst.append(uid)
            self.draw_tech_list()

    def deactivate_tech_hit(self, x, y):
        hit = self.get_tech_hit_item(x, y)
        if not hit:
            return
        cat, uid = hit
        unique_id = f"{cat}_{uid}"
        if unique_id == self._last_dragged_id:
            return
        self._last_dragged_id = unique_id

        lst = self.tech[self.curr_tech_faction][cat]
        if uid in lst:
            self.push_tech_drag_undo_once()
            lst.remove(uid)
            self.draw_tech_list()

    def process_tech_hit(self, x, y):
        hit = self.get_tech_hit_item(x, y)
        if hit:
            cat, uid = hit
            lst = self.tech[self.curr_tech_faction][cat]
            self.push_undo_snapshot()
            if uid in lst: lst.remove(uid)
            else: lst.append(uid)
            self.draw_tech_list()

    def build_script_ui(self):
        p = self.panels['SCRIPT']
        for w in p.winfo_children(): w.destroy()

        tk.Label(p, text="LEVEL SCRIPT (LDF)", fg="#008080", bg="#1a1a1a", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(p, text="Write custom LDF commands here", fg="#aaa", bg="#1a1a1a", font=("Arial", 9)).pack(pady=2)

        txt = tk.Text(p, bg="#111", fg="#00FF00", font=("Courier", 10), insertbackground="white", height=20)
        txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        txt.insert("1.0", self.script_content)
        self.script_text_widget = txt

        def save_script():
            self.sync_script_widget_to_data(push_undo=True)
            messagebox.showinfo("Script", "Script saved successfully!")

        tk.Button(p, text="SAVE SCRIPT", command=save_script, bg="#005555", fg="white", font=("bold")).pack(fill=tk.X, padx=5, pady=5)
