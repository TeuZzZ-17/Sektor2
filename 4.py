# --- START 4.py ---
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

# --- END 4.py ---
