# --- START 2.py ---
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

# --- END 2.py ---
