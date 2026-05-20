import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path
from dataclasses import dataclass
import copy

# ============================================================
# CARTELLE
# ============================================================

ICON_FOLDER = Path("buildings_icons")
OUTPUT_FOLDER = Path("output_buildings")

ICON_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)


# ============================================================
# DATI ICONA
# ============================================================

@dataclass
class PlacedIcon:
    icon_name: str
    x: int = 50          # percentuale 0-100
    y: int = 50          # percentuale 0-100
    scale: float = 1.0   # moltiplicatore dimensione


# ============================================================
# TOOL
# ============================================================

class BuildingIconTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Sektor Buildings Builder")

        self.base_img = None
        self.base_path = None

        self.icons = {}          # nome -> PIL image
        self.placed_icons = []   # lista PlacedIcon
        self.selected_index = None

        self.preview_img = None
        self.updating_controls = False

        self.icon_var = tk.StringVar()
        self.output_name = tk.StringVar(value="00")

        self.icon_x = tk.IntVar(value=50)
        self.icon_y = tk.IntVar(value=50)
        self.icon_scale = tk.DoubleVar(value=1.0)

        self.build_ui()
        self.load_icons()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):
        self.root.configure(bg="#111111")

        left = tk.Frame(self.root, bg="#202020", width=260)
        left.pack(side="left", fill="y")

        right = tk.Frame(self.root, bg="#111111")
        right.pack(side="right", fill="both", expand=True)

        # --------------------------
        # Load immagine
        # --------------------------

        tk.Button(
            left,
            text="Load Sector Image",
            command=self.load_base,
            bg="#333333",
            fg="white"
        ).pack(fill="x", padx=8, pady=(8, 4))

        tk.Label(
            left,
            text="Output HEX name:",
            fg="cyan",
            bg="#202020"
        ).pack(anchor="w", padx=8)

        tk.Entry(
            left,
            textvariable=self.output_name,
            bg="#111111",
            fg="white",
            insertbackground="white"
        ).pack(fill="x", padx=8, pady=(0, 8))

        # --------------------------
        # Scelta icona
        # --------------------------

        tk.Label(
            left,
            text="Icon type:",
            fg="cyan",
            bg="#202020"
        ).pack(anchor="w", padx=8)

        self.icon_menu = tk.OptionMenu(left, self.icon_var, "")
        self.icon_menu.config(bg="#333333", fg="white", highlightthickness=0)
        self.icon_menu["menu"].config(bg="#222222", fg="white")
        self.icon_menu.pack(fill="x", padx=8, pady=(0, 6))

        # --------------------------
        # Bottoni icone
        # --------------------------

        row1 = tk.Frame(left, bg="#202020")
        row1.pack(fill="x", padx=8, pady=2)

        tk.Button(row1, text="Add", command=self.add_icon, bg="#005f5f", fg="white").pack(side="left", fill="x", expand=True, padx=1)
        tk.Button(row1, text="Remove", command=self.remove_icon, bg="#5f0000", fg="white").pack(side="left", fill="x", expand=True, padx=1)

        row2 = tk.Frame(left, bg="#202020")
        row2.pack(fill="x", padx=8, pady=2)

        tk.Button(row2, text="Duplicate", command=self.duplicate_icon, bg="#333333", fg="white").pack(side="left", fill="x", expand=True, padx=1)
        tk.Button(row2, text="Clear", command=self.clear_icons, bg="#333333", fg="white").pack(side="left", fill="x", expand=True, padx=1)

        row3 = tk.Frame(left, bg="#202020")
        row3.pack(fill="x", padx=8, pady=2)

        tk.Button(row3, text="Up", command=self.move_icon_up, bg="#333333", fg="white").pack(side="left", fill="x", expand=True, padx=1)
        tk.Button(row3, text="Down", command=self.move_icon_down, bg="#333333", fg="white").pack(side="left", fill="x", expand=True, padx=1)

        # --------------------------
        # Lista icone piazzate
        # --------------------------

        tk.Label(
            left,
            text="Placed icons:",
            fg="cyan",
            bg="#202020"
        ).pack(anchor="w", padx=8, pady=(8, 0))

        self.icon_listbox = tk.Listbox(
            left,
            height=7,
            bg="#111111",
            fg="white",
            selectbackground="#008b8b",
            selectforeground="white",
            activestyle="none"
        )
        self.icon_listbox.pack(fill="x", padx=8, pady=4)
        self.icon_listbox.bind("<<ListboxSelect>>", self.on_icon_selected)

        # --------------------------
        # Controlli icona selezionata
        # --------------------------

        tk.Label(left, text="Icon X %", fg="cyan", bg="#202020").pack(anchor="w", padx=8)
        tk.Scale(
            left,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.icon_x,
            command=lambda e: self.update_selected_icon(),
            bg="#202020",
            fg="white",
            troughcolor="#333333",
            highlightthickness=0
        ).pack(fill="x", padx=8)

        tk.Label(left, text="Icon Y %", fg="cyan", bg="#202020").pack(anchor="w", padx=8)
        tk.Scale(
            left,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.icon_y,
            command=lambda e: self.update_selected_icon(),
            bg="#202020",
            fg="white",
            troughcolor="#333333",
            highlightthickness=0
        ).pack(fill="x", padx=8)

        tk.Label(left, text="Icon Scale", fg="cyan", bg="#202020").pack(anchor="w", padx=8)
        tk.Scale(
            left,
            from_=0.25,
            to=3.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.icon_scale,
            command=lambda e: self.update_selected_icon(),
            bg="#202020",
            fg="white",
            troughcolor="#333333",
            highlightthickness=0
        ).pack(fill="x", padx=8)

        # --------------------------
        # Preset rapidi
        # --------------------------

        tk.Label(
            left,
            text="Quick presets:",
            fg="cyan",
            bg="#202020"
        ).pack(anchor="w", padx=8, pady=(8, 0))

        preset1 = tk.Frame(left, bg="#202020")
        preset1.pack(fill="x", padx=8, pady=2)

        tk.Button(preset1, text="Center", command=self.preset_center, bg="#333333", fg="white").pack(side="left", fill="x", expand=True, padx=1)
        tk.Button(preset1, text="Vertical", command=self.preset_vertical_stack, bg="#333333", fg="white").pack(side="left", fill="x", expand=True, padx=1)

        preset2 = tk.Frame(left, bg="#202020")
        preset2.pack(fill="x", padx=8, pady=2)

        tk.Button(preset2, text="Horizontal", command=self.preset_horizontal_stack, bg="#333333", fg="white").pack(side="left", fill="x", expand=True, padx=1)
        tk.Button(preset2, text="Double Same", command=self.preset_duplicate_vertical, bg="#333333", fg="white").pack(side="left", fill="x", expand=True, padx=1)

        # --------------------------
        # Salva
        # --------------------------

        tk.Button(
            left,
            text="SAVE BUILDING PNG",
            command=self.save_output,
            bg="#008000",
            fg="white"
        ).pack(fill="x", padx=8, pady=12)

        # --------------------------
        # Preview
        # --------------------------

        self.preview_label = tk.Label(right, bg="#111111")
        self.preview_label.pack(fill="both", expand=True)

    # ========================================================
    # ICONE
    # ========================================================

    def load_icons(self):
        self.icons.clear()

        for file in ICON_FOLDER.glob("*.png"):
            try:
                self.icons[file.stem] = Image.open(file).convert("RGBA")
            except Exception as e:
                print(f"Errore caricando icona {file.name}: {e}")

        menu = self.icon_menu["menu"]
        menu.delete(0, "end")

        if not self.icons:
            messagebox.showinfo(
                "Icons missing",
                f"Metti le icone PNG dentro:\n{ICON_FOLDER.resolve()}"
            )
            return

        for name in sorted(self.icons.keys()):
            menu.add_command(label=name, command=lambda n=name: self.icon_var.set(n))

        first = sorted(self.icons.keys())[0]
        self.icon_var.set(first)

    # ========================================================
    # LOAD BASE
    # ========================================================

    def load_base(self):
        file = filedialog.askopenfilename(
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*")
            ]
        )

        if not file:
            return

        self.base_path = Path(file)
        self.base_img = Image.open(file).convert("RGBA")

        # Suggerisce nome output se il file si chiama tipo 1b.png
        stem = self.base_path.stem.lower()
        if len(stem) == 2 and all(c in "0123456789abcdef" for c in stem):
            self.output_name.set(stem)

        self.update_preview()

    # ========================================================
    # GESTIONE LISTA ICONE
    # ========================================================

    def add_icon(self):
        if not self.icons:
            messagebox.showerror("Error", "Nessuna icona trovata.")
            return

        name = self.icon_var.get()

        if not name:
            messagebox.showerror("Error", "Seleziona un'icona.")
            return

        icon = PlacedIcon(icon_name=name, x=50, y=50, scale=1.0)
        self.placed_icons.append(icon)

        self.selected_index = len(self.placed_icons) - 1
        self.refresh_icon_list()
        self.select_listbox_index(self.selected_index)
        self.load_controls_from_selected()
        self.update_preview()

    def remove_icon(self):
        if self.selected_index is None:
            return

        if 0 <= self.selected_index < len(self.placed_icons):
            del self.placed_icons[self.selected_index]

        if not self.placed_icons:
            self.selected_index = None
        else:
            self.selected_index = min(self.selected_index, len(self.placed_icons) - 1)

        self.refresh_icon_list()

        if self.selected_index is not None:
            self.select_listbox_index(self.selected_index)
            self.load_controls_from_selected()

        self.update_preview()

    def duplicate_icon(self):
        if self.selected_index is None:
            return

        icon = copy.deepcopy(self.placed_icons[self.selected_index])

        # Sposta leggermente la copia, così la vedi
        icon.y = min(icon.y + 18, 100)

        self.placed_icons.insert(self.selected_index + 1, icon)
        self.selected_index += 1

        self.refresh_icon_list()
        self.select_listbox_index(self.selected_index)
        self.load_controls_from_selected()
        self.update_preview()

    def clear_icons(self):
        self.placed_icons.clear()
        self.selected_index = None
        self.refresh_icon_list()
        self.update_preview()

    def move_icon_up(self):
        if self.selected_index is None or self.selected_index <= 0:
            return

        i = self.selected_index
        self.placed_icons[i - 1], self.placed_icons[i] = self.placed_icons[i], self.placed_icons[i - 1]
        self.selected_index -= 1

        self.refresh_icon_list()
        self.select_listbox_index(self.selected_index)
        self.update_preview()

    def move_icon_down(self):
        if self.selected_index is None or self.selected_index >= len(self.placed_icons) - 1:
            return

        i = self.selected_index
        self.placed_icons[i + 1], self.placed_icons[i] = self.placed_icons[i], self.placed_icons[i + 1]
        self.selected_index += 1

        self.refresh_icon_list()
        self.select_listbox_index(self.selected_index)
        self.update_preview()

    def refresh_icon_list(self):
        self.icon_listbox.delete(0, "end")

        for i, icon in enumerate(self.placed_icons):
            text = f"{i + 1}. {icon.icon_name}  x:{icon.x} y:{icon.y} s:{icon.scale:.2f}"
            self.icon_listbox.insert("end", text)

    def select_listbox_index(self, index):
        self.icon_listbox.selection_clear(0, "end")
        self.icon_listbox.selection_set(index)
        self.icon_listbox.activate(index)

    def on_icon_selected(self, event=None):
        selection = self.icon_listbox.curselection()

        if not selection:
            return

        self.selected_index = selection[0]
        self.load_controls_from_selected()

    def load_controls_from_selected(self):
        if self.selected_index is None:
            return

        if not (0 <= self.selected_index < len(self.placed_icons)):
            return

        icon = self.placed_icons[self.selected_index]

        self.updating_controls = True
        self.icon_var.set(icon.icon_name)
        self.icon_x.set(icon.x)
        self.icon_y.set(icon.y)
        self.icon_scale.set(icon.scale)
        self.updating_controls = False

    def update_selected_icon(self):
        if self.updating_controls:
            return

        if self.selected_index is None:
            return

        if not (0 <= self.selected_index < len(self.placed_icons)):
            return

        icon = self.placed_icons[self.selected_index]

        icon.icon_name = self.icon_var.get()
        icon.x = int(self.icon_x.get())
        icon.y = int(self.icon_y.get())
        icon.scale = float(self.icon_scale.get())

        self.refresh_icon_list()
        self.select_listbox_index(self.selected_index)
        self.update_preview()

    # ========================================================
    # PRESET
    # ========================================================

    def preset_center(self):
        if self.selected_index is None:
            return

        icon = self.placed_icons[self.selected_index]
        icon.x = 50
        icon.y = 50
        icon.scale = 1.0

        self.load_controls_from_selected()
        self.refresh_icon_list()
        self.select_listbox_index(self.selected_index)
        self.update_preview()

    def preset_vertical_stack(self):
        if len(self.placed_icons) < 2:
            messagebox.showinfo("Preset", "Servono almeno 2 icone.")
            return

        # Sistema le prime due icone in verticale
        self.placed_icons[0].x = 50
        self.placed_icons[0].y = 37
        self.placed_icons[0].scale = 1.0

        self.placed_icons[1].x = 50
        self.placed_icons[1].y = 63
        self.placed_icons[1].scale = 1.0

        self.refresh_icon_list()
        self.update_preview()

    def preset_horizontal_stack(self):
        if len(self.placed_icons) < 2:
            messagebox.showinfo("Preset", "Servono almeno 2 icone.")
            return

        # Sistema le prime due icone in orizzontale
        self.placed_icons[0].x = 38
        self.placed_icons[0].y = 50
        self.placed_icons[0].scale = 1.0

        self.placed_icons[1].x = 62
        self.placed_icons[1].y = 50
        self.placed_icons[1].scale = 1.0

        self.refresh_icon_list()
        self.update_preview()

    def preset_duplicate_vertical(self):
        if self.selected_index is None:
            messagebox.showinfo("Preset", "Seleziona un'icona da duplicare.")
            return

        base = copy.deepcopy(self.placed_icons[self.selected_index])
        base.x = 50
        base.y = 37
        base.scale = 1.0

        duplicate = copy.deepcopy(base)
        duplicate.y = 63

        self.placed_icons = [base, duplicate]
        self.selected_index = 0

        self.refresh_icon_list()
        self.select_listbox_index(0)
        self.load_controls_from_selected()
        self.update_preview()

    # ========================================================
    # COMPOSIZIONE
    # ========================================================

    def compose(self):
        if self.base_img is None:
            return None

        result = self.base_img.copy()
        base_w, base_h = result.size

        for placed in self.placed_icons:
            if placed.icon_name not in self.icons:
                continue

            icon = self.icons[placed.icon_name].copy()

            target_w = int(base_w * 0.22 * placed.scale)
            target_w = max(target_w, 1)

            aspect = icon.height / icon.width
            target_h = int(target_w * aspect)
            target_h = max(target_h, 1)

            icon = icon.resize((target_w, target_h), Image.Resampling.NEAREST)

            x = int((base_w - target_w) * placed.x / 100)
            y = int((base_h - target_h) * placed.y / 100)

            result.alpha_composite(icon, (x, y))

        return result

    def update_preview(self):
        composed = self.compose()

        if composed is None:
            return

        preview = composed.copy()
        preview.thumbnail((1000, 800), Image.Resampling.LANCZOS)

        self.preview_img = ImageTk.PhotoImage(preview)
        self.preview_label.config(image=self.preview_img)

    # ========================================================
    # SALVATAGGIO
    # ========================================================

    def save_output(self):
        composed = self.compose()

        if composed is None:
            messagebox.showerror("Error", "Carica prima un'immagine settore.")
            return

        name = self.output_name.get().strip().lower()

        if not name:
            messagebox.showerror("Error", "Nome output vuoto.")
            return

        if not all(c in "0123456789abcdef" for c in name):
            messagebox.showerror("Error", "Usa solo caratteri esadecimali: 0-9 a-f.")
            return

        out = OUTPUT_FOLDER / f"{name}.png"

        composed.save(out, optimize=True, compress_level=9)

        messagebox.showinfo("Saved", f"Salvato:\n{out}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = BuildingIconTool(root)
    root.mainloop()