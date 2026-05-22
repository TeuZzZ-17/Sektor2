import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import copy
import re
import platform
import subprocess

from sektor_constants import *

class CanvasMixin:
<<<<<<< HEAD
=======
    MAP_BORDER_TAG = "map_outer_border"
    MAP_BORDER_COLOR = "#00FFFF"
    HOVER_TAG = "map_hover_overlay"
    HOVER_COLOR = "#B8F4FF"
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)

    OWNER_PANEL_LABELS = {
        0: "Neutral",
        1: "Resistance",
        2: "Sulgogar",
        3: "Mykonian",
        4: "Taerkasten",
        5: "Black Sect",
        6: "Ghorkov",
        7: "Drones",
    }

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

    def get_cell_label_font(self, size):
        if not hasattr(self, "_cell_label_fonts"):
            self._cell_label_fonts = {}
        size = int(size)
        if size not in self._cell_label_fonts:
            self._cell_label_fonts[size] = tkfont.Font(family="Arial", size=size, weight="bold")
        return self._cell_label_fonts[size]

    def fit_label_text(self, text, sz, min_font=7, max_font=None, padding=12):
        text = str(text)
        min_font = int(min_font)
        max_font = int(max_font if max_font is not None else max(7, sz // 8))
        max_font = max(min_font, max_font)
        max_width = max(1, int(sz - padding))

        for font_size in range(max_font, min_font - 1, -1):
            label_font = self.get_cell_label_font(font_size)
            text_width = label_font.measure(text)
            if text_width <= max_width:
                return text, font_size, text_width

        label_font = self.get_cell_label_font(min_font)
        ellipsis = "..."
        if label_font.measure(ellipsis) > max_width:
            final_text = ellipsis
            while final_text and label_font.measure(final_text) > max_width:
                final_text = final_text[:-1]
            return final_text, min_font, label_font.measure(final_text)

        base = text
        while base and label_font.measure(base.rstrip() + ellipsis) > max_width:
            base = base[:-1]
        final_text = (base.rstrip() + ellipsis) if base.strip() else ellipsis
        while final_text and label_font.measure(final_text) > max_width:
            final_text = final_text[:-1]
        return final_text, min_font, label_font.measure(final_text)

<<<<<<< HEAD
=======
    def fit_cell_multiline_text(self, text, sz, min_font=4, max_font=None, padding=8):
        lines = str(text).splitlines() or [str(text)]
        min_font = int(min_font)
        max_font = int(max_font if max_font is not None else max(8, sz // 4))
        max_font = max(min_font, max_font)
        max_width = max(1, int(sz - padding))
        max_height = max(1, int(sz - padding))

        for font_size in range(max_font, min_font - 1, -1):
            label_font = self.get_cell_label_font(font_size)
            line_height = label_font.metrics("linespace")
            text_height = line_height * len(lines)
            widest_line = max(label_font.measure(line) for line in lines)
            if widest_line <= max_width and text_height <= max_height:
                return "\n".join(lines), label_font

        label_font = self.get_cell_label_font(min_font)
        if label_font.metrics("linespace") * len(lines) > max_height:
            return "", label_font

        fitted_lines = []
        for line in lines:
            fitted_line, _, _ = self.fit_label_text(line, sz, min_font=min_font, max_font=min_font, padding=padding)
            fitted_lines.append(fitted_line)
        return "\n".join(fitted_lines), label_font

>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
    def draw_cell_label(self, x, y, sz, text, fill_color, text_color, tag, position="bottom"):
        label_text, font_size, text_width = self.fit_label_text(text, sz)
        label_font = self.get_cell_label_font(font_size)

        cell_margin = 2
        pad_x = 4
        max_plate_w = max(1, sz - (cell_margin * 2))
        plate_w = min(max_plate_w, max(1, text_width + (pad_x * 2)))
        cx = x + sz // 2
        x1 = max(x + cell_margin, cx - (plate_w // 2))
        x2 = min(x + sz - cell_margin, x1 + plate_w)
        x1 = max(x + cell_margin, x2 - plate_w)

        plate_h = min(max(1, sz - (cell_margin * 2)), label_font.metrics("linespace") + 4)
        if position == "top":
            y1 = y + cell_margin
            y2 = min(y + sz - cell_margin, y1 + plate_h)
        else:
            y2 = y + sz - cell_margin
            y1 = max(y + cell_margin, y2 - plate_h)
        self.cv_map.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="black", tags=tag)
        self.cv_map.create_text(cx, (y1 + y2) // 2, text=label_text, fill=text_color, font=label_font, tags=tag)

    def draw_building_overlays(self, x, y, sz, bid, tag, canvas=None, palette=False):
        overlays = getattr(self, "building_overlays", {}).get(str(bid).lower(), [])
        if not overlays:
            return
        if canvas is None:
            canvas = self.cv_map

        if palette:
            icons = overlays[:4]
        else:
            icons = [icon for icon in overlays if icon not in PALETTE_ONLY_BUILDING_OVERLAYS][:4]
        if not icons:
            return
        count = len(icons)
        if count <= 2:
            icon_sz = max(8, min(sz - 8, int(sz * 0.34)))
        else:
            icon_sz = max(7, min((sz - 10) // 2, int(sz * 0.30)))
        if icon_sz <= 0:
            return

        gap = max(2, sz // 18)
        cx = x + sz // 2
        cy = y + sz // 2
        positions = []

        if count == 1:
            positions = [(cx - icon_sz // 2, cy - icon_sz // 2)]
        elif count == 2:
            group_w = (icon_sz * 2) + gap
            left = cx - group_w // 2
            top = cy - icon_sz // 2
            positions = [(left, top), (left + icon_sz + gap, top)]
        else:
            group_w = (icon_sz * 2) + gap
            group_h = (icon_sz * 2) + gap
            left = cx - group_w // 2
            top = cy - group_h // 2
            positions = [
                (left, top),
                (left + icon_sz + gap, top),
                (left + (group_w - icon_sz) // 2, top + icon_sz + gap),
            ]
            if count >= 4:
                positions[2] = (left, top + icon_sz + gap)
                positions.append((left + icon_sz + gap, top + icon_sz + gap))

        for icon_name, (ix, iy) in zip(icons, positions):
            img = self.get_img('building_overlay', icon_name, icon_sz)
            if img:
                ix = max(x + 2, min(x + sz - icon_sz - 2, ix))
                iy = max(y + 2, min(y + sz - icon_sz - 2, iy))
                canvas.create_image(ix, iy, image=img, anchor=tk.NW, tags=tag)

    def draw_building_markers(self, x, y, sz, tag):
        inset = max(3, sz // 16)
        max_segment_len = max(2, sz - (inset * 2))
        segment_len = min(max(8, sz // 3), max_segment_len)
        half_len = segment_len // 2
        width = 3 if sz >= 48 else 2
        cx = x + sz // 2
        cy = y + sz // 2

        left = max(x + inset, cx - half_len)
        right = min(x + sz - inset, cx + half_len)
        top = max(y + inset, cy - half_len)
        bottom = min(y + sz - inset, cy + half_len)

        self.cv_map.create_line(left, y + inset, right, y + inset, fill=MARKER_COLOR, width=width, tags=tag)
        self.cv_map.create_line(left, y + sz - inset, right, y + sz - inset, fill=MARKER_COLOR, width=width, tags=tag)
        self.cv_map.create_line(x + inset, top, x + inset, bottom, fill=MARKER_COLOR, width=width, tags=tag)
        self.cv_map.create_line(x + sz - inset, top, x + sz - inset, bottom, fill=MARKER_COLOR, width=width, tags=tag)

    def get_editor_height_value(self, r, c):
        try:
            return int(self.grids['hgt'][r][c]) - HGT_MIN
        except Exception:
            return 30

    def draw_text_with_outline(self, canvas, x, y, text, fill, font, tag, anchor=tk.NW, outline="#000000", width=1):
        offsets = []
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                if dx == 0 and dy == 0:
                    continue
                if abs(dx) == width or abs(dy) == width:
                    offsets.append((dx, dy))

        for dx, dy in offsets:
            canvas.create_text(x + dx, y + dy, text=text, fill=outline, font=font, anchor=anchor, tags=tag)
        canvas.create_text(x, y, text=text, fill=fill, font=font, anchor=anchor, tags=tag)

    def draw_cell_outline(self, x, y, sz, tag, color="white", width=3, inset=2):
        self.cv_map.create_rectangle(
            x + inset,
            y + inset,
            x + sz - inset,
            y + sz - inset,
            outline=color,
            width=width,
            tags=tag
        )

<<<<<<< HEAD
=======
    def clear_hover_overlay(self, event=None):
        if hasattr(self, 'cv_map'):
            self.cv_map.delete(self.HOVER_TAG)
        self.hover_cell = None

    def draw_hover_overlay(self, col, row):
        if not hasattr(self, 'cv_map'):
            return
        self.cv_map.delete(self.HOVER_TAG)

        sz = self.zoom_m
        x = col * sz
        y = row * sz
        inset = max(3, min(6, sz // 8))
        self.cv_map.create_rectangle(
            x + inset,
            y + inset,
            x + sz - inset,
            y + sz - inset,
            outline=self.HOVER_COLOR,
            width=1,
            dash=(3, 2),
            tags=self.HOVER_TAG
        )
        self.cv_map.tag_raise(self.MAP_BORDER_TAG)

    def update_hover_from_event(self, event):
        if self._map_panning:
            self.clear_hover_overlay()
            return

        col = int(self.cv_map.canvasx(event.x) // self.zoom_m)
        row = int(self.cv_map.canvasy(event.y) // self.zoom_m)
        if not (0 <= col < self.mw and 0 <= row < self.mh):
            self.clear_hover_overlay()
            return

        hover_cell = (col, row)
        if hover_cell == getattr(self, "hover_cell", None):
            self.cv_map.tag_raise(self.HOVER_TAG)
            return

        self.hover_cell = hover_cell
        self.draw_hover_overlay(col, row)

    def draw_map_outer_border(self):
        if not hasattr(self, 'cv_map'):
            return

        self.cv_map.delete(self.MAP_BORDER_TAG)

        sz = getattr(self, 'zoom_m', 0)
        rows = getattr(self, 'mh', 0)
        cols = getattr(self, 'mw', 0)
        if sz <= 0 or rows <= 0 or cols <= 0:
            return

        width = 2 if sz >= 32 else 1
        inset = max(1, width // 2)
        self.cv_map.create_rectangle(
            inset,
            inset,
            (cols * sz) - inset,
            (rows * sz) - inset,
            outline=self.MAP_BORDER_COLOR,
            width=width,
            tags=self.MAP_BORDER_TAG
        )
        self.cv_map.tag_raise(self.HOVER_TAG)
        self.cv_map.tag_raise(self.MAP_BORDER_TAG)

>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
    def draw_special_icon(self, x, y, sz, tag, icon_key):
        img = self.get_img('special', icon_key, sz)
        if img:
            self.cv_map.create_image(x, y, image=img, anchor=tk.NW, tags=tag)

<<<<<<< HEAD
=======
    def get_unknown_id_label(self, cat, hex_id):
        try:
            val_int = int(hex_id, 16)
            return self.custom_definitions[cat].get(val_int, "GHOST")
        except:
            return "GHOST"

    def get_height_tint_color(self, editor_height, base_color):
        if editor_height > EDITOR_HEIGHT_BASE:
            return HEIGHT_HIGH_COLOR
        if editor_height < EDITOR_HEIGHT_BASE:
            return HEIGHT_LOW_COLOR
        return base_color

>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
    def draw_height_overlay(self, x, y, sz, editor_height, tag):
        delta = editor_height - EDITOR_HEIGHT_BASE
        visual_delta = max(-15, min(15, delta))
        center_y = y + (sz // 2)
        fill_h = int((abs(visual_delta) / 15.0) * (sz / 2))

<<<<<<< HEAD
        self.cv_map.create_rectangle(x, y, x + sz, y + sz, fill="#000000", outline="", stipple="gray12", tags=tag)
=======
        self.cv_map.create_rectangle(x, y, x + sz, y + sz, fill="#202020", outline="", stipple="gray12", tags=tag)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)

        if visual_delta > 0 and fill_h > 0:
            self.cv_map.create_rectangle(
                x, center_y - fill_h, x + sz, center_y,
                fill=HEIGHT_HIGH_COLOR, outline="", stipple="gray50", tags=tag
            )
        elif visual_delta < 0 and fill_h > 0:
            self.cv_map.create_rectangle(
                x, center_y, x + sz, center_y + fill_h,
                fill=HEIGHT_LOW_COLOR, outline="", stipple="gray50", tags=tag
            )

<<<<<<< HEAD
        line_w = max(1, sz // 28)
        self.cv_map.create_line(
            x + 2, center_y, x + sz - 2, center_y,
            fill="#FFFFFF", width=line_w, tags=tag
        )

=======
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
    def draw_height_number(self, x, y, sz, editor_height, tag):
        text = str(editor_height)
        if self.mode == "HGT":
            font = ("Arial", max(6, sz // 8), "bold")
<<<<<<< HEAD
=======
            text_color = self.get_height_tint_color(editor_height, "#FFFFFF")
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
            self.cv_map.create_text(
                x + 3,
                y + 2,
                text=text,
<<<<<<< HEAD
                fill="#FF0000",
=======
                fill=text_color,
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
                font=font,
                anchor=tk.NW,
                tags=tag
            )
        elif sz >= 32:
            font = ("Arial", max(6, sz // 8), "bold")
            self.draw_text_with_outline(
                self.cv_map,
                x + 3,
                y + 2,
                text,
                "#68C7CC",
                font,
                tag,
                outline="#101010",
                width=1
            )

<<<<<<< HEAD
    def draw_cell(self, c, r):
        sz = self.zoom_m; x, y = c*sz, r*sz; tag = f"c_{c}_{r}"
        self.cv_map.delete(tag)
=======
    def draw_cell(self, c, r, refresh_border=True):
        sz = self.zoom_m; x, y = c*sz, r*sz; tag = f"c_{c}_{r}"
        self.cv_map.delete(tag)
        if refresh_border:
            self.cv_map.delete(self.MAP_BORDER_TAG)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)

        # RULER LOGIC
        if r == 0 or r == self.mh - 1 or c == 0 or c == self.mw - 1:
            self.cv_map.create_rectangle(x, y, x + sz, y + sz, fill="#151515", outline="#404040", tags=tag)
            self.draw_height_number(x, y, sz, self.get_editor_height_value(r, c), tag)
            
            txt = ""
            if (r == 0 or r == self.mh - 1) and (0 < c < self.mw - 1): txt = str(c)
            elif (c == 0 or c == self.mw - 1) and (0 < r < self.mh - 1): txt = str(r)
            if txt: self.cv_map.create_text(x + sz//2, y + sz//2, text=txt, fill="#00FFFF", font=("Arial", max(8, sz//3), "bold"), tags=tag)
<<<<<<< HEAD
=======
            if refresh_border:
                self.draw_map_outer_border()
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
            return

        # --- STANDARD MAP RENDERING (BASE LAYER) ---
        tid = self.grids['type'][r][c]
        
        # 1. Background Fill (Always standard dark grid to allow transparency)
        self.cv_map.create_rectangle(x,y,x+sz,y+sz, fill="#202020", outline="", tags=tag)

        # 2. Sector Image
        img = self.get_img('type', tid, sz)
        if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)

        if self.clear_view and self.mode == "HGT":
            self.cv_map.create_rectangle(x,y,x+sz,y+sz, outline=GRID_COLOR, tags=tag)
<<<<<<< HEAD
=======
            if refresh_border:
                self.draw_map_outer_border()
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
            return

        if self.mode == "HGT":
            editor_height = self.get_editor_height_value(r, c)
            self.draw_height_overlay(x, y, sz, editor_height, tag)
            self.cv_map.create_rectangle(x, y, x+sz, y+sz, outline="#3A3A3A", width=1, tags=tag)
            self.draw_height_number(x, y, sz, editor_height, tag)
<<<<<<< HEAD
=======
            if refresh_border:
                self.draw_map_outer_border()
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
            return

        # 3. Custom Sector Outline & Logic (Transparent center)
        is_custom_sector = tid not in self.lists['type']
        if is_custom_sector:
            # Only Red Border, no fill (Transparent)
            self.cv_map.create_rectangle(x,y,x+sz,y+sz, outline=CUSTOM_BORDER_COLOR, width=2, tags=tag)

<<<<<<< HEAD
        if self.clear_view: self.cv_map.create_rectangle(x,y,x+sz,y+sz, outline=GRID_COLOR, tags=tag); return
=======
        if self.clear_view:
            self.cv_map.create_rectangle(x,y,x+sz,y+sz, outline=GRID_COLOR, tags=tag)
            if refresh_border:
                self.draw_map_outer_border()
            return
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)

        # 4. Building Layer
        bid = self.grids['blg'][r][c]
        is_custom_building = (bid != '00' and bid not in self.lists['blg'])

        if bid!='00':
            img = self.get_img('blg', bid, sz)
            if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
            
            if is_custom_building:
                 self.cv_map.create_rectangle(x+1,y+1,x+sz-1,y+sz-1, outline=CUSTOM_BORDER_COLOR, width=3, tags=tag)
            self.draw_building_overlays(x, y, sz, bid, tag)

<<<<<<< HEAD
        # --- MOD: TEXT RENDERING PRIORITY & COLOR UNIFICATION ---
=======
        # --- TEXT RENDERING PRIORITY & COLOR UNIFICATION ---
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        # Rule: Show Building Text if present. Else Show Sector Text if present.
        # Color: Yellow (#FFFF00) for both.
        # Format: ID \n Name
        
        text_to_draw = None
        
        if is_custom_building:
<<<<<<< HEAD
            try:
                 val_int = int(bid, 16)
                 name = self.custom_definitions['blg'].get(val_int, "MOD")
            except: name = "MOD"
=======
            name = self.get_unknown_id_label('blg', bid)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
            text_to_draw = f"{bid}\n{name}"
            
        elif is_custom_sector:
            # Only draw sector text if building text is NOT drawn
<<<<<<< HEAD
            try:
                val_int = int(tid, 16)
                name = self.custom_definitions['type'].get(val_int, "MOD")
            except: name = "MOD"
            text_to_draw = f"{tid}\n{name}"

        if text_to_draw:
             f_size = max(8, sz // 4)
             self.cv_map.create_text(x+sz//2, y+sz//2, text=text_to_draw, fill="#FFFF00", font=("Arial", int(f_size), "bold"), justify=tk.CENTER, tags=tag)
=======
            name = self.get_unknown_id_label('type', tid)
            text_to_draw = f"{tid}\n{name}"

        if text_to_draw:
             label_text, label_font = self.fit_cell_multiline_text(text_to_draw, sz)
             if label_text:
                 self.cv_map.create_text(x+sz//2, y+sz//2, text=label_text, fill="#FFFF00", font=label_font, justify=tk.CENTER, tags=tag)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)


        # --- GLOW LOGIC ---
        glow_width = 3

        # BEAMGATES
        for i in range(1, self.visible_gate_slots + 1):
            g = self.gates[i]
            if g['x'] == c and g['y'] == r:
                self.draw_special_icon(x, y, sz, tag, 'gate')
                if self.mode == "GATE" and i == self.current_gate_slot:
                     self.draw_cell_outline(x, y, sz, tag, width=glow_width, inset=2)

            if (c,r) in g['keys']:
                self.draw_special_icon(x, y, sz, tag, 'key')
                if self.mode == "GATE" and i == self.current_gate_slot:
                     self.draw_cell_outline(x, y, sz, tag, width=glow_width, inset=2)

        # BOMBS
        for i in range(1, self.visible_item_slots + 1):
            it = self.items[i]
            if it['x'] == c and it['y'] == r:
                self.draw_special_icon(x, y, sz, tag, 'item')
                if self.mode == "ITEM" and i == self.current_item_slot:
                     self.draw_cell_outline(x, y, sz, tag, width=glow_width, inset=2)

            if (c,r) in it['keys']:
                self.draw_special_icon(x, y, sz, tag, 'item_key')
                if self.mode == "ITEM" and i == self.current_item_slot:
                     self.draw_cell_outline(x, y, sz, tag, width=glow_width, inset=2)

        # GEMS
        for i in range(1, self.visible_gem_slots + 1):
            gm = self.gems[i]
            if gm['x'] == c and gm['y'] == r:
                self.draw_special_icon(x, y, sz, tag, 'gem')
                if self.mode == "GEM" and i == self.current_gem_slot:
                     self.draw_cell_outline(x, y, sz, tag, width=glow_width, inset=2)

        fid = self.grids['own'][r][c]
        if fid != 0:
            f_col = FACTIONS.get(fid, (None, None))[1]
            if f_col:
                owner_inset = 1
                owner_width = 1
                self.cv_map.create_rectangle(
                    x + owner_inset, y + owner_inset,
                    x + sz - owner_inset, y + sz - owner_inset,
                    outline=f_col, width=owner_width, tags=tag
                )

        if bid != '00' and not is_custom_building:
            self.draw_building_markers(x, y, sz, tag)

        # HOST STATIONS
        hosts_here = [(i, h) for i, h in enumerate(self.host_stations) if h['x'] == c and h['y'] == r]
        if hosts_here:
            i, h = hosts_here[-1]
            f_col = FACTIONS[h['owner']][1] if FACTIONS[h['owner']][1] else "#FFF"
            self.cv_map.create_rectangle(x+2, y+2, x+sz-2, y+sz-2, outline=f_col, width=3, tags=tag)
            img = self.get_img('host', h['veh'], sz)
            if img: self.cv_map.create_image(x,y,image=img, anchor=tk.NW, tags=tag)
            vname = h['custom_name']
            if not vname: vname = self.defs['host'].get(h['veh'], "Unknown")
            txt_col = "black" if h['owner'] in [2,3,4] else "white"
            squads_here = [(i, s) for i, s in enumerate(self.squads) if s['x'] == c and s['y'] == r]
            host_label_position = "top" if squads_here else "bottom"
            self.draw_cell_label(x, y, sz, vname, f_col, txt_col, tag, position=host_label_position)
            if self.mode == "HOST" and i == self.current_host_index:
                 self.draw_cell_outline(x, y, sz, tag, width=2, inset=1)

        # SQUADS
        squads_here = [(i, s) for i, s in enumerate(self.squads) if s['x'] == c and s['y'] == r]
        if squads_here:
            i, s = squads_here[-1]
            vname = s['custom_name']
            if not vname: vname = self.defs['veh'].get(s['veh'], "Unknown")
            vname = f"{s.get('num', 1)} {vname}"
            col = FACTIONS[s['owner']][1] if FACTIONS[s['owner']][1] else "#FFF"
            txt_col = "black" if s['owner'] in [2,3,4] else "white"
            self.draw_cell_label(x, y, sz, vname, col, txt_col, tag)
            if self.mode == "SQUAD" and i == self.current_squad_index:
                 self.draw_cell_outline(x, y, sz, tag, width=3, inset=1)

        self.cv_map.create_rectangle(x,y,x+sz,y+sz, outline=GRID_COLOR, tags=tag)
        self.draw_height_number(x, y, sz, self.get_editor_height_value(r, c), tag)
<<<<<<< HEAD
=======
        if refresh_border:
            self.draw_map_outer_border()
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)

    def draw_grid(self):
        if not hasattr(self, 'cv_map'): return
        self.cv_map.delete("all")
<<<<<<< HEAD
        rows = getattr(self, 'mh', DEFAULT_H)
        cols = getattr(self, 'mw', DEFAULT_W)
        for r in range(rows):
            for c in range(cols): self.draw_cell(c, r)
=======
        self.hover_cell = None
        rows = getattr(self, 'mh', DEFAULT_H)
        cols = getattr(self, 'mw', DEFAULT_W)
        for r in range(rows):
            for c in range(cols): self.draw_cell(c, r, refresh_border=False)
        self.draw_map_outer_border()
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        self.cv_map.config(scrollregion=(0,0,self.mw*self.zoom_m, self.mh*self.zoom_m))

    def draw_palette(self, e=None):
        if self.mode in ["HGT", "GATE", "ITEM", "TECH", "GEM", "SCRIPT", "SQUAD", "HOST"]: return

        previous_y = 0.0
        try:
            previous_y = self.cv_pal.yview()[0]
        except:
            pass

        self.cv_pal.delete("all")
        w = self.cv_pal.winfo_width() or 300
        sz = self.zoom_p
        if self.mode == "OWN":
            cw, ch = max(sz + 5, 135), sz + 30
        else:
            cw, ch = sz+5, sz+25
        cols = max(1, w // (cw+5))
        items = self.get_current_items()

        if not items: return

        sel_val = self.sel['type'] if self.mode=="TYPE" else self.sel['own'] if self.mode=="OWN" else self.sel['hgt'] if self.mode=="HGT" else self.sel['blg']
        r, c = 0, 0
        for it in items:
            cell_x, y = c*cw+10, r*ch+10
            x = cell_x + ((cw - sz) // 2 if self.mode == "OWN" else 0)
            if it==sel_val: self.cv_pal.create_rectangle(x-3,y-3,x+sz+3,y+sz+20, fill="#008080", outline="")

            img = None
            lbl = str(it)

            if self.mode=="TYPE": img = self.get_img('type', it, sz)
            elif self.mode=="OWN":
                 lbl = f"{it:02d} - {self.OWNER_PANEL_LABELS.get(it, FACTIONS[it][0].title())}"
                 if it!=0: img = self.get_img('overlay', it, sz, 'pale')
            elif self.mode=="BLG":
                 if it!='00': img = self.get_img('blg', it, sz)
            elif self.mode=="HGT":
                 lbl = str(it - HGT_MIN)
                 img = self.get_img('hgt', it, sz)

            if img:
                self.cv_pal.create_image(x,y,image=img, anchor=tk.NW)
                if self.mode=="BLG":
                    self.draw_building_overlays(x, y, sz, it, None, canvas=self.cv_pal, palette=True)
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
        try:
            self.cv_pal.yview_moveto(max(0.0, min(1.0, previous_y)))
        except:
            pass

    def get_current_items(self):
        if self.mode=="TYPE": return self.lists['type']
        elif self.mode=="OWN": return list(FACTIONS.keys())
        elif self.mode=="HGT":
            return list(range(HGT_MIN, HGT_MAX + 1))
        elif self.mode=="BLG": return self.lists['blg']
        return []

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
        self.zoom_m = max(self.zoom_m_min, min(self.zoom_m_max, self.zoom_m+d))
        self.draw_grid(); self.cv_map.config(scrollregion=(0,0,self.mw*self.zoom_m, self.mh*self.zoom_m))

    def zoom_map_at_cursor(self, event, direction):
        if direction == 0:
            return "break"

        old_zoom = self.zoom_m
        new_zoom = max(
            self.zoom_m_min,
            min(self.zoom_m_max, old_zoom + (self.zoom_m_step if direction > 0 else -self.zoom_m_step))
        )
        if new_zoom == old_zoom:
            return "break"

        view_w = max(1, self.cv_map.winfo_width())
        view_h = max(1, self.cv_map.winfo_height())
        mouse_x = max(0, min(view_w - 1, int(event.x)))
        mouse_y = max(0, min(view_h - 1, int(event.y)))

        old_total_w = max(1, self.mw * old_zoom)
        old_total_h = max(1, self.mh * old_zoom)

        old_offset_x = 0.0
        old_offset_y = 0.0
        try:
            x0, _ = self.cv_map.xview()
            y0, _ = self.cv_map.yview()
            if old_total_w > view_w:
                old_offset_x = x0 * (old_total_w - view_w)
            if old_total_h > view_h:
                old_offset_y = y0 * (old_total_h - view_h)
        except:
            pass

        # Punto logico sotto il mouse prima dello zoom.
        map_x = (old_offset_x + mouse_x) / max(1, old_zoom)
        map_y = (old_offset_y + mouse_y) / max(1, old_zoom)

        self.zoom_m = new_zoom
        self.draw_grid()

        new_total_w = max(1, self.mw * new_zoom)
        new_total_h = max(1, self.mh * new_zoom)
        self.root.update_idletasks()

        # Nuovi offset che mantengono lo stesso punto logico sotto il cursore.
        new_offset_x = (map_x * new_zoom) - mouse_x
        new_offset_y = (map_y * new_zoom) - mouse_y

        max_off_x = max(0.0, new_total_w - view_w)
        max_off_y = max(0.0, new_total_h - view_h)
        new_offset_x = max(0.0, min(max_off_x, new_offset_x))
        new_offset_y = max(0.0, min(max_off_y, new_offset_y))

        if new_total_w > view_w:
            x_frac = new_offset_x / max(1, (new_total_w - view_w))
            self.cv_map.xview_moveto(max(0.0, min(1.0, x_frac)))
        else:
            self.cv_map.xview_moveto(0.0)

        if new_total_h > view_h:
            y_frac = new_offset_y / max(1, (new_total_h - view_h))
            self.cv_map.yview_moveto(max(0.0, min(1.0, y_frac)))
        else:
            self.cv_map.yview_moveto(0.0)

<<<<<<< HEAD
=======
        self.update_hover_from_event(event)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        return "break"

    def bind_scroll(self, w):
        if w == self.cv_map:
            w.bind("<Button-4>", self.on_map_wheel_linux_up)
            w.bind("<Button-5>", self.on_map_wheel_linux_down)
            w.bind("<MouseWheel>", self.on_map_mousewheel)
            w.bind("<Motion>", self.on_mouse_move)
        else:
            w.bind("<Button-4>", lambda e: w.yview_scroll(-1,"units"))
            w.bind("<Button-5>", lambda e: w.yview_scroll(1,"units"))
            w.bind("<MouseWheel>", lambda e: w.yview_scroll(int(-1*(e.delta/120)),"units"))

    def bind_palette_scroll_and_zoom(self):
        self.cv_pal.bind("<Button-4>", lambda e: self.on_palette_wheel(e, 1))
        self.cv_pal.bind("<Button-5>", lambda e: self.on_palette_wheel(e, -1))
        self.cv_pal.bind("<MouseWheel>", self.on_palette_mousewheel)

    def on_palette_mousewheel(self, event):
        delta = 1 if event.delta > 0 else -1
        return self.on_palette_wheel(event, delta)

    def on_palette_wheel(self, event, delta_sign):
        ctrl_pressed = (event.state & 0x4) != 0
        if ctrl_pressed:
            self.zoom_pal(16 if delta_sign > 0 else -16)
        else:
            self.cv_pal.yview_scroll(-1 if delta_sign > 0 else 1, "units")
        return "break"

    def on_map_wheel_linux_up(self, event):
        return self.zoom_map_at_cursor(event, 1)

    def on_map_wheel_linux_down(self, event):
        return self.zoom_map_at_cursor(event, -1)

    def on_map_mousewheel(self, event):
        if event.delta > 0:
            return self.zoom_map_at_cursor(event, 1)
        if event.delta < 0:
            return self.zoom_map_at_cursor(event, -1)
        return "break"

    def on_space_pan_press(self, event):
        self.space_pan_active = True

    def on_space_pan_release(self, event):
        self.space_pan_active = False
        if self._map_panning and self._map_pan_source == "space_left":
            self.stop_map_pan(event)

    def on_map_left_press(self, event):
        if self.space_pan_active:
            return self.start_map_pan(event, source="space_left")
<<<<<<< HEAD
=======
        self.update_hover_from_event(event)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        if self.mode in ["TYPE", "OWN", "BLG", "HGT", "GATE", "ITEM", "GEM", "SQUAD", "HOST"] and not self._map_edit_snapshot_taken:
            self.push_undo_snapshot()
            self._map_edit_snapshot_taken = True
        return self.on_click(event)

    def on_map_left_drag(self, event):
        if self._map_panning and self._map_pan_source == "space_left":
            return self.drag_map_pan(event)
<<<<<<< HEAD
=======
        self.update_hover_from_event(event)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        return self.on_click(event)

    def on_map_left_release(self, event):
        if self._map_panning and self._map_pan_source == "space_left":
            self.stop_map_pan(event)
            return "break"
        self._map_edit_snapshot_taken = False
        self.on_release(event)

    def start_map_pan_middle(self, event):
        return self.start_map_pan(event, source="middle")

    def start_map_pan(self, event, source="middle"):
        self._map_panning = True
        self._map_pan_source = source
<<<<<<< HEAD
=======
        self.clear_hover_overlay()
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        self.cv_map.focus_set()
        self.cv_map.scan_mark(event.x, event.y)
        self.cv_map.config(cursor="fleur")
        return "break"

    def drag_map_pan(self, event):
        if not self._map_panning:
            return
        self.cv_map.scan_dragto(event.x, event.y, gain=1)
        return "break"

    def stop_map_pan(self, event=None):
        self._map_panning = False
        self._map_pan_source = None
        self.cv_map.config(cursor="")
<<<<<<< HEAD
=======
        if event is not None:
            self.update_hover_from_event(event)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        return "break"

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
                        self.push_undo_snapshot()
                        self.squads.pop(i); self.draw_cell(cx, cy); self.refresh_squad_list(); break
             return

        # HOST REMOVAL
        if self.mode == "HOST":
             self.lb_hosts.selection_clear(0, tk.END); self.current_host_index = -1; self.draw_grid()
             for i in reversed(range(len(self.host_stations))):
                    h = self.host_stations[i]
                    if h['x'] == cx and h['y'] == cy:
                        self.push_undo_snapshot()
                        self.host_stations.pop(i); self.draw_cell(cx, cy); self.refresh_host_list(); break
             return

        if self.mode in ["TYPE", "OWN", "BLG", "HGT"]: self.pick(e); return
        if self.mode == "GATE":
            for i, g in self.gates.items():
                if g['x'] == cx and g['y'] == cy:
                    self.push_undo_snapshot()
                    g['x'] = -1; g['y'] = -1; self.draw_cell(cx, cy); return
                if (cx, cy) in g['keys']:
                    self.push_undo_snapshot()
                    g['keys'].remove((cx, cy)); self.draw_cell(cx, cy); return
        elif self.mode == "ITEM":
            for i, it in self.items.items():
                if it['x'] == cx and it['y'] == cy:
                    self.push_undo_snapshot()
                    it['x'] = -1; it['y'] = -1; self.draw_cell(cx, cy); return
                if (cx, cy) in it['keys']:
                    self.push_undo_snapshot()
                    it['keys'].remove((cx, cy)); self.draw_cell(cx, cy); return
        elif self.mode == "GEM":
            for i, gm in self.gems.items():
                if gm['x'] == cx and gm['y'] == cy:
                    self.push_undo_snapshot()
                    gm['x'] = -1; gm['y'] = -1; self.draw_cell(cx, cy); return

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
                if hasattr(self, 'update_height_ui_after_value_change'):
                    self.update_height_ui_after_value_change()
                elif hasattr(self, 'hgt_entry'):
                    user_val = new_hgt - HGT_MIN
                    self.hgt_entry.delete(0, tk.END); self.hgt_entry.insert(0, str(user_val))
            elif self.mode=="BLG": self.sel['blg']=self.grids['blg'][cy][cx]
            self.upd_lbl(); self.draw_palette()

    def on_mouse_move(self, e):
<<<<<<< HEAD
=======
        self.update_hover_from_event(e)
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        if self._map_panning:
            return
        if self.mode in ["TYPE", "OWN", "BLG", "HGT"]: return

        cx = int(self.cv_map.canvasx(e.x)//self.zoom_m)
        cy = int(self.cv_map.canvasy(e.y)//self.zoom_m)
<<<<<<< HEAD
=======
        if not (0 <= cx < self.mw and 0 <= cy < self.mh):
            return
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
        world_x, world_z = self.grid_to_world(cx, cy)

        if hasattr(self, 'lbl_sel'):
            base_txt = self.lbl_sel.cget("text").split(" | ")[0]
            self.lbl_sel.config(text=f"{base_txt} | POS_X: {world_x}  POS_Z: {world_z}")

        # Auto-trigger move logic for Dragging
        if (self.mode == "SQUAD" or self.mode == "HOST") and str(e.type) == '6': self.on_click(e)

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

    def toggle_clear(self):
        self.clear_view = not self.clear_view
        self.btn_cl.config(bg="#00FF00" if self.clear_view else "#444"); self.draw_grid()
