import os
import glob
import numpy as np
import pyvista as pv
from PyQt5 import QtWidgets, QtCore
from pyvistaqt import BackgroundPlotter
import sys

"""
🦴 Spinal Cord & Muscles Movement - Complete Anatomical Movement
Vertebrae, Spinal Cord, and Surrounding Muscles moving in harmony
"""

# Solid colors for anatomical parts
ANATOMICAL_COLORS = {
    # Spinal structures
    'spinal': (0.95, 0.75, 0.78),      # Pink - Spinal cord
    'vertebra': (0.95, 0.90, 0.80),    # Bone color - Vertebrae
    'vertebrae': (0.95, 0.90, 0.80),   # Bone color - Vertebrae
    
    # Major muscle groups
    'trapezius': (0.85, 0.40, 0.35),   # Deep red
    'latissimus': (0.75, 0.35, 0.30),  # Dark red
    'erector': (0.90, 0.45, 0.40),     # Red
    'multifidus': (0.80, 0.38, 0.35),  # Medium red
    'semispinalis': (0.88, 0.42, 0.38),# Light red
    'rhomboid': (0.82, 0.48, 0.45),    # Pinkish red
    'serratus': (0.78, 0.50, 0.48),    # Light pink
    'muscle': (0.85, 0.45, 0.40),      # Default muscle red
    
    # Default
    'default': (0.90, 0.90, 0.90),     # Gray
}

# Movement configurations for different anatomical parts
MOVING_PARTS = {
    # Spinal cord - Central nervous system
    'spinal': {
        'moves': True,
        'movement_type': 'subtle_pulse',
        'amplitude': 3.0,
        'frequency': 0.6
    },
    
    # Vertebrae - Support structure
    'vertebra': {
        'moves': True,
        'movement_type': 'gentle_sway',
        'amplitude': 2.5,
        'frequency': 0.5
    },
    
    'vertebrae': {
        'moves': True,
        'movement_type': 'gentle_sway',
        'amplitude': 2.5,
        'frequency': 0.5
    },
    
    # Deep back muscles - Trapezius
    'trapezius': {
        'moves': True,
        'movement_type': 'wave',
        'amplitude': 6.0,
        'frequency': 0.8
    },
    
    # Latissimus dorsi - Large back muscle
    'latissimus': {
        'moves': True,
        'movement_type': 'breathing',
        'amplitude': 7.0,
        'frequency': 0.4
    },
    
    # Erector spinae - Spinal support
    'erector': {
        'moves': True,
        'movement_type': 'pulsation',
        'amplitude': 5.5,
        'frequency': 0.9
    },
    
    # Multifidus - Deep spinal muscles
    'multifidus': {
        'moves': True,
        'movement_type': 'oscillate',
        'amplitude': 4.5,
        'frequency': 1.0
    },
    
    # Semispinalis - Neck and upper back
    'semispinalis': {
        'moves': True,
        'movement_type': 'gentle_wave',
        'amplitude': 5.0,
        'frequency': 0.7
    },
    
    # Rhomboid muscles
    'rhomboid': {
        'moves': True,
        'movement_type': 'gentle_pulse',
        'amplitude': 4.8,
        'frequency': 0.85
    },
    
    # Serratus muscles
    'serratus': {
        'moves': True,
        'movement_type': 'wave',
        'amplitude': 5.2,
        'frequency': 0.75
    },
    
    # Generic muscle
    'muscle': {
        'moves': True,
        'movement_type': 'breathing',
        'amplitude': 5.5,
        'frequency': 0.6
    },
    
    # Default for any other parts
    'default': {
        'moves': True,
        'movement_type': 'subtle_wave',
        'amplitude': 4.0,
        'frequency': 0.85
    }
}


def is_surface_part(filename: str) -> bool:
    """Check if file is a surface anatomical part"""
    name = filename.lower()
    surface_keywords = [
        'spinal', 'vertebra', 'vertebrae', 'muscle', 'muscl',
        'trapezius', 'latissimus', 'erector', 'multifidus',
        'semispinalis', 'rhomboid', 'serratus', 'dorsi',
        'cervical', 'thoracic', 'lumbar', 'sacral'
    ]
    return any(keyword in name for keyword in surface_keywords)


def classify_region(filename: str) -> str:
    """Classify anatomical region from filename"""
    low = filename.lower()
    
    # Check for specific muscle names first
    muscle_names = ['trapezius', 'latissimus', 'erector', 'multifidus', 
                    'semispinalis', 'rhomboid', 'serratus']
    for muscle in muscle_names:
        if muscle in low:
            return muscle
    
    # Check for general categories
    if 'spinal' in low or 'cord' in low:
        return 'spinal'
    if 'vertebra' in low or 'vertebrae' in low:
        return 'vertebrae'
    if 'muscle' in low or 'muscl' in low:
        return 'muscle'
    
    return 'default'


def get_movement_config(region: str):
    """Get movement configuration - ALL regions move"""
    return MOVING_PARTS.get(region, MOVING_PARTS['default'])


class CompleteSpinalMovement(QtWidgets.QMainWindow):
    def __init__(self, spinal_files, muscle_files):
        super().__init__()
        self.spinal_files = spinal_files
        self.muscle_files = muscle_files
        self.parts = []
        
        # Animation
        self.is_animating = False
        self.time = 0.0
        
        # Global controls - Defaults: 35% amplitude, 0.8x speed
        self.movement_enabled = True
        self.global_amplitude = 0.35
        self.speed_factor = 0.8
        
        # Store originals
        self.original_positions = {}
        self.original_centers = {}
        
        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_movement)
        self.timer.setInterval(33)
        
        self.setWindowTitle("🦴 Spinal Cord & Muscles Movement")
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
                    stop:0 #ff6b6b, stop:1 #ee5a52);
                color: white; border: none;
                padding: 14px 24px; border-radius: 10px;
                font-size: 14pt; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8787, stop:1 #ff6b6b);
            }
            QLabel { color: #ffffff; font-size: 12pt; }
            QSlider::groove:horizontal {
                background: #2a2a2a; height: 10px; border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #ff6b6b; width: 24px; height: 24px;
                margin: -7px 0; border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #ff6b6b; border-radius: 5px;
            }
            QGroupBox {
                background: #1a1a1a; border: 2px solid #2a2a2a;
                border-radius: 12px; padding: 18px; margin-top: 15px;
                color: #ff6b6b; font-size: 14pt; font-weight: bold;
            }
            QListWidget {
                background: #1a1a1a; border: 2px solid #2a2a2a;
                border-radius: 8px; color: white; font-size: 11pt;
            }
            QListWidget::item {
                padding: 8px; border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #ff6b6b; color: black;
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
        top.setStyleSheet("background: #1a1a1a; border-bottom: 3px solid #ff6b6b;")
        top.setFixedHeight(70)
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setContentsMargins(30, 10, 30, 10)
        top.setLayout(top_layout)
        
        title = QtWidgets.QLabel("🦴 Spinal Cord & Muscles Movement (All Parts Active)")
        title.setStyleSheet("color: #ff6b6b; font-size: 20pt; font-weight: 800;")
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        viewer_layout.addWidget(top)
        
        # Plotter
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background('#000000')
        viewer_layout.addWidget(self.plotter.interactor)
        
        main_layout.addWidget(viewer, 1)
    
    def _create_control_panel(self):
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(400)
        panel.setStyleSheet("background: #141414; border-right: 3px solid #ff6b6b;")
        
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        content.setLayout(layout)
        
        # Title
        title = QtWidgets.QLabel("Movement Control")
        title.setStyleSheet("color: #ff6b6b; font-size: 20pt; font-weight: 800;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Main control
        main_box = QtWidgets.QGroupBox("Main Control")
        main_layout = QtWidgets.QVBoxLayout()
        
        self.btn_play = QtWidgets.QPushButton("▶ START MOVEMENT")
        self.btn_play.clicked.connect(self._toggle)
        main_layout.addWidget(self.btn_play)
        
        btn_reset = QtWidgets.QPushButton("🔄 RESET")
        btn_reset.clicked.connect(self._reset)
        main_layout.addWidget(btn_reset)
        
        main_box.setLayout(main_layout)
        layout.addWidget(main_box)
        
        # Global settings
        global_box = QtWidgets.QGroupBox("Global Settings")
        global_layout = QtWidgets.QVBoxLayout()
        
        global_layout.addWidget(QtWidgets.QLabel("Movement Amplitude"))
        self.amp_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.amp_slider.setRange(0, 200)
        self.amp_slider.setValue(35)
        self.amp_slider.valueChanged.connect(self._update_amplitude)
        global_layout.addWidget(self.amp_slider)
        self.amp_label = QtWidgets.QLabel("35%")
        self.amp_label.setAlignment(QtCore.Qt.AlignCenter)
        global_layout.addWidget(self.amp_label)
        
        global_layout.addWidget(QtWidgets.QLabel("Speed"))
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed_slider.setRange(1, 20)
        self.speed_slider.setValue(8)
        self.speed_slider.valueChanged.connect(self._update_speed)
        global_layout.addWidget(self.speed_slider)
        self.speed_label = QtWidgets.QLabel("0.8x")
        self.speed_label.setAlignment(QtCore.Qt.AlignCenter)
        global_layout.addWidget(self.speed_label)
        
        global_box.setLayout(global_layout)
        layout.addWidget(global_box)
        
        # Moving parts info
        info_box = QtWidgets.QGroupBox("Active Movements")
        info_layout = QtWidgets.QVBoxLayout()
        
        info_text = QtWidgets.QLabel(
            "🟢 ALL parts are active!\n\n"
            "🔴 Trapezius: Wave\n"
            "🔴 Latissimus: Breathing\n"
            "🔴 Erector: Pulsation\n"
            "🔴 Multifidus: Oscillation\n"
            "🟠 Semispinalis: Gentle wave\n"
            "🟠 Rhomboid: Gentle pulse\n"
            "🟠 Serratus: Wave\n"
            "🟣 Spinal cord: Subtle pulse\n"
            "🟤 Vertebrae: Gentle sway"
        )
        info_text.setStyleSheet("color: #ccc; font-size: 10pt; line-height: 1.4;")
        info_layout.addWidget(info_text)
        
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)
        
        # Parts list
        parts_box = QtWidgets.QGroupBox("All Parts")
        parts_layout = QtWidgets.QVBoxLayout()
        
        self.parts_list = QtWidgets.QListWidget()
        parts_layout.addWidget(self.parts_list)
        
        parts_box.setLayout(parts_layout)
        layout.addWidget(parts_box)
        
        # Status
        self.status = QtWidgets.QLabel("Ready")
        self.status.setStyleSheet(
            "color: #ff6b6b; font-size: 13pt; font-weight: bold; "
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
        self.status.setText("⏳ Loading anatomy...")
        QtWidgets.QApplication.processEvents()
        
        self._load_meshes()
        self._setup_scene()
        self._update_parts_list()
        
        self.status.setText("✅ Ready! Press START")
    
    def _load_meshes(self):
        loaded = 0
        
        # Load spinal cord files
        for path in self.spinal_files:
            if not is_surface_part(os.path.basename(path)):
                continue
            
            try:
                mesh = pv.read(path)
                if mesh.n_points == 0:
                    continue
                
                mesh = mesh.clean()
                mesh = mesh.compute_normals(auto_orient_normals=True)
                
                name = os.path.basename(path)
                region = classify_region(name)
                color = ANATOMICAL_COLORS.get(region, ANATOMICAL_COLORS['default'])
                movement_config = get_movement_config(region)
                
                self.parts.append({
                    'name': name,
                    'mesh': mesh,
                    'color': color,
                    'region': region,
                    'original_center': np.array(mesh.center),
                    'movement_config': movement_config,
                    'actor': None,
                    'type': 'spinal'
                })
                
                loaded += 1
                
            except Exception as e:
                print(f"Error loading spinal file: {e}")
        
        # Load muscle files
        for path in self.muscle_files:
            if not is_surface_part(os.path.basename(path)):
                continue
            
            try:
                mesh = pv.read(path)
                if mesh.n_points == 0:
                    continue
                
                mesh = mesh.clean()
                mesh = mesh.compute_normals(auto_orient_normals=True)
                
                name = os.path.basename(path)
                region = classify_region(name)
                color = ANATOMICAL_COLORS.get(region, ANATOMICAL_COLORS['muscle'])
                movement_config = get_movement_config(region)
                
                self.parts.append({
                    'name': name,
                    'mesh': mesh,
                    'color': color,
                    'region': region,
                    'original_center': np.array(mesh.center),
                    'movement_config': movement_config,
                    'actor': None,
                    'type': 'muscle'
                })
                
                loaded += 1
                
            except Exception as e:
                print(f"Error loading muscle file: {e}")
        
        print(f"✅ Loaded {loaded} parts (ALL moving)")
    
    def _setup_scene(self):
        """Setup scene - SOLID meshes"""
        for part in self.parts:
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=1.0,
                smooth_shading=True,
                ambient=0.35,
                diffuse=0.75,
                specular=0.25,
                specular_power=20
            )
            part['actor'] = actor
            
            self.original_positions[part['name']] = part['mesh'].points.copy()
            self.original_centers[part['name']] = part['original_center'].copy()
        
        # Lighting
        self.plotter.remove_all_lights()
        
        light1 = pv.Light(position=(600, 600, 800), light_type='scene light')
        light1.intensity = 0.9
        self.plotter.add_light(light1)
        
        light2 = pv.Light(position=(-600, -600, 600), light_type='scene light')
        light2.intensity = 0.5
        self.plotter.add_light(light2)
        
        light3 = pv.Light(position=(0, 0, -600), light_type='scene light')
        light3.intensity = 0.4
        self.plotter.add_light(light3)
        
        # Camera
        self.plotter.reset_camera()
        bounds = self.plotter.bounds
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2
        cz = (bounds[4] + bounds[5]) / 2
        
        self.plotter.camera.position = (cx + 100, cy - 450, cz + 80)
        self.plotter.camera.focal_point = (cx, cy, cz)
        self.plotter.camera.up = (0, 0, 1)
        
        print("✅ Scene ready")
    
    def _update_parts_list(self):
        """Update parts list - ALL moving"""
        self.parts_list.clear()
        for part in self.parts:
            config = part['movement_config']
            icon = "🟢"
            move_type = config.get('movement_type', 'moving')
            part_type = part['type']
            item_text = f"{icon} [{part_type}] {part['region']}: {move_type}"
            self.parts_list.addItem(item_text)
    
    def _toggle(self):
        if self.is_animating:
            self.is_animating = False
            self.timer.stop()
            self.btn_play.setText("▶ START MOVEMENT")
            self.status.setText("⏸ Paused")
        else:
            self.is_animating = True
            self.timer.start()
            self.btn_play.setText("⏸ PAUSE")
            self.status.setText("▶ All parts moving...")
    
    def _update_movement(self):
        """Update ALL parts with different movement types"""
        if not self.is_animating:
            return
        
        dt = 0.033
        self.time += dt * self.speed_factor
        
        for part in self.parts:
            config = part['movement_config']
            
            orig_points = self.original_positions[part['name']]
            orig_center = self.original_centers[part['name']]
            
            movement_type = config.get('movement_type', 'subtle_wave')
            amplitude = config.get('amplitude', 4.0) * self.global_amplitude
            frequency = config.get('frequency', 0.85)
            
            new_points = orig_points.copy()
            
            # Different movement types
            if movement_type == 'pulsation':
                factor = np.sin(2 * np.pi * frequency * self.time)
                vectors = new_points - orig_center
                scale = 1.0 + (factor * amplitude / 100.0)
                new_points = orig_center + vectors * scale
                
            elif movement_type == 'gentle_wave':
                wave = np.sin(2 * np.pi * frequency * self.time)
                new_points[:, 2] += wave * amplitude * 0.5
                new_points[:, 0] += wave * amplitude * 0.3
                
            elif movement_type == 'wave':
                wave = np.sin(2 * np.pi * frequency * self.time)
                new_points[:, 0] += wave * amplitude
                new_points[:, 2] += wave * amplitude * 0.5
                
            elif movement_type == 'subtle_pulse':
                pulse = np.sin(2 * np.pi * frequency * self.time)
                vectors = new_points - orig_center
                scale = 1.0 + (pulse * amplitude / 200.0)
                new_points = orig_center + vectors * scale
                
            elif movement_type == 'oscillate':
                osc = np.sin(2 * np.pi * frequency * self.time)
                new_points[:, 0] += osc * amplitude
                new_points[:, 1] += osc * amplitude * 0.3
                
            elif movement_type == 'breathing':
                breath = np.sin(2 * np.pi * frequency * self.time)
                new_points[:, 2] += breath * amplitude
                vectors = new_points - orig_center
                scale = 1.0 + (breath * amplitude / 300.0)
                new_points = orig_center + vectors * scale
                
            elif movement_type == 'gentle_pulse':
                pulse = np.sin(2 * np.pi * frequency * self.time)
                vectors = new_points - orig_center
                scale = 1.0 + (pulse * amplitude / 150.0)
                new_points = orig_center + vectors * scale
                
            elif movement_type == 'gentle_sway':
                sway = np.sin(2 * np.pi * frequency * self.time)
                new_points[:, 0] += sway * amplitude * 0.3
                new_points[:, 1] += sway * amplitude * 0.2
                
            elif movement_type == 'subtle_wave':
                wave = np.sin(2 * np.pi * frequency * self.time)
                new_points[:, 2] += wave * amplitude * 0.4
                new_points[:, 1] += wave * amplitude * 0.2
            
            # Update mesh
            part['mesh'].points = new_points
            part['mesh'].compute_normals(auto_orient_normals=True, inplace=True)
        
        self.plotter.render()
    
    def _reset(self):
        """Reset all parts"""
        for part in self.parts:
            part['mesh'].points = self.original_positions[part['name']].copy()
            part['mesh'].compute_normals(auto_orient_normals=True, inplace=True)
        
        self.time = 0.0
        self.plotter.render()
        self.status.setText("🔄 Reset")
    
    def _update_amplitude(self, val):
        self.global_amplitude = val / 100.0
        self.amp_label.setText(f"{val}%")
    
    def _update_speed(self, val):
        self.speed_factor = val / 10.0
        self.speed_label.setText(f"{val/10.0:.1f}x")


def main():
    print("\n" + "="*70)
    print("🦴 SPINAL CORD & MUSCLES MOVEMENT")
    print("="*70)
    print("ALL anatomical parts move in coordinated harmony:")
    print("  🔴 Trapezius: Wave motion")
    print("  🔴 Latissimus dorsi: Breathing motion")
    print("  🔴 Erector spinae: Pulsation")
    print("  🔴 Multifidus: Oscillation")
    print("  🟠 Semispinalis: Gentle wave")
    print("  🟠 Rhomboid: Gentle pulse")
    print("  🟠 Serratus: Wave")
    print("  🟣 Spinal cord: Subtle pulse")
    print("  🟤 Vertebrae: Gentle sway")
    print("  Default: 35% amplitude, 0.8x speed")
    print("="*70)
    
    current_dir = os.getcwd()
    spinal_path = os.path.join(current_dir, "spinalcorddataset")
    muscle_path = os.path.join(current_dir, "muscelsdataset")
    
    # Check paths
    if not os.path.exists(spinal_path):
        print(f"\n❌ Spinal cord dataset not found: {spinal_path}\n")
        return
    
    if not os.path.exists(muscle_path):
        print(f"\n❌ Muscles dataset not found: {muscle_path}\n")
        return
    
    # Load files
    spinal_files = glob.glob(os.path.join(spinal_path, "*.obj"))
    spinal_files.extend(glob.glob(os.path.join(spinal_path, "*.OBJ")))
    spinal_files = sorted(list(set(spinal_files)))
    
    muscle_files = glob.glob(os.path.join(muscle_path, "*.obj"))
    muscle_files.extend(glob.glob(os.path.join(muscle_path, "*.OBJ")))
    muscle_files = sorted(list(set(muscle_files)))
    
    if not spinal_files and not muscle_files:
        print("\n❌ No OBJ files found in either dataset\n")
        return
    
    print(f"\n✅ Found {len(spinal_files)} spinal files")
    print(f"✅ Found {len(muscle_files)} muscle files")
    print("🚀 Launching spinal & muscle movement...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = CompleteSpinalMovement(spinal_files, muscle_files)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()