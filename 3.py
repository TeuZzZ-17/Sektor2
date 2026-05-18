# --- START 3.py ---
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

# --- END 3.py ---
