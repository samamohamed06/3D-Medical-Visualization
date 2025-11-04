import os
import glob
import numpy as np
import pyvista as pv
from PyQt5 import QtWidgets, QtCore
from pyvistaqt import BackgroundPlotter
import sys

"""
🦷 Dental Jaw Movement - Upper and Lower Jaw Animation
Realistic jaw opening and closing movement (VERTICAL MOVEMENT)
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

# Jaw movement configuration
JAW_MOVEMENT = {
    'upper_jaw': {
        'moves': True,
        'movement_type': 'upper_jaw_open',
        'max_displacement': 3.0,  # mm upward
        'frequency': 0.5,
        'direction': 'up'
    },
    'lower_jaw': {
        'moves': True,
        'movement_type': 'lower_jaw_open',
        'max_displacement': 15.0,  # mm downward (main movement)
        'frequency': 0.5,
        'direction': 'down'
    },
    'teeth_upper': {
        'moves': True,
        'movement_type': 'follow_upper',
        'max_displacement': 3.0,
        'frequency': 0.5,
        'direction': 'up'
    },
    'teeth_lower': {
        'moves': True,
        'movement_type': 'follow_lower',
        'max_displacement': 15.0,
        'frequency': 0.5,
        'direction': 'down'
    },
    'crown': {
        'moves': True,
        'movement_type': 'follow_upper',
        'max_displacement': 3.0,
        'frequency': 0.5,
        'direction': 'up'
    },
    'roots': {
        'moves': True,
        'movement_type': 'follow_upper',
        'max_displacement': 3.0,
        'frequency': 0.5,
        'direction': 'up'
    },
    'middle': {
        'moves': False,
        'movement_type': 'fixed',
    },
    'default': {
        'moves': False,
        'movement_type': 'fixed',
    }
}


def classify_dental_part(filename: str) -> str:
    """Classify dental part from filename"""
    name = filename.lower()
    
    # Layer-based classification
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
            return 'teeth_upper'
        elif 'lower' in name or 'inferior' in name:
            return 'teeth_lower'
        return 'teeth_upper'
    elif 'crown' in name:
        return 'crown'
    elif 'root' in name:
        return 'roots'
    
    return 'default'


def get_movement_config(region: str):
    """Get movement configuration for dental part"""
    return JAW_MOVEMENT.get(region, JAW_MOVEMENT['default'])


class DentalJawMovement(QtWidgets.QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.parts = []
        
        # Animation
        self.is_animating = False
        self.time = 0.0
        
        # Global controls
        self.movement_enabled = True
        self.global_amplitude = 1.0
        self.speed_factor = 1.0
        
        # Store originals
        self.original_positions = {}
        self.original_centers = {}
        
        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_movement)
        self.timer.setInterval(33)
        
        self.setWindowTitle("🦷 Dental Jaw Movement")
        self.resize(1600, 900)
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
                padding: 14px 24px; border-radius: 10px;
                font-size: 14pt; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            QLabel { color: #ffffff; font-size: 12pt; }
            QSlider::groove:horizontal {
                background: #2a2a2a; height: 10px; border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #3498db; width: 24px; height: 24px;
                margin: -7px 0; border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #3498db; border-radius: 5px;
            }
            QGroupBox {
                background: #1a1a1a; border: 2px solid #2a2a2a;
                border-radius: 12px; padding: 18px; margin-top: 15px;
                color: #3498db; font-size: 14pt; font-weight: bold;
            }
            QListWidget {
                background: #1a1a1a; border: 2px solid #2a2a2a;
                border-radius: 8px; color: white; font-size: 11pt;
            }
            QListWidget::item {
                padding: 8px; border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #3498db; color: black;
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
        
        title = QtWidgets.QLabel("🦷 Dental Jaw Movement - Open & Close Animation")
        title.setStyleSheet("color: #3498db; font-size: 20pt; font-weight: 800;")
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
        panel.setFixedWidth(400)
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
        title = QtWidgets.QLabel("Jaw Control")
        title.setStyleSheet("color: #3498db; font-size: 20pt; font-weight: 800;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Main control
        main_box = QtWidgets.QGroupBox("Animation Control")
        main_layout = QtWidgets.QVBoxLayout()
        
        self.btn_play = QtWidgets.QPushButton("▶ START JAW MOVEMENT")
        self.btn_play.clicked.connect(self._toggle)
        main_layout.addWidget(self.btn_play)
        
        btn_reset = QtWidgets.QPushButton("🔄 RESET TO CLOSED")
        btn_reset.clicked.connect(self._reset)
        main_layout.addWidget(btn_reset)
        
        main_box.setLayout(main_layout)
        layout.addWidget(main_box)
        
        # Movement settings
        settings_box = QtWidgets.QGroupBox("Movement Settings")
        settings_layout = QtWidgets.QVBoxLayout()
        
        settings_layout.addWidget(QtWidgets.QLabel("Opening Distance"))
        self.amp_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.amp_slider.setRange(0, 200)
        self.amp_slider.setValue(100)
        self.amp_slider.valueChanged.connect(self._update_amplitude)
        settings_layout.addWidget(self.amp_slider)
        self.amp_label = QtWidgets.QLabel("100%")
        self.amp_label.setAlignment(QtCore.Qt.AlignCenter)
        settings_layout.addWidget(self.amp_label)
        
        settings_layout.addWidget(QtWidgets.QLabel("Animation Speed"))
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed_slider.setRange(1, 30)
        self.speed_slider.setValue(10)
        self.speed_slider.valueChanged.connect(self._update_speed)
        settings_layout.addWidget(self.speed_slider)
        self.speed_label = QtWidgets.QLabel("1.0x")
        self.speed_label.setAlignment(QtCore.Qt.AlignCenter)
        settings_layout.addWidget(self.speed_label)
        
        settings_box.setLayout(settings_layout)
        layout.addWidget(settings_box)
        
        # Movement info
        info_box = QtWidgets.QGroupBox("Movement Info")
        info_layout = QtWidgets.QVBoxLayout()
        
        info_text = QtWidgets.QLabel(
            "🦷 Realistic Jaw Movement:\n\n"
            "🔵 Upper Jaw: Slight upward movement\n"
            "🔵 Lower Jaw: Main downward movement\n"
            "⚪ Middle Parts: Fixed (hinge point)\n\n"
            "Natural vertical opening/closing"
        )
        info_text.setStyleSheet("color: #ccc; font-size: 10pt; line-height: 1.4;")
        info_layout.addWidget(info_text)
        
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)
        
        # Parts list
        parts_box = QtWidgets.QGroupBox("Dental Parts")
        parts_layout = QtWidgets.QVBoxLayout()
        
        self.parts_list = QtWidgets.QListWidget()
        parts_layout.addWidget(self.parts_list)
        
        parts_box.setLayout(parts_layout)
        layout.addWidget(parts_box)
        
        # Status
        self.status = QtWidgets.QLabel("Ready")
        self.status.setStyleSheet(
            "color: #3498db; font-size: 13pt; font-weight: bold; "
            "padding: 15px; background: #1a1a1a; border-radius: 10px;"
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
        
        self.status.setText("✅ Ready! Press START")
    
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
                movement_config = get_movement_config(region)
                
                self.parts.append({
                    'name': name,
                    'mesh': mesh,
                    'color': color,
                    'region': region,
                    'original_center': np.array(mesh.center),
                    'movement_config': movement_config,
                    'actor': None
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
            
            self.original_positions[part['name']] = part['mesh'].points.copy()
            self.original_centers[part['name']] = part['original_center'].copy()
        
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
        self.plotter.reset_camera()
        bounds = self.plotter.bounds
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2
        cz = (bounds[4] + bounds[5]) / 2
        
        self.plotter.camera.position = (cx, cy - 300, cz + 100)
        self.plotter.camera.focal_point = (cx, cy, cz)
        self.plotter.camera.up = (0, 0, 1)
        
        print("✅ Scene ready")
    
    def _update_parts_list(self):
        """Update parts list"""
        self.parts_list.clear()
        for part in self.parts:
            config = part['movement_config']
            if config.get('moves', False):
                icon = "🟢" if 'jaw' in part['region'] else "🔵"
                move_type = config.get('movement_type', 'moving')
                item_text = f"{icon} {part['region']}: {move_type}"
            else:
                icon = "⚪"
                item_text = f"{icon} {part['region']}: fixed"
            self.parts_list.addItem(item_text)
    
    def _toggle(self):
        """Toggle animation"""
        if self.is_animating:
            self.is_animating = False
            self.timer.stop()
            self.btn_play.setText("▶ START JAW MOVEMENT")
            self.status.setText("⏸ Paused")
        else:
            self.is_animating = True
            self.timer.start()
            self.btn_play.setText("⏸ PAUSE")
            self.status.setText("▶ Jaw opening & closing...")
    
    def _update_movement(self):
        """Update jaw movement - VERTICAL MOVEMENT (up/down)"""
        if not self.is_animating:
            return
        
        dt = 0.033
        self.time += dt * self.speed_factor
        
        # Smooth cycle (0 = closed, 1 = fully open, back to 0)
        cycle = (np.sin(2 * np.pi * 0.5 * self.time) + 1) / 2
        
        for part in self.parts:
            config = part['movement_config']
            
            if not config.get('moves', False):
                continue
            
            orig_points = self.original_positions[part['name']]
            movement_type = config.get('movement_type', 'fixed')
            max_displacement = config.get('max_displacement', 0) * self.global_amplitude
            
            # Current displacement based on cycle
            current_displacement = max_displacement * cycle
            
            new_points = orig_points.copy()
            
            # VERTICAL MOVEMENT - changing Z coordinate
            if movement_type in ['upper_jaw_open', 'follow_upper']:
                # Upper jaw moves UP (positive Z direction)
                new_points[:, 2] += current_displacement
                
            elif movement_type in ['lower_jaw_open', 'follow_lower']:
                # Lower jaw moves DOWN (negative Z direction)
                new_points[:, 2] -= current_displacement
            
            # Update mesh
            part['mesh'].points = new_points
            part['mesh'].compute_normals(auto_orient_normals=True, inplace=True)
        
        self.plotter.render()
    
    def _reset(self):
        """Reset to closed position"""
        for part in self.parts:
            part['mesh'].points = self.original_positions[part['name']].copy()
            part['mesh'].compute_normals(auto_orient_normals=True, inplace=True)
        
        self.time = 0.0
        self.plotter.render()
        self.status.setText("🔄 Reset to closed position")
    
    def _update_amplitude(self, val):
        """Update opening distance"""
        self.global_amplitude = val / 100.0
        self.amp_label.setText(f"{val}%")
    
    def _update_speed(self, val):
        """Update animation speed"""
        self.speed_factor = val / 10.0
        self.speed_label.setText(f"{val/10.0:.1f}x")


def main():
    print("\n" + "="*70)
    print("🦷 DENTAL JAW MOVEMENT - VERTICAL OPEN/CLOSE")
    print("="*70)
    print("Realistic vertical jaw movement:")
    print("  🔵 Upper Jaw: Moves UP (+Z direction)")
    print("  🔵 Lower Jaw: Moves DOWN (-Z direction)")
    print("  ⚪ Middle Parts: Fixed hinge point")
    print("  Simple linear up/down displacement - NO rotation!")
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
    print("🚀 Launching vertical jaw movement...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = DentalJawMovement(files)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()