import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import copy
import re
import platform
import subprocess

from sektor_constants import *
from sektor_paths import resource_path

class DialogMixin:

    def ask_integer_modal(self, title, prompt, **kwargs):
        owner = tk.Toplevel(self.root)
        owner.withdraw()
        owner.transient(self.root)
        owner.attributes("-topmost", True)
        owner.grab_set()
        owner.lift()
        owner.focus_force()
        owner.update_idletasks()
        try:
            return simpledialog.askinteger(title, prompt, parent=owner, **kwargs)
        finally:
            try:
                owner.grab_release()
            except:
                pass
            owner.destroy()
            self.root.lift()

    def ask_set(self):
        n = self.ask_integer_modal(APP_NAME, "Select Set (1-6):", minvalue=1, maxvalue=6, initialvalue=1)
        return f"set{n}" if n else None

    def ask_map_dimensions(self, default_w=DEFAULT_W, default_h=DEFAULT_H):
        w = self.ask_integer_modal(APP_NAME, "W:", initialvalue=default_w, minvalue=3)
        if w is None:
            return None
        h = self.ask_integer_modal(APP_NAME, "H:", initialvalue=default_h, minvalue=3)
        if h is None:
            return None
        return w, h

    def ask_dims(self):
        dims = self.ask_map_dimensions(DEFAULT_W, DEFAULT_H)
        if dims:
            w, h = dims
            self.mw, self.mh = w, h
            self.reset_map(False, track_history=False)
            self.clear_history()
<<<<<<< HEAD
            self.mark_saved_state()
=======
<<<<<<< HEAD
=======
            self.mark_saved_state()
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
>>>>>>> 960ab1aa40a49cce6e2d2ab9956235aab9074263
        else:
            self.root.destroy()

    def create_new_map(self, set_folder, width, height):
        if not os.path.exists(resource_path(set_folder)):
            messagebox.showerror("Missing Set", f"Folder not found: {set_folder}")
            return

        set_changed = (set_folder != self.set_folder)
        self.set_folder = set_folder
        if set_changed:
            self.reload_assets()
        else:
            self.update_window_title()

        self.current_filename = None
        self.update_window_title()

        self.mw, self.mh = width, height
        self.zoom_m = 64
        self.clear_view = False

        self.lvl_info = {
            'title': "Untitled Map",
            'sky': "objects/x7.bas",
            'mbmap': "MB_53.IFF",
            'dbmap': "DB_53.IFF",
            'music': "None",
            'movie': "None"
        }
        self.script_content = ""
        self.tech = {i: {'veh': [], 'blg': []} for i in range(1, 8)}
        self.custom_tech_names = {}
        self.curr_tech_faction = 1

        self.current_gate_slot = 1
        self.current_item_slot = 1
        self.current_gem_slot = 1
        self.current_squad_index = -1
        self.current_host_index = -1
        self._drag_squad_idx = -1
        self._drag_host_idx = -1

        self.current_squad_data = {'owner': 1, 'veh': 1, 'num': 1, 'hidden': False, 'custom_name': None}
        self.current_host_data = {'owner': 1, 'veh': 56, 'energy': 500000, 'pos_y': -330, 'custom_name': None, 'hidden': False}

        self.reset_map(confirm=False, track_history=False)
        self.clear_history()
<<<<<<< HEAD
        self.mark_saved_state()
=======
<<<<<<< HEAD
=======
        self.mark_saved_state()
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
>>>>>>> 960ab1aa40a49cce6e2d2ab9956235aab9074263
        self.set_mode("TYPE")
        self.refresh_palette_layout(force_full=True)
        self.refresh_map_layout(force_full=True)

    def new_map_dialog(self):
        set_folder = self.ask_set()
        if not set_folder:
            return
        dims = self.ask_map_dimensions(DEFAULT_W, DEFAULT_H)
        if not dims:
            return
        w, h = dims
        self.create_new_map(set_folder, w, h)

    def resize_map_dialog(self):
        w = self.ask_integer_modal("Resize Map", "New Width:", initialvalue=self.mw, minvalue=3)
        h = self.ask_integer_modal("Resize Map", "New Height:", initialvalue=self.mh, minvalue=3)
        
        if w and h:
            if w == self.mw and h == self.mh:
                return
            self.push_undo_snapshot()
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
        cv_s = tk.Canvas(fr_sky, bg="#111", highlightthickness=0); sb_s = tk.Scrollbar(
            fr_sky,
            command=cv_s.yview,
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
                        path = resource_path(os.path.join("skies", f))
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
            new_sky = f"objects/{name}.bas"
            if self.lvl_info['sky'] != new_sky:
                self.push_undo_snapshot()
                self.lvl_info['sky'] = new_sky
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
            new_title = e_title.get()
            new_mbmap = e_mb.get().strip() or "MB_53.IFF"
            new_dbmap = e_db.get().strip() or "DB_53.IFF"
            new_music = cb_music.get()
            
            raw_movie = cb_movie.get().strip()
            if raw_movie == "None" or raw_movie == "":
                new_movie = "None"
            else:
                if not raw_movie.lower().startswith("mov/") and not raw_movie.lower().startswith("mov:"):
                     new_movie = f"mov/{raw_movie}"
                else:
                     new_movie = raw_movie.replace(":", "/")

            changed = (
                self.lvl_info['title'] != new_title or
                self.lvl_info.get('mbmap') != new_mbmap or
                self.lvl_info.get('dbmap') != new_dbmap or
                self.lvl_info.get('music') != new_music or
                self.lvl_info.get('movie') != new_movie
            )
            if changed:
                self.push_undo_snapshot()
                self.lvl_info['title'] = new_title
                self.lvl_info['mbmap'] = new_mbmap
                self.lvl_info['dbmap'] = new_dbmap
                self.lvl_info['music'] = new_music
                self.lvl_info['movie'] = new_movie

            win.destroy(); messagebox.showinfo("Success", "Level Info Updated!")
        
        tk.Button(win, text="CONFIRM", command=save, bg="#008800", fg="white", width=20).pack(pady=15)
