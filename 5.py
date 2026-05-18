# --- START 5.py ---
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

# --- END 5.py ---
