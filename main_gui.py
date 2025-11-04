import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import sys
import subprocess

class MedicalVisualizationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Medical Visualization System")
        self.root.geometry("1350x800")
        self.root.configure(bg='#0a0e27')
        
        # Colors
        self.colors = {
            "bg_dark": "#0a0e27",
            "bg_header": "#0f1941",
            "card_bg": "#1a1f3a",
            "card_border": "#2d3561",
            "text_primary": "#ffffff",
            "text_secondary": "#b0b8c4",
            "text_muted": "#7f8c9a",
            "accent_cyan": "#00d4ff",
            "nervous": "#9b59b6",
            "cardio": "#e74c3c",
            "muscle": "#f39c12",
            "dental": "#3498db"
        }
        
        # Systems
        self.systems = {
            "Nervous System": {
                "code": "nervous",
                "color": "#9b59b6",
                "image": "nervous.png"
            },
            "Cardiovascular System": {
                "code": "cardiovascular",
                "color": "#e74c3c",
                "image": "cardiovascular.png"
            },
            "Musculoskeletal System": {
                "code": "musculoskeletal",
                "color": "#f39c12",
                "image": "musculoskeletal.png"
            },
            "Mouth/Dental System": {
                "code": "dental",
                "color": "#3498db",
                "image": "dental.png"
            }
        }
        
        self.features = {
            "Visualization Methods": [
                "Surface Rendering",
                "Clipping Plans",
                "Curved MPR"
            ],
            "Navigation Methods": [
                "Focus Navigation",
                "Moving Stuff Illustration",
                "Fly-through Navigation"
            ]
        }
        
        self.file_to_system_mapping = self.create_file_system_mapping()
        self.selected_system = None
        self.images = []
        
        self.show_main_menu()
    
    def create_file_system_mapping(self):
        mapping = {
            "Cardiovascular System": [],
            "Nervous System": [],
            "Musculoskeletal System": [],
            "Mouth/Dental System": []
        }
        
        for file in os.listdir('.'):
            if file.endswith('.py') and file != 'main_gui.py':
                file_lower = file.lower()
                if 'heart' in file_lower or 'aorta' in file_lower:
                    mapping["Cardiovascular System"].append(file)
                elif 'brain' in file_lower:
                    mapping["Nervous System"].append(file)
                elif 'bone' in file_lower or 'skeleton' in file_lower or 'muscle' in file_lower:
                    mapping["Musculoskeletal System"].append(file)
                elif 'tooth' in file_lower or 'dental' in file_lower or 'mouth' in file_lower:
                    mapping["Mouth/Dental System"].append(file)
        
        return mapping
    
    def get_feature_file(self, system_name, feature_name):
        feature_patterns = {
            "Surface Rendering": ["surfacerendering", "rendering"],
            "Clipping Plans": ["clipping", "clippingplans"],
            "Curved MPR": ["curved", "mpr", "curvedmpr"],
            "Focus Navigation": ["focus", "navigation", "focusnavigation"],
            "Moving Stuff Illustration": ["moving", "illustration", "movingstuff"],
            "Fly-through Navigation": ["flythrough", "fly"]
        }
        
        pattern = feature_patterns.get(feature_name, [])
        system_files = self.file_to_system_mapping.get(system_name, [])
        
        for file in system_files:
            file_lower = file.lower()
            for p in pattern:
                if p in file_lower:
                    return file
        return None
    
    def load_system_image(self, image_file, size=(110, 110)):
        try:
            if os.path.exists(image_file):
                img = Image.open(image_file)
                img = img.resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except:
            pass
        return self.create_placeholder_image(size)
    
    def create_placeholder_image(self, size=(110, 110)):
        img = Image.new('RGB', size, (42, 47, 74))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=(255, 255, 255), width=2)
        return ImageTk.PhotoImage(img)
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.images.clear()
    
    def show_main_menu(self):
        self.clear_window()
        
        # Header
        header = tk.Frame(self.root, bg=self.colors["bg_header"], height=100)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="3D Medical Visualization System",
            font=("Segoe UI", 32, "bold"),
            bg=self.colors["bg_header"],
            fg=self.colors["accent_cyan"]
        )
        title.pack(pady=28)
        
        # Subtitle
        subtitle_frame = tk.Frame(self.root, bg=self.colors["bg_dark"], height=50)
        subtitle_frame.pack(fill=tk.X, side=tk.TOP)
        subtitle_frame.pack_propagate(False)
        
        subtitle = tk.Label(
            subtitle_frame,
            text="SELECT AN ANATOMICAL SYSTEM",
            font=("Segoe UI", 12),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_secondary"]
        )
        subtitle.pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors["bg_dark"])
        main_container.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Content frame - centered
        content = tk.Frame(main_container, bg=self.colors["bg_dark"])
        content.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=1200, height=520)
        
        # Create all 4 cards - SAME SIZE
        systems_list = list(self.systems.items())
        for idx, (sys_name, sys_info) in enumerate(systems_list):
            row = idx // 2
            col = idx % 2
            self.create_system_card(content, sys_name, sys_info, row, col)
        
        # Grid configuration - uniform
        content.grid_columnconfigure(0, weight=1, uniform="col")
        content.grid_columnconfigure(1, weight=1, uniform="col")
        content.grid_rowconfigure(0, weight=1, uniform="row")
        content.grid_rowconfigure(1, weight=1, uniform="row")
        
        # Footer
        footer = tk.Frame(self.root, bg=self.colors["bg_header"], height=45)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        footer.pack_propagate(False)
        
        footer_text = tk.Label(
            footer,
            text="4 SYSTEMS  •  3 VISUALIZATION  •  3 NAVIGATION",
            font=("Segoe UI", 9),
            bg=self.colors["bg_header"],
            fg=self.colors["text_muted"]
        )
        footer_text.pack(pady=14)
    
    def create_system_card(self, parent, sys_name, sys_info, row, col):
        color = sys_info["color"]
        image_file = sys_info["image"]
        
        # Card container
        card_container = tk.Frame(parent, bg=self.colors["bg_dark"])
        card_container.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
        
        # Card - ALL SAME SIZE: 560x230
        card = tk.Frame(
            card_container,
            bg=self.colors["card_bg"],
            highlightthickness=2,
            highlightbackground=self.colors["card_border"],
            width=560,
            height=230
        )
        card.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        card.pack_propagate(False)
        
        # Image
        img = self.load_system_image(image_file, (110, 110))
        self.images.append(img)
        
        img_label = tk.Label(card, image=img, bg=self.colors["card_bg"])
        img_label.pack(pady=(15, 8))
        
        # System name
        name_label = tk.Label(
            card,
            text=sys_name,
            font=("Segoe UI", 17, "bold"),
            bg=self.colors["card_bg"],
            fg=self.colors["text_primary"]
        )
        name_label.pack(pady=(0, 4))
        
        # Feature count
        count = len(self.file_to_system_mapping.get(sys_name, []))
        count_text = f"{count} features available" if count > 0 else "Coming Soon"
        
        count_label = tk.Label(
            card,
            text=count_text,
            font=("Segoe UI", 9),
            bg=self.colors["card_bg"],
            fg=self.colors["text_muted"]
        )
        count_label.pack(pady=(0, 10))
        
        # EXPLORE button
        explore_btn = tk.Button(
            card,
            text="EXPLORE →",
            font=("Segoe UI", 11, "bold"),
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            bd=0,
            width=15,
            command=lambda s=sys_name: self.select_system(s)
        )
        explore_btn.pack(ipady=6)
        
        # Hover effects
        def on_enter(e):
            card.config(highlightbackground=color, highlightthickness=3)
            explore_btn.config(bg=self.lighten_color(color))
        
        def on_leave(e):
            card.config(highlightbackground=self.colors["card_border"], highlightthickness=2)
            explore_btn.config(bg=color)
        
        for widget in [card, img_label, name_label, count_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
    
    def lighten_color(self, color):
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r * 1.25))
        g = min(255, int(g * 1.25))
        b = min(255, int(b * 1.25))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def select_system(self, system_name):
        print(f"\n>>> Selected: {system_name}")
        self.selected_system = system_name
        self.show_features_menu()
    
    def show_features_menu(self):
        self.clear_window()
        
        color = self.systems[self.selected_system]["color"]
        
        # Header
        header = tk.Frame(self.root, bg=self.colors["bg_header"], height=95)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        # Back button
        back_btn = tk.Button(
            header,
            text="← BACK",
            font=("Segoe UI", 10, "bold"),
            bg='#2d3561',
            fg='white',
            activebackground='#3d4571',
            relief=tk.FLAT,
            cursor="hand2",
            bd=0,
            padx=20,
            pady=8,
            command=self.show_main_menu
        )
        back_btn.place(x=22, y=22)
        
        # Title
        title = tk.Label(
            header,
            text=self.selected_system.upper(),
            font=("Segoe UI", 26, "bold"),
            bg=self.colors["bg_header"],
            fg=color
        )
        title.pack(pady=28)
        
        # Subtitle
        subtitle_frame = tk.Frame(self.root, bg=self.colors["bg_dark"], height=50)
        subtitle_frame.pack(fill=tk.X, side=tk.TOP)
        subtitle_frame.pack_propagate(False)
        
        subtitle = tk.Label(
            subtitle_frame,
            text="SELECT A FEATURE",
            font=("Segoe UI", 11),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_secondary"]
        )
        subtitle.pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors["bg_dark"])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Content
        main = tk.Frame(main_container, bg=self.colors["bg_dark"])
        main.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=1200)
        
        # Visualization
        viz = self.create_feature_section(
            main,
            "VISUALIZATION METHODS",
            self.features["Visualization Methods"],
            "#00d4ff",
            "#0078d4"
        )
        viz.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        
        # Navigation
        nav = self.create_feature_section(
            main,
            "NAVIGATION METHODS",
            self.features["Navigation Methods"],
            "#00ff88",
            "#00aa66"
        )
        nav.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
    
    def create_feature_section(self, parent, title, features, title_color, btn_color):
        frame = tk.LabelFrame(
            parent,
            text=f"  {title}  ",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["card_bg"],
            fg=title_color,
            bd=2,
            padx=20,
            pady=20
        )
        
        for feature in features:
            file_name = self.get_feature_file(self.selected_system, feature)
            exists = file_name is not None
            
            item = tk.Frame(frame, bg='#0f1326', bd=1, relief=tk.SOLID)
            item.pack(pady=8, fill=tk.X, ipady=2)
            
            btn = tk.Button(
                item,
                text=feature,
                font=("Segoe UI", 11, "bold"),
                bg=btn_color if exists else '#3d4571',
                fg='white',
                activebackground=self.lighten_color(btn_color) if exists else '#4d5581',
                width=30,
                height=2,
                relief=tk.FLAT,
                cursor="hand2" if exists else "arrow",
                state=tk.NORMAL if exists else tk.DISABLED,
                bd=0,
                command=lambda f=feature: self.run_feature(f)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            
            status = tk.Label(
                item,
                text="✓" if exists else "⏳",
                font=("Segoe UI", 12, "bold"),
                bg='#0f1326',
                fg='#27ae60' if exists else self.colors["text_muted"]
            )
            status.pack(side=tk.RIGHT, padx=10)
        
        return frame
    
    def run_feature(self, feature_name):
        file_name = self.get_feature_file(self.selected_system, feature_name)
        
        if not file_name:
            messagebox.showinfo(
                "Coming Soon",
                f"{feature_name}\n\nWill be available soon for {self.selected_system}!"
            )
            return
        
        print(f"\n{'='*60}")
        print(f"Running: {feature_name}")
        print(f"System: {self.selected_system}")
        print(f"File: {file_name}")
        print(f"{'='*60}\n")
        
        self.root.withdraw()
        
        try:
            subprocess.run([sys.executable, file_name], cwd=os.getcwd())
        except Exception as e:
            messagebox.showerror("Error", f"Error:\n{str(e)}")
        finally:
            self.root.deiconify()
            print("\n>>> Returned to main menu\n")

def main():
    root = tk.Tk()
    
    # Center window
    w, h = 1350, 800
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f'{w}x{h}+{x}+{y}')
    
    root.minsize(1200, 700)
    
    app = MedicalVisualizationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()