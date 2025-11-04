import os
import glob
import numpy as np
import pyvista as pv
from PyQt5 import QtWidgets, QtCore
from pyvistaqt import BackgroundPlotter
import sys

"""
🦷 Dental Opacity Control - View and Control Surface Transparency
Simple viewer with opacity control for each dental part
"""

# Dental part colors
DENTAL_COLORS = {
    'upper_jaw':    (0.95, 0.92, 0.88),  # Bone white
    'lower_jaw':    (0.92, 0.89, 0.85),  # Slightly darker bone
    'teeth':        (0.98, 0.98, 0.95),  # White teeth
    'crown':        (0.97, 0.95, 0.90),  # Crown color
    'roots':        (0.88, 0.85, 0.80),  # Root color
    'middle':       (0.90, 0.87, 0.82),  # Middle parts
    'default':      (0.93, 0.90, 0.86),  # Default bone
}


def classify_dental_part(filename: str) -> str:
    """Classify dental part from filename"""
    name = filename.lower()
    
    # Layer-based classification (from your image)
    if '(1)' in name or 'crown' in name:
        return 'crown'
    elif '(2)' in name:
        return 'upper_jaw'
    elif '(3)' in name:
        return 'middle'
    elif '(4)' in name:
        return 'lower_jaw'
    elif '(5)' in name or 'root' in name:
        return 'roots'
    
    # General classification
    if 'upper' in name or 'maxilla' in name or 'superior' in name:
        return 'upper_jaw'
    elif 'lower' in name or 'mandible' in name or 'inferior' in name:
        return 'lower_jaw'
    elif 'teeth' in name or 'tooth' in name or 'dental' in name:
        if 'upper' in name or 'superior' in name:
            return 'teeth'
        elif 'lower' in name or 'inferior' in name:
            return 'teeth'
        return 'teeth'
    elif 'crown' in name:
        return 'crown'
    elif 'root' in name:
        return 'roots'
    
    return 'default'


class DentalOpacityControl(QtWidgets.QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.parts = []
        
        # Global opacity control
        self.global_opacity = 1.0
        
        self.setWindowTitle("🦷 Dental Opacity Control")
        self.resize(1800, 900)
        self.setStyleSheet(self._get_stylesheet())
        
        self._build_ui()
        QtCore.QTimer.singleShot(100, self._initialize)
    
    def _get_stylesheet(self):
        return """
            QMainWindow { background: #0a0a0a; }
            QWidget { background: #0a0a0a; color: #ffffff; font-family: 'Segoe UI', Arial; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white; border: none;
                padding: 12px 20px; border-radius: 8px;
                font-size: 13pt; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            QPushButton:pressed {
                background: #2980b9;
            }
            QLabel { color: #ffffff; font-size: 11pt; }
            QSlider::groove:horizontal {
                background: #2a2a2a; height: 8px; border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db; width: 20px; height: 20px;
                margin: -6px 0; border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #3498db; border-radius: 4px;
            }
            QGroupBox {
                background: #1a1a1a; border: 2px solid #2a2a2a;
                border-radius: 10px; padding: 15px; margin-top: 12px;
                color: #3498db; font-size: 13pt; font-weight: bold;
            }
            QListWidget {
                background: #1a1a1a; border: 2px solid #2a2a2a;
                border-radius: 8px; color: white; font-size: 10pt;
            }
            QListWidget::item {
                padding: 6px; border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #3498db; color: black;
            }
            QListWidget::item:hover {
                background: #2a2a2a;
            }
        """
    
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        central.setLayout(main_layout)
        
        # Control Panel
        panel = self._create_control_panel()
        main_layout.addWidget(panel)
        
        # Viewer
        viewer = QtWidgets.QWidget()
        viewer_layout = QtWidgets.QVBoxLayout()
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer.setLayout(viewer_layout)
        
        # Top bar
        top = QtWidgets.QFrame()
        top.setStyleSheet("background: #1a1a1a; border-bottom: 3px solid #3498db;")
        top.setFixedHeight(70)
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setContentsMargins(30, 10, 30, 10)
        top.setLayout(top_layout)
        
        title = QtWidgets.QLabel("🦷 Dental Model - Opacity Control")
        title.setStyleSheet("color: #3498db; font-size: 22pt; font-weight: 800;")
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        viewer_layout.addWidget(top)
        
        # Plotter
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background('#0a0a0a')
        viewer_layout.addWidget(self.plotter.interactor)
        
        main_layout.addWidget(viewer, 1)
    
    def _create_control_panel(self):
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(450)
        panel.setStyleSheet("background: #141414; border-right: 3px solid #3498db;")
        
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        content.setLayout(layout)
        
        # Title
        title = QtWidgets.QLabel("Opacity Control")
        title.setStyleSheet("color: #3498db; font-size: 20pt; font-weight: 800;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Global opacity control
        global_box = QtWidgets.QGroupBox("Global Opacity")
        global_layout = QtWidgets.QVBoxLayout()
        
        global_layout.addWidget(QtWidgets.QLabel("All Parts Opacity"))
        self.global_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.global_slider.setRange(0, 100)
        self.global_slider.setValue(100)
        self.global_slider.valueChanged.connect(self._update_global_opacity)
        global_layout.addWidget(self.global_slider)
        self.global_label = QtWidgets.QLabel("100%")
        self.global_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #3498db;")
        self.global_label.setAlignment(QtCore.Qt.AlignCenter)
        global_layout.addWidget(self.global_label)
        
        # Quick buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        btn_solid = QtWidgets.QPushButton("Solid")
        btn_solid.clicked.connect(lambda: self._set_global_opacity(100))
        btn_layout.addWidget(btn_solid)
        
        btn_half = QtWidgets.QPushButton("50%")
        btn_half.clicked.connect(lambda: self._set_global_opacity(50))
        btn_layout.addWidget(btn_half)
        
        btn_transparent = QtWidgets.QPushButton("Transparent")
        btn_transparent.clicked.connect(lambda: self._set_global_opacity(10))
        btn_layout.addWidget(btn_transparent)
        
        global_layout.addLayout(btn_layout)
        
        global_box.setLayout(global_layout)
        layout.addWidget(global_box)
        
        # Individual parts control
        parts_box = QtWidgets.QGroupBox("Individual Parts")
        parts_layout = QtWidgets.QVBoxLayout()
        
        parts_layout.addWidget(QtWidgets.QLabel("Select part to control:"))
        self.parts_list = QtWidgets.QListWidget()
        self.parts_list.itemSelectionChanged.connect(self._on_part_selected)
        parts_layout.addWidget(self.parts_list)
        
        # Individual opacity slider
        parts_layout.addWidget(QtWidgets.QLabel("Selected Part Opacity"))
        self.individual_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.individual_slider.setRange(0, 100)
        self.individual_slider.setValue(100)
        self.individual_slider.setEnabled(False)
        self.individual_slider.valueChanged.connect(self._update_individual_opacity)
        parts_layout.addWidget(self.individual_slider)
        self.individual_label = QtWidgets.QLabel("--")
        self.individual_label.setStyleSheet("font-size: 12pt; color: #ccc;")
        self.individual_label.setAlignment(QtCore.Qt.AlignCenter)
        parts_layout.addWidget(self.individual_label)
        
        parts_box.setLayout(parts_layout)
        layout.addWidget(parts_box)
        
        # View presets
        view_box = QtWidgets.QGroupBox("View Presets")
        view_layout = QtWidgets.QVBoxLayout()
        
        btn_front = QtWidgets.QPushButton("👁 Front View")
        btn_front.clicked.connect(self._view_front)
        view_layout.addWidget(btn_front)
        
        btn_side = QtWidgets.QPushButton("👁 Side View")
        btn_side.clicked.connect(self._view_side)
        view_layout.addWidget(btn_side)
        
        btn_top = QtWidgets.QPushButton("👁 Top View")
        btn_top.clicked.connect(self._view_top)
        view_layout.addWidget(btn_top)
        
        btn_reset = QtWidgets.QPushButton("🔄 Reset Camera")
        btn_reset.clicked.connect(self._reset_camera)
        view_layout.addWidget(btn_reset)
        
        view_box.setLayout(view_layout)
        layout.addWidget(view_box)
        
        # Layer visibility presets
        layer_box = QtWidgets.QGroupBox("Layer Visibility")
        layer_layout = QtWidgets.QVBoxLayout()
        
        btn_all = QtWidgets.QPushButton("Show All")
        btn_all.clicked.connect(self._show_all)
        layer_layout.addWidget(btn_all)
        
        btn_upper = QtWidgets.QPushButton("Upper Only")
        btn_upper.clicked.connect(self._show_upper_only)
        layer_layout.addWidget(btn_upper)
        
        btn_lower = QtWidgets.QPushButton("Lower Only")
        btn_lower.clicked.connect(self._show_lower_only)
        layer_layout.addWidget(btn_lower)
        
        btn_internal = QtWidgets.QPushButton("Internal View")
        btn_internal.clicked.connect(self._show_internal)
        layer_layout.addWidget(btn_internal)
        
        layer_box.setLayout(layer_layout)
        layout.addWidget(layer_box)
        
        # Info
        info_box = QtWidgets.QGroupBox("Info")
        info_layout = QtWidgets.QVBoxLayout()
        
        self.info_label = QtWidgets.QLabel(
            "🦷 Dental Model Viewer\n\n"
            "• Use mouse to rotate\n"
            "• Scroll to zoom\n"
            "• Control opacity globally or per part\n"
            "• Select parts from list"
        )
        self.info_label.setStyleSheet("color: #ccc; font-size: 10pt; line-height: 1.5;")
        info_layout.addWidget(self.info_label)
        
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)
        
        # Status
        self.status = QtWidgets.QLabel("Ready")
        self.status.setStyleSheet(
            "color: #3498db; font-size: 12pt; font-weight: bold; "
            "padding: 12px; background: #1a1a1a; border-radius: 8px;"
        )
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        p_layout = QtWidgets.QVBoxLayout()
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.addWidget(scroll)
        panel.setLayout(p_layout)
        
        return panel
    
    def _initialize(self):
        self.status.setText("⏳ Loading dental model...")
        QtWidgets.QApplication.processEvents()
        
        self._load_meshes()
        self._setup_scene()
        self._update_parts_list()
        
        self.status.setText(f"✅ Loaded {len(self.parts)} parts")
    
    def _load_meshes(self):
        """Load dental meshes"""
        loaded = 0
        for path in self.files:
            try:
                mesh = pv.read(path)
                if mesh.n_points == 0:
                    continue
                
                mesh = mesh.clean()
                mesh = mesh.compute_normals(auto_orient_normals=True)
                
                name = os.path.basename(path)
                region = classify_dental_part(name)
                color = DENTAL_COLORS.get(region, DENTAL_COLORS['default'])
                
                self.parts.append({
                    'name': name,
                    'mesh': mesh,
                    'color': color,
                    'region': region,
                    'opacity': 1.0,
                    'actor': None,
                    'visible': True
                })
                
                loaded += 1
                
            except Exception as e:
                print(f"Error loading {path}: {e}")
        
        print(f"✅ Loaded {loaded} dental parts")
    
    def _setup_scene(self):
        """Setup 3D scene"""
        for part in self.parts:
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=1.0,
                smooth_shading=True,
                ambient=0.4,
                diffuse=0.6,
                specular=0.3,
                specular_power=30
            )
            part['actor'] = actor
        
        # Lighting
        self.plotter.remove_all_lights()
        
        light1 = pv.Light(position=(0, -400, 300), light_type='scene light')
        light1.intensity = 1.2
        self.plotter.add_light(light1)
        
        light2 = pv.Light(position=(300, -200, 200), light_type='scene light')
        light2.intensity = 0.6
        self.plotter.add_light(light2)
        
        light3 = pv.Light(position=(0, 200, 100), light_type='scene light')
        light3.intensity = 0.4
        self.plotter.add_light(light3)
        
        # Camera
        self._reset_camera()
        
        print("✅ Scene ready")
    
    def _update_parts_list(self):
        """Update parts list"""
        self.parts_list.clear()
        for i, part in enumerate(self.parts):
            opacity_percent = int(part['opacity'] * 100)
            item_text = f"{part['region']} - {opacity_percent}% - {part['name']}"
            self.parts_list.addItem(item_text)
    
    def _update_global_opacity(self, value):
        """Update all parts opacity"""
        opacity = value / 100.0
        self.global_opacity = opacity
        self.global_label.setText(f"{value}%")
        
        for part in self.parts:
            part['opacity'] = opacity
            if part['actor']:
                part['actor'].GetProperty().SetOpacity(opacity)
        
        self.plotter.render()
        self._update_parts_list()
    
    def _set_global_opacity(self, value):
        """Set global opacity to specific value"""
        self.global_slider.setValue(value)
    
    def _on_part_selected(self):
        """When a part is selected from list"""
        selected_items = self.parts_list.selectedItems()
        if not selected_items:
            self.individual_slider.setEnabled(False)
            self.individual_label.setText("--")
            return
        
        # Get selected part index
        index = self.parts_list.row(selected_items[0])
        part = self.parts[index]
        
        # Update individual slider
        opacity_value = int(part['opacity'] * 100)
        self.individual_slider.setEnabled(True)
        self.individual_slider.setValue(opacity_value)
        self.individual_label.setText(f"{opacity_value}% - {part['region']}")
    
    def _update_individual_opacity(self, value):
        """Update selected part opacity"""
        selected_items = self.parts_list.selectedItems()
        if not selected_items:
            return
        
        index = self.parts_list.row(selected_items[0])
        part = self.parts[index]
        
        opacity = value / 100.0
        part['opacity'] = opacity
        
        if part['actor']:
            part['actor'].GetProperty().SetOpacity(opacity)
        
        self.individual_label.setText(f"{value}% - {part['region']}")
        self.plotter.render()
        self._update_parts_list()
    
    def _reset_camera(self):
        """Reset camera to default view"""
        self.plotter.reset_camera()
        bounds = self.plotter.bounds
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2
        cz = (bounds[4] + bounds[5]) / 2
        
        self.plotter.camera.position = (cx, cy - 300, cz + 100)
        self.plotter.camera.focal_point = (cx, cy, cz)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.render()
    
    def _view_front(self):
        """Front view"""
        bounds = self.plotter.bounds
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2
        cz = (bounds[4] + bounds[5]) / 2
        
        self.plotter.camera.position = (cx, cy - 400, cz)
        self.plotter.camera.focal_point = (cx, cy, cz)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.render()
    
    def _view_side(self):
        """Side view"""
        bounds = self.plotter.bounds
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2
        cz = (bounds[4] + bounds[5]) / 2
        
        self.plotter.camera.position = (cx + 400, cy, cz)
        self.plotter.camera.focal_point = (cx, cy, cz)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.render()
    
    def _view_top(self):
        """Top view"""
        bounds = self.plotter.bounds
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2
        cz = (bounds[4] + bounds[5]) / 2
        
        self.plotter.camera.position = (cx, cy, cz + 400)
        self.plotter.camera.focal_point = (cx, cy, cz)
        self.plotter.camera.up = (0, 1, 0)
        self.plotter.render()
    
    def _show_all(self):
        """Show all parts"""
        for part in self.parts:
            part['opacity'] = 1.0
            if part['actor']:
                part['actor'].GetProperty().SetOpacity(1.0)
        self.global_slider.setValue(100)
        self.plotter.render()
        self._update_parts_list()
    
    def _show_upper_only(self):
        """Show only upper jaw parts"""
        for part in self.parts:
            if part['region'] in ['upper_jaw', 'crown', 'teeth']:
                part['opacity'] = 1.0
                if part['actor']:
                    part['actor'].GetProperty().SetOpacity(1.0)
            else:
                part['opacity'] = 0.1
                if part['actor']:
                    part['actor'].GetProperty().SetOpacity(0.1)
        self.plotter.render()
        self._update_parts_list()
    
    def _show_lower_only(self):
        """Show only lower jaw parts"""
        for part in self.parts:
            if part['region'] in ['lower_jaw', 'roots']:
                part['opacity'] = 1.0
                if part['actor']:
                    part['actor'].GetProperty().SetOpacity(1.0)
            else:
                part['opacity'] = 0.1
                if part['actor']:
                    part['actor'].GetProperty().SetOpacity(0.1)
        self.plotter.render()
        self._update_parts_list()
    
    def _show_internal(self):
        """Show internal structure (make outer parts transparent)"""
        for part in self.parts:
            if part['region'] in ['crown', 'upper_jaw']:
                part['opacity'] = 0.3
                if part['actor']:
                    part['actor'].GetProperty().SetOpacity(0.3)
            elif part['region'] in ['roots', 'middle']:
                part['opacity'] = 1.0
                if part['actor']:
                    part['actor'].GetProperty().SetOpacity(1.0)
            else:
                part['opacity'] = 0.5
                if part['actor']:
                    part['actor'].GetProperty().SetOpacity(0.5)
        self.plotter.render()
        self._update_parts_list()


def main():
    print("\n" + "="*70)
    print("🦷 DENTAL OPACITY CONTROL")
    print("="*70)
    print("Simple dental model viewer with opacity control")
    print("  • Control global opacity for all parts")
    print("  • Control individual part opacity")
    print("  • Quick view presets (Front, Side, Top)")
    print("  • Layer visibility presets")
    print("="*70)
    
    current_dir = os.getcwd()
    path = os.path.join(current_dir, "dentaldataset.obj")
    
    if not os.path.exists(path):
        print(f"\n❌ Folder not found: {path}\n")
        return
    
    files = glob.glob(os.path.join(path, "*.obj"))
    files.extend(glob.glob(os.path.join(path, "*.OBJ")))
    files = sorted(list(set(files)))
    
    if not files:
        print("\n❌ No .obj files found\n")
        return
    
    print(f"\n✅ Found {len(files)} dental files")
    print("🚀 Launching dental opacity control...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = DentalOpacityControl(files)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()