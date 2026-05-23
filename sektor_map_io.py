import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import copy
import re
import platform
import subprocess

from sektor_constants import *
from sektor_paths import resource_path

class MapIOMixin:

    def split_user_script_block(self, raw_text):
        marker = re.search(r'(?im)^[ \t]*;[ \t]*---[ \t]*USER SCRIPT[ \t]*---[ \t\r]*$', raw_text)
        if not marker:
            return "", raw_text

        rest = raw_text[marker.end():]
        maps_match = re.search(r'(?im)^[ \t]*begin_maps\b', rest)
        if maps_match:
            block_end = marker.end() + maps_match.start()
        else:
            block_end = len(raw_text)

        script_block = raw_text[marker.end():block_end]
        if script_block.startswith("\r\n"):
            script_block = script_block[2:]
        elif script_block.startswith("\n") or script_block.startswith("\r"):
            script_block = script_block[1:]
        lines = script_block.splitlines()
        while lines and not lines[-1].strip():
            lines.pop()
        if lines and re.match(r'^\s*;-{5,}\s*$', lines[-1]):
            lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()

        parse_text = raw_text[:marker.start()] + raw_text[block_end:]
        return "\n".join(lines), parse_text

    def extract_level_line_value(self, raw_text, key):
        in_level = False
        key_pattern = re.compile(rf'^\s*{re.escape(key)}\s*=\s*(.*)$', re.IGNORECASE)
        for line in raw_text.splitlines():
            stripped = line.strip()
            lower = stripped.lower()
            if lower == 'begin_level':
                in_level = True
                continue
            if in_level and lower == 'end':
                break
            if not in_level:
                continue
            match = key_pattern.match(line)
            if match:
                return match.group(1).strip()
        return None

    def extract_block_vehicle_comment_names(self, raw_text, block_name):
        names = []
        in_block = False
        current_name = None
        begin_pattern = re.compile(rf'^\s*{re.escape(block_name)}\b', re.IGNORECASE)
        vehicle_pattern = re.compile(r'^\s*vehicle\s*(?:=\s*)?\d+\b.*?;\s*(.*?)\s*$', re.IGNORECASE)

        for line in raw_text.splitlines():
            stripped = line.strip()
            if begin_pattern.match(stripped):
                in_block = True
                current_name = None
                continue
            if in_block and stripped.lower() == 'end':
                names.append(current_name)
                in_block = False
                continue
            if not in_block:
                continue

            match = vehicle_pattern.match(line)
            if match:
                name = match.group(1).strip()
                current_name = name or None

        if in_block:
            names.append(current_name)

        return names

    def extract_tech_comment_names(self, raw_text):
        names = {}
        in_enable = False
        begin_pattern = re.compile(r'^\s*begin_enable\b', re.IGNORECASE)
        entry_pattern = re.compile(r'^\s*(?:vehicle|building)\s*(?:=\s*)?(\d+)\b.*?;\s*(.*?)\s*$', re.IGNORECASE)

        for line in raw_text.splitlines():
            stripped = line.strip()
            if begin_pattern.match(stripped):
                in_enable = True
                continue
            if in_enable and stripped.lower() == 'end':
                in_enable = False
                continue
            if not in_enable:
                continue

            match = entry_pattern.match(line)
            if not match:
                continue
            name = match.group(2).strip()
            if not name:
                continue
            try:
                names[int(match.group(1))] = name
            except:
                pass

        return names

    def open_saved_map_file(self, path):
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showwarning("Open Map", f"Could not open the saved map:\n{e}")

    def confirm_load_with_unsaved_changes(self):
        if not self.has_unsaved_changes():
            return True

        result = messagebox.askyesnocancel(
            "Unsaved changes",
            "Save changes before loading another map?"
        )

        if result is True:
            return self.save_map(ask_open_after_save=False)
        if result is False:
            return True
        return False

    def detect_ldf_set_folder(self, filename):
        try:
            with open(filename, 'r', errors='ignore') as f:
                raw_text = f.read(4096)
        except:
            return None

        set_match = re.search(r'set\s*=\s*(\d+)', raw_text, re.IGNORECASE)
        if not set_match:
            return None

        set_folder = f"set{int(set_match.group(1))}"
        if os.path.exists(resource_path(set_folder)):
            return set_folder
        return None

    def load_map(self):
        if not self.confirm_load_with_unsaved_changes():
            return False

        filename = filedialog.askopenfilename(filetypes=[("LDF maps", "*.ldf"), ("All files", "*.*")])
        if not filename:
            return False
        return self.load_map_from_path(filename, prompt_unsaved=False)

    def load_map_from_path(self, filename, prompt_unsaved=True, show_success=True):
        if prompt_unsaved and not self.confirm_load_with_unsaved_changes():
            return False

        try:
            with open(filename, 'r', errors='ignore') as f: raw_text = f.read()
            loaded_script_content, parse_text = self.split_user_script_block(raw_text)
            raw_title = self.extract_level_line_value(parse_text, 'title_default')
            squad_comment_names = self.extract_block_vehicle_comment_names(parse_text, 'begin_squad')
            host_comment_names = self.extract_block_vehicle_comment_names(parse_text, 'begin_robo')
            tech_comment_names = self.extract_tech_comment_names(parse_text)

            set_match = re.search(r'set\s*=\s*(\d+)', parse_text, re.IGNORECASE)
            if set_match:
                detected_set_num = int(set_match.group(1))
                new_set_folder = f"set{detected_set_num}"
                if new_set_folder != self.set_folder:
                    if os.path.exists(resource_path(new_set_folder)):
                        self.set_folder = new_set_folder
                        self.reload_assets()
                        if show_success:
                            messagebox.showinfo("Set Detected", f"Switched to Set {detected_set_num}")
                    else:
                        messagebox.showwarning("Missing Set", f"Map uses Set {detected_set_num}, but folder not found. Displaying current set assets ({self.set_folder.upper()}).")

            clean_text = re.sub(r';.*', '', parse_text)
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

            if w == 0:
                messagebox.showerror("Error", "Could not determine map size")
                return False
            if h == 0:
                messagebox.showerror("Error", "Could not determine map size")
                return False
            self.mw, self.mh = w, h; self.reset_map(confirm=False, track_history=False)
            self.script_content = loaded_script_content
            self.script_text_widget = None
            self.tech = {i: {'veh': [], 'blg': []} for i in range(1, 8)}
            self.custom_tech_names = {}

            iterator = iter(tokens)
            pushed_tokens = []
            skipped_special_counts = {'gate': 0, 'item': 0, 'gem': 0}
            squad_comment_idx = 0
            host_comment_idx = 0
            grids_loaded = {}
            current_gate = None; current_item = None; current_gem = None; current_squad = None; current_host = None
            current_enable_faction = None
            current_action_context = None

            reading_level = False
            reading_mb = False
            reading_db = False

            def next_token():
                if pushed_tokens:
                    return pushed_tokens.pop()
                return next(iterator)

            def push_token(tok):
                pushed_tokens.append(tok)

            def get_val(itr=None):
                v = next_token(); return next_token() if v == '=' else v

            def read_key_pair():
                try:
                    kx_raw = get_val()
                except StopIteration:
                    return None
                try:
                    kx = int(kx_raw)
                except ValueError:
                    push_token(kx_raw)
                    return None

                try:
                    key_token = next_token()
                except StopIteration:
                    return None
                if key_token.lower() != 'keysec_y':
                    push_token(key_token)
                    return None

                try:
                    ky_raw = get_val()
                except StopIteration:
                    return None
                try:
                    ky = int(ky_raw)
                except ValueError:
                    push_token(ky_raw)
                    return None
                return (kx, ky)

            while True:
                try:
                    token = next_token()
                    token_lower = token.lower()

                    if token_lower == 'begin_squad':
                        custom_name = squad_comment_names[squad_comment_idx] if squad_comment_idx < len(squad_comment_names) else None
                        squad_comment_idx += 1
                        current_squad = {'owner':1, 'veh':1, 'num':1, 'hidden':False, 'custom_name':custom_name, 'x':-1, 'y':-1}

                    elif token_lower == 'begin_robo':
                        custom_name = host_comment_names[host_comment_idx] if host_comment_idx < len(host_comment_names) else None
                        host_comment_idx += 1
                        current_host = {'owner':1, 'veh':56, 'energy':500000, 'pos_y':-330, 'custom_name':custom_name, 'x':-1, 'y':-1, 'hidden':False}

                    elif token_lower == 'begin_level': reading_level = True
                    elif token_lower == 'begin_mbmap': reading_mb = True
                    elif token_lower == 'begin_dbmap': reading_db = True

                    elif token_lower == 'begin_gate':
                        idx = -1
                        for i in range(1, MAX_SPECIAL_SLOTS + 1):
                            if self.gates[i]['x'] == -1: idx = i; break
                        if idx != -1: current_gate = self.gates[idx]; self.visible_gate_slots = max(self.visible_gate_slots, idx)
                        else: skipped_special_counts['gate'] += 1

                    elif token_lower == 'begin_item':
                         idx = -1
                         for i in range(1, MAX_SPECIAL_SLOTS + 1):
                             if self.items[i]['x'] == -1: idx = i; break
                         if idx != -1: current_item = self.items[idx]; self.visible_item_slots = max(self.visible_item_slots, idx)
                         else: skipped_special_counts['item'] += 1

                    elif token_lower == 'begin_gem':
                        idx = -1
                        for i in range(1, MAX_SPECIAL_SLOTS + 1):
                            if self.gems[i]['x'] == -1: idx = i; break
                        if idx != -1:
                            current_gem = self.gems[idx]
                            self.visible_gem_slots = max(self.visible_gem_slots, idx)
                            current_gem['actions'] = []
                            current_action_context = None
                        else:
                            skipped_special_counts['gem'] += 1

                    elif token_lower == 'begin_enable':
                        try:
                            faction_id = int(next_token())
                            current_enable_faction = faction_id if faction_id in self.tech else None
                        except:
                            current_enable_faction = None

                    elif current_enable_faction is not None:
                        if token_lower == 'end':
                            current_enable_faction = None
                        elif token_lower == 'vehicle':
                            veh_id = int(get_val(iterator))
                            if veh_id not in self.tech[current_enable_faction]['veh']:
                                self.tech[current_enable_faction]['veh'].append(veh_id)
                        elif token_lower == 'building':
                            building_id = int(get_val(iterator))
                            if building_id not in self.tech[current_enable_faction]['blg']:
                                self.tech[current_enable_faction]['blg'].append(building_id)

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
                        elif token_lower == 'mb_status':
                            val = get_val(iterator)
                            if val.lower() == 'unknown': current_gem['hidden'] = True

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
                         elif token_lower == 'mb_status':
                             val = get_val(iterator)
                             if val.lower() == 'unknown': current_gate['hidden'] = True
                         elif token_lower == 'keysec_x':
                             key_pair = read_key_pair()
                             if key_pair:
                                 current_gate['keys'].append(key_pair)

                    elif current_item:
                         if token_lower == 'sec_x': current_item['x'] = int(get_val(iterator))
                         elif token_lower == 'sec_y': current_item['y'] = int(get_val(iterator))
                         elif token_lower == 'type': current_item['type'] = int(get_val(iterator))
                         elif token_lower == 'inactive_bp': current_item['inactive_bp'] = int(get_val(iterator))
                         elif token_lower == 'active_bp': current_item['active_bp'] = int(get_val(iterator))
                         elif token_lower == 'trigger_bp': current_item['trigger_bp'] = int(get_val(iterator))
                         elif token_lower == 'countdown': current_item['countdown'] = int(get_val(iterator))
                         elif token_lower == 'mb_status':
                             val = get_val(iterator)
                             if val.lower() == 'unknown': current_item['hidden'] = True
                         elif token_lower == 'keysec_x':
                             key_pair = read_key_pair()
                             if key_pair:
                                 current_item['keys'].append(key_pair)

                    elif token_lower in ['typ_map', 'own_map', 'hgt_map', 'blg_map']:
                        key_map = token_lower; v1 = next_token()
                        if v1 == '=': v1 = next_token()
                        next_token()
                        data_tokens = []
                        target_count = w * h
                        for _ in range(target_count): data_tokens.append(next_token())
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
            if raw_title is not None:
                self.lvl_info['title'] = raw_title
            self.custom_tech_names.update(tech_comment_names)
            self.clear_history()
            self._suppress_script_sync = True
            try:
                self.set_mode("TYPE")
            finally:
                self._suppress_script_sync = False
            self.refresh_squad_list(); self.refresh_host_list()
            self.current_filename = os.path.basename(filename)
            self.current_filepath = os.path.abspath(filename)
            self.update_window_title()
            self.mark_saved_state()
            skipped_total = sum(skipped_special_counts.values())
            if skipped_total:
                messagebox.showwarning(
                    "Special Object Limit",
                    "Some special objects were skipped because the map exceeds the current limit:\n\n"
                    f"Beamgates: {skipped_special_counts['gate']}\n"
                    f"Bombs/Items: {skipped_special_counts['item']}\n"
                    f"Gems: {skipped_special_counts['gem']}"
                )
            if show_success:
                messagebox.showinfo("Success", f"Map Loaded: {w}x{h}")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {str(e)}")
            return False

    def on_close(self):
        if not self.has_unsaved_changes():
            self.root.destroy()
            return

        result = messagebox.askyesnocancel(
            "Unsaved changes",
            "Save changes before exiting?"
        )

        if result is True:
            if self.save_map(ask_open_after_save=False):
                self.root.destroy()
        elif result is False:
            self.root.destroy()

    def save_map(self, ask_open_after_save=True):
        if hasattr(self, 'sync_script_widget_to_data'):
            self.sync_script_widget_to_data(push_undo=True)

        initialfile = self.current_filename or "l0101.ldf"
        f = filedialog.asksaveasfile(mode='w', defaultextension=".ldf", initialfile=initialfile)
        if not f:
            return False

        saved_path = f.name

        try:
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
                    w(f"   closed_bp = {g['closed_bp']}"); w(f"   opened_bp = {g['opened_bp']}")
                    if g.get('hidden', False): w("   mb_status = unknown")
                    for kx, ky in g['keys']: w(f"   keysec_x = {kx}\n   keysec_y = {ky}")
                    w("end"); w(";------------------------------------------------------------")
            for i in range(1, self.visible_item_slots + 1):
                it = self.items[i]
                if it['x'] != -1:
                    w("begin_item"); w(f"   sec_x = {it['x']}\n   sec_y = {it['y']}"); w(f"   inactive_bp = {it['inactive_bp']}"); w(f"   active_bp = {it['active_bp']}")
                    w(f"   trigger_bp = {it['trigger_bp']}"); w(f"   type = {it['type']}"); w(f"   countdown = {it['countdown']}")
                    if it.get('hidden', False): w("   mb_status = unknown")
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
                    if gm.get('hidden', False): w("   mb_status = unknown")
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

            w("end")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}")
            return False
        finally:
            try:
                f.close()
            except:
                pass

        self.current_filename = os.path.basename(saved_path)
        self.current_filepath = os.path.abspath(saved_path)
        self.update_window_title()
        self.mark_saved_state()

        if ask_open_after_save and messagebox.askyesno("Saved", f"Map saved to:\n{saved_path}\n\nDo you want to view the map now?"):
            self.open_saved_map_file(saved_path)
        return True

    def reset_map(self, confirm=True, track_history=True):
        if confirm and not messagebox.askyesno("RESET", "Wipe map?"): return
        if track_history:
            self.push_undo_snapshot()
        self.grids = { 'type': [['00'] * self.mw for _ in range(self.mh)], 'own': [[0] * self.mw for _ in range(self.mh)], 'hgt': [[DEFAULT_HGT] * self.mw for _ in range(self.mh)], 'blg': [['00'] * self.mw for _ in range(self.mh)] }
        self.apply_borders()
        self.gates = {i: {'active': False, 'x': -1, 'y': -1, 'keys': [], 'target': 0, 'closed_bp': 25, 'opened_bp': 26, 'hidden': False} for i in range(1, MAX_SPECIAL_SLOTS + 1)}
        self.items = {i: {'active': False, 'x': -1, 'y': -1, 'keys': [], 'countdown': 300000, 'inactive_bp': 35, 'active_bp': 36, 'trigger_bp': 37, 'type': 1, 'hidden': False} for i in range(1, MAX_SPECIAL_SLOTS + 1)}
        self.gems = {i: {'x': -1, 'y': -1, 'blg': 50, 'type': 3, 'actions': [], 'hidden': False} for i in range(1, MAX_SPECIAL_SLOTS + 1)}
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
            changed = False
            for r in range(self.mh):
                for c in range(self.mw):
                    if not (r == 0 or r == self.mh - 1 or c == 0 or c == self.mw - 1):
                        if self.mode == "TYPE":
                            if self.grids['type'][r][c] != self.sel['type']:
                                if not changed:
                                    self.push_undo_snapshot()
                                    changed = True
                                self.grids['type'][r][c] = self.sel['type']
                        elif self.mode == "OWN":
                            if self.grids['own'][r][c] != self.sel['own']:
                                if not changed:
                                    self.push_undo_snapshot()
                                    changed = True
                                self.grids['own'][r][c] = self.sel['own']
                        elif self.mode == "HGT":
                            if self.grids['hgt'][r][c] != self.sel['hgt']:
                                if not changed:
                                    self.push_undo_snapshot()
                                    changed = True
                                self.grids['hgt'][r][c] = self.sel['hgt']
                        elif self.mode == "BLG":
                            if self.grids['blg'][r][c] != self.sel['blg']:
                                if not changed:
                                    self.push_undo_snapshot()
                                    changed = True
                                self.grids['blg'][r][c] = self.sel['blg']
            if changed:
                self.draw_grid()
