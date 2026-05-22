import json
import os
from tkinter import messagebox

from PIL import Image, ImageDraw, ImageTk

from sektor_constants import *
from sektor_paths import resource_path, writable_path


class AssetMixin:

    def ensure_asset_dir(self, relative_dir):
        path = resource_path(relative_dir)
        if os.path.isdir(path):
            return path
        path = writable_path(relative_dir)
        try:
            os.makedirs(path, exist_ok=True)
        except:
            pass
        return path

    def iter_asset_files(self, relative_dir, extensions=IMAGE_EXTENSIONS, create_if_missing=False):
        directory = self.ensure_asset_dir(relative_dir) if create_if_missing else resource_path(relative_dir)
        if not os.path.isdir(directory):
            return []
        return [
            (filename, os.path.join(directory, filename))
            for filename in sorted(os.listdir(directory))
            if filename.lower().endswith(extensions)
        ]

    def make_fallback_icon(self, fallback_col, fallback_txt):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([4, 4, 60, 60], outline=fallback_col, width=4)
        draw.text((10, 20), fallback_txt, fill=fallback_col)
        return img

    def load_icon(self, filename, key, fallback_col, fallback_txt):
        path = resource_path(os.path.join("icons", filename))
        if os.path.exists(path):
            self.assets[key] = Image.open(path)
        else:
            self.assets[key] = self.make_fallback_icon(fallback_col, fallback_txt)

    def load_standard_icons(self, include_custom_tile_icons=False):
        self.ensure_asset_dir("icons")
        if include_custom_tile_icons:
<<<<<<< HEAD
            self.load_icon("custom_sector.png", "custom_sector", "#FF0000", "SEC\nGHOST")
            self.load_icon("custom_building.png", "custom_building", "#FF0000", "BLG\nGHOST")

        self.load_icon("custom.png", "custom_mod", "#FF00FF", "GHOST")
=======
<<<<<<< HEAD
            self.load_icon("custom_sector.png", "custom_sector", "#FF0000", "SEC\nMOD")
            self.load_icon("custom_building.png", "custom_building", "#FF0000", "BLG\nMOD")

        self.load_icon("custom.png", "custom_mod", "#FF00FF", "MOD")
=======
            self.load_icon("custom_sector.png", "custom_sector", "#FF0000", "SEC\nGHOST")
            self.load_icon("custom_building.png", "custom_building", "#FF0000", "BLG\nGHOST")

        self.load_icon("custom.png", "custom_mod", "#FF00FF", "GHOST")
>>>>>>> 9935212 (Refactor code structure for improved readability and maintainability)
>>>>>>> 960ab1aa40a49cce6e2d2ab9956235aab9074263
        self.load_icon("gate.png", "gate", "#00FFFF", "GATE")
        self.load_icon("key.png", "key", "#FFFF00", "KEY")
        self.load_icon("superitem.png", "item", "#FF00FF", "ITEM")
        self.load_icon("superitem_key.png", "item_key", "#FF9900", "KEY")
        self.load_icon("gem.png", "gem", "#00FF00", "GEM")

        for i in range(1, 9):
            fac_col = FACTIONS[i][1] if i in FACTIONS and FACTIONS[i][1] else "#FFF"
            self.load_icon(f"host_{i}.png", f"host_{i}", fac_col, f"HOST\n{i}")

    def load_set_tiles(self):
        for filename, path in self.iter_asset_files(self.set_folder, extensions=TILE_IMAGE_EXTENSIONS):
            key = os.path.splitext(filename)[0]
            self.assets[key] = Image.open(path)
            self.lists['type'].append(key)
        if self.lists['type']:
            self.sel['type'] = self.lists['type'][0]

    def load_building_tiles(self):
        for filename, path in self.iter_asset_files("buildings", extensions=TILE_IMAGE_EXTENSIONS, create_if_missing=True):
            key = os.path.splitext(filename)[0]
            self.assets[f"blg_{key}"] = Image.open(path)
            if key not in self.lists['blg']:
                self.lists['blg'].append(key)

    def load_gem_graphics(self):
        for filename, path in self.iter_asset_files("gems", extensions=GEM_IMAGE_EXTENSIONS):
            key = os.path.splitext(filename)[0]
            try:
                self.assets[f"gem_graphic_{key}"] = Image.open(path)
                self.lists['gem_graphics'].append(key)
            except:
                pass

    def load_sky_list(self):
        self.lists['sky'] = [
            filename
            for filename, _ in self.iter_asset_files("skies", create_if_missing=True)
        ]

    def load_generated_owner_overlays(self):
        for i in range(1, 9):
            col_hex = FACTIONS.get(i, ["Unknown", "#888888"])[1]
            if col_hex.startswith("#"):
                col_hex = col_hex[1:]
            if len(col_hex) == 3:
                col_hex = "".join([c * 2 for c in col_hex])
            try:
                r, g, b = tuple(int(col_hex[j:j + 2], 16) for j in (0, 2, 4))
            except:
                r, g, b = (128, 128, 128)
            alpha = 40 if i in [1, 2, 4, 6, 7] else 90
            self.assets[str(i)] = Image.new("RGBA", (64, 64), (r, g, b, alpha))

    def load_asset_catalogs(self, include_generated_overlays=False, include_custom_tile_icons=False):
        if include_generated_overlays:
            self.load_generated_owner_overlays()

        self.load_set_tiles()
        self.load_building_tiles()
        self.load_gem_graphics()
        self.load_sky_list()
        self.load_standard_icons(include_custom_tile_icons=include_custom_tile_icons)
        self.load_building_overlay_icons()
        self.load_building_overlays()

    def load_assets(self):
        self.load_asset_catalogs()

    def reload_assets(self):
        self.assets = {}
        self.lists = {'type': [], 'blg': ['00'], 'sky': [], 'gem_graphics': []}
        self.cache = {}

        self.load_asset_catalogs(include_generated_overlays=True, include_custom_tile_icons=True)

        self.draw_palette()
        self.draw_grid()
        self.update_window_title()

    def load_building_overlay_icons(self):
        self.ensure_asset_dir(os.path.join("buildings", "buildings_icons"))

        for filename, path in self.iter_asset_files(os.path.join("buildings", "buildings_icons")):
            key = os.path.splitext(filename)[0].lower()
            try:
                self.assets[f"building_overlay_{key}"] = Image.open(path)
            except:
                pass

    def load_building_overlays(self):
        candidates = [
            os.path.join("definitions", "building_overlays.json"),
            os.path.join("buildings", "building_overlays.json"),
            "building_overlays.json",
        ]
        self.building_overlays = {}

        path = None
        for candidate in candidates:
            candidate_path = resource_path(candidate)
            if os.path.exists(candidate_path):
                path = candidate_path
                break

        if path is None:
            path = writable_path(os.path.join("definitions", "building_overlays.json"))
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=2)
                    f.write("\n")
            except:
                pass
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            try:
                messagebox.showwarning("Building Overlays", f"Invalid building_overlays.json:\n{e}")
            except:
                pass
            return

        if not isinstance(data, dict):
            try:
                messagebox.showwarning("Building Overlays", "building_overlays.json must contain an object.")
            except:
                pass
            return

        for bid, icons in data.items():
            if not isinstance(icons, list):
                continue
            clean_icons = [str(icon).lower() for icon in icons if isinstance(icon, str)]
            if clean_icons:
                self.building_overlays[str(bid).lower()] = clean_icons

    def load_definition_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            try:
                messagebox.showwarning("Definitions", f"Could not load {path}:\n{e}")
            except:
                pass
            return {}

        if not isinstance(data, list):
            try:
                messagebox.showwarning("Definitions", f"{path} must contain a JSON array.")
            except:
                pass
            return {}

        loaded = {}
        for entry in data:
            if not isinstance(entry, dict):
                continue
            try:
                eid = int(entry["id"])
            except:
                continue
            name = str(entry.get("name", "")).strip()
            if name:
                loaded[eid] = name
        return loaded

    def load_definitions(self):
        for kind, base_name in [('veh', 'vehicles'), ('blg', 'buildings'), ('host', 'hoststations')]:
            path = resource_path(os.path.join("definitions", f"{base_name}.json"))
            if os.path.exists(path):
                self.defs[kind] = self.load_definition_json(path)
                if not self.defs[kind]:
                    try:
                        messagebox.showwarning("Definitions", f"No valid definitions found in:\n{path}")
                    except:
                        pass
            else:
                self.defs[kind] = {}
                try:
                    messagebox.showwarning("Definitions", f"Missing required definition file:\n{path}")
                except:
                    pass

    def get_img(self, cat, name, sz, extra=None):
        key = (cat, name, sz, extra)
        if key in self.cache:
            return self.cache[key]
        src = None

        if cat == 'type':
            if name in self.assets:
                src = self.assets[name]

        elif cat == 'blg':
            if f"blg_{name}" in self.assets:
                src = self.assets[f"blg_{name}"]

        elif cat == 'gem_graphic':
            if f"gem_graphic_{name}" in self.assets:
                src = self.assets[f"gem_graphic_{name}"]

        elif cat == 'building_overlay':
            overlay_key = f"building_overlay_{str(name).lower()}"
            if overlay_key in self.assets:
                src = self.assets[overlay_key]

        elif cat == 'special':
            if name in self.assets:
                src = self.assets[name]

        elif cat == 'host':
            h_key = f"host_{name}"
            if h_key not in self.assets:
                path = resource_path(os.path.join("icons", f"{name}.png"))
                if os.path.exists(path):
                    self.assets[h_key] = Image.open(path)
            if h_key in self.assets:
                src = self.assets[h_key]
            else:
                src = self.assets["custom_mod"]

        elif cat == 'overlay':
            fid = int(name)
            if fid in FACTIONS and FACTIONS[fid][1]:
                col = FACTIONS[fid][1]
                rgb = tuple(int(col.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                if extra == 'pale':
                    alpha = 200
                elif fid == 7:
                    alpha = 171
                elif fid == 5:
                    alpha = 128
                else:
                    alpha = 60
                src = Image.new("RGBA", (sz, sz), rgb + (alpha,))
        elif cat == 'hgt':
            h = int(name)
            diff = abs(h - 127)
            alpha = int(min(200, diff * 6.6))
            color = (255, 255, 255) if h > 127 else (0, 0, 0)
            src = Image.new("RGBA", (sz, sz), color + (alpha,))
        elif cat == 'border':
            src = Image.new("RGBA", (sz, sz), (0, 255, 255, 140))

        if src:
            tk_img = ImageTk.PhotoImage(src.resize((sz, sz), Image.Resampling.NEAREST))
            self.cache[key] = tk_img
            return tk_img
        return None
