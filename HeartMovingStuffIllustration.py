import os
import glob
import numpy as np
import pyvista as pv
from PyQt5 import QtWidgets, QtCore
from pyvistaqt import BackgroundPlotter
import sys

"""
🫀 Realistic Heart Cardiac Cycle Animation
   - Using Heart Parts Dataset
Complete anatomical cardiac cycle with all parts moving correctly
"""

# Anatomical colors
ANATOMICAL_COLORS = {
    'right_atrium':      (0.85, 0.54, 0.54),
    'left_atrium':       (0.91, 0.60, 0.60),
    'right_ventricle':   (0.70, 0.13, 0.13),
    'left_ventricle':    (0.55, 0.00, 0.00),
    'mitral_valve':      (1.00, 0.71, 0.76),
    'tricuspid_valve':   (1.00, 0.75, 0.80),
    'aortic_valve':      (1.00, 0.41, 0.71),
    'pulmonary_valve':   (1.00, 0.71, 0.85),
    'valve':             (1.00, 0.71, 0.76),
    'papillary':         (0.65, 0.16, 0.16),
    'chordae':           (1.00, 0.97, 0.86),
    'septum':            (0.80, 0.36, 0.36),
    'vessel':            (0.86, 0.08, 0.24),
    'aorta':             (0.90, 0.10, 0.10),
    'vena_cava':         (0.40, 0.40, 0.70),
    'pulmonary_artery':  (0.70, 0.40, 0.50),
    'wall':              (0.75, 0.20, 0.20),
    'default':           (0.70, 0.13, 0.13),
}


def classify_heart_part(filename: str) -> str:
    """Classify heart part by filename"""
    name_lower = filename.lower()
    
    if 'right' in name_lower and any(w in name_lower for w in ['atrium', 'atrial']):
        return 'right_atrium'
    if 'left' in name_lower and any(w in name_lower for w in ['atrium', 'atrial']):
        return 'left_atrium'
    if 'right' in name_lower and 'ventricle' in name_lower:
        return 'right_ventricle'
    if 'left' in name_lower and 'ventricle' in name_lower:
        return 'left_ventricle'
    if 'mitral' in name_lower:
        return 'mitral_valve'
    if 'tricuspid' in name_lower:
        return 'tricuspid_valve'
    if 'aortic' in name_lower and 'valve' in name_lower:
        return 'aortic_valve'
    if 'pulmonary' in name_lower and 'valve' in name_lower:
        return 'pulmonary_valve'
    if 'valve' in name_lower:
        return 'valve'
    if 'papillary' in name_lower:
        return 'papillary'
    if 'chorda' in name_lower or 'tendin' in name_lower:
        return 'chordae'
    if 'septum' in name_lower or 'septal' in name_lower:
        return 'septum'
    if 'aorta' in name_lower:
        return 'aorta'
    if 'vena' in name_lower and 'cava' in name_lower:
        return 'vena_cava'
    if 'pulmonary' in name_lower and 'artery' in name_lower:
        return 'pulmonary_artery'
    if any(w in name_lower for w in ['artery', 'vein', 'vessel']):
        return 'vessel'
    if 'wall' in name_lower:
        return 'wall'
    if 'atrium' in name_lower or 'atrial' in name_lower:
        return 'right_atrium'
    if 'ventricle' in name_lower or 'ventricular' in name_lower:
        return 'left_ventricle'
    
    return 'default'


def smooth_step(t):
    """Smooth interpolation"""
    return t * t * (3 - 2 * t)


class RealisticHeartCycle(QtWidgets.QMainWindow):
    def __init__(self, parts_folder):
        super().__init__()
        self.parts_folder = parts_folder
        self.parts = []
        
        # Animation state
        self.is_animating = False
        self.time = 0.0
        self.beat_count = 0
        
        # Cardiac parameters
        self.heart_rate = 75  # BPM
        self.global_amplitude = 1.0
        
        # Storage
        self.original_positions = {}
        self.original_centers = {}
        self.original_bounds = {}
        
        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_cardiac_cycle)
        self.timer.setInterval(33)  # ~30 FPS
        
        self.setWindowTitle("Heart Cardiac pump")
        self.resize(1600, 900)
        self.setStyleSheet(self._get_stylesheet())
        
        self._build_ui()
        QtCore.QTimer.singleShot(100, self._initialize)
    
    def _get_stylesheet(self):
        return """
            QMainWindow { background: #000000; }
            QWidget { background: #000000; color: #ffffff; font-family: 'Segoe UI', Arial; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white; border: none;
                padding: 14px 24px; border-radius: 10px;
                font-size: 14pt; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6b5a, stop:1 #e74c3c);
            }
            QLabel { color: #ffffff; font-size: 12pt; }
            QSlider::groove:horizontal {
                background: #1a1a1a; height: 10px; border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #e74c3c; width: 24px; height: 24px;
                margin: -7px 0; border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #e74c3c; border-radius: 5px;
            }
            QGroupBox {
                background: #0a0a0a; border: 2px solid #1a1a1a;
                border-radius: 12px; padding: 18px; margin-top: 15px;
                color: #e74c3c; font-size: 14pt; font-weight: bold;
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
        top.setStyleSheet("background: #0a0a0a; border-bottom: 3px solid #e74c3c;")
        top.setFixedHeight(70)
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setContentsMargins(30, 10, 30, 10)
        top.setLayout(top_layout)
        
        title = QtWidgets.QLabel("Heart pump")
        title.setStyleSheet("color: #e74c3c; font-size: 20pt; font-weight: 800;")
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        self.bpm_label = QtWidgets.QLabel(f"{self.heart_rate} BPM")
        self.bpm_label.setStyleSheet("color: #e74c3c; font-size: 18pt; font-weight: bold;")
        top_layout.addWidget(self.bpm_label)
        
        viewer_layout.addWidget(top)
        
        # Plotter
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background('#000000')
        viewer_layout.addWidget(self.plotter.interactor)
        
        main_layout.addWidget(viewer, 1)
    
    def _create_control_panel(self):
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(400)
        panel.setStyleSheet("background: #050505; border-right: 3px solid #e74c3c;")
        
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        content.setLayout(layout)
        
        # Title
        title = QtWidgets.QLabel("Cardiac Control")
        title.setStyleSheet("color: #e74c3c; font-size: 20pt; font-weight: 800;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Main control
        main_box = QtWidgets.QGroupBox("Main Control")
        main_layout = QtWidgets.QVBoxLayout()
        
        self.btn_play = QtWidgets.QPushButton("▶ START HEARTBEAT")
        self.btn_play.clicked.connect(self._toggle)
        main_layout.addWidget(self.btn_play)
        
        btn_reset = QtWidgets.QPushButton("🔄 RESET")
        btn_reset.clicked.connect(self._reset)
        main_layout.addWidget(btn_reset)
        
        main_box.setLayout(main_layout)
        layout.addWidget(main_box)
        
        # Settings
        settings_box = QtWidgets.QGroupBox("Settings")
        settings_layout = QtWidgets.QVBoxLayout()
        
        settings_layout.addWidget(QtWidgets.QLabel("Heart Rate (BPM)"))
        self.hr_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.hr_slider.setRange(40, 180)
        self.hr_slider.setValue(75)
        self.hr_slider.valueChanged.connect(self._update_heart_rate)
        settings_layout.addWidget(self.hr_slider)
        self.hr_label = QtWidgets.QLabel("75 BPM")
        self.hr_label.setAlignment(QtCore.Qt.AlignCenter)
        settings_layout.addWidget(self.hr_label)
        
        settings_layout.addWidget(QtWidgets.QLabel("Contraction Strength"))
        self.amp_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.amp_slider.setRange(20, 200)
        self.amp_slider.setValue(100)
        self.amp_slider.valueChanged.connect(self._update_amplitude)
        settings_layout.addWidget(self.amp_slider)
        self.amp_label = QtWidgets.QLabel("100%")
        self.amp_label.setAlignment(QtCore.Qt.AlignCenter)
        settings_layout.addWidget(self.amp_label)
        
        settings_box.setLayout(settings_layout)
        layout.addWidget(settings_box)
        
        # Phase indicator
        phase_box = QtWidgets.QGroupBox("Cardiac Phase")
        phase_layout = QtWidgets.QVBoxLayout()
        
        self.phase_label = QtWidgets.QLabel("Ready")
        self.phase_label.setStyleSheet("color: #4ecdc4; font-size: 16pt; font-weight: bold;")
        self.phase_label.setAlignment(QtCore.Qt.AlignCenter)
        phase_layout.addWidget(self.phase_label)
        
        self.phase_detail = QtWidgets.QLabel("...")
        self.phase_detail.setStyleSheet("color: #aaa; font-size: 10pt;")
        self.phase_detail.setAlignment(QtCore.Qt.AlignCenter)
        self.phase_detail.setWordWrap(True)
        phase_layout.addWidget(self.phase_detail)
        
        self.beat_label = QtWidgets.QLabel("Beat: 0")
        self.beat_label.setStyleSheet("color: #FFD700; font-size: 14pt;")
        self.beat_label.setAlignment(QtCore.Qt.AlignCenter)
        phase_layout.addWidget(self.beat_label)
        
        phase_box.setLayout(phase_layout)
        layout.addWidget(phase_box)
        
        # Info
        info_box = QtWidgets.QGroupBox("Cardiac Cycle")
        info_layout = QtWidgets.QVBoxLayout()
        
        info_text = QtWidgets.QLabel(
            "📍 Diastole: Heart fills with blood\n"
            "  → Atria fill → Ventricles fill\n\n"
            "📍 Atrial Systole: Atria contract\n"
            "  → Push blood to ventricles\n\n"
            "📍 Ventricular Systole: Ventricles contract\n"
            "  → AV valves close\n"
            "  → Semilunar valves open\n"
            "  → Blood pumped out\n\n"
            "📍 Papillary muscles & chordae\n"
            "  → Prevent valve prolapse"
        )
        info_text.setStyleSheet("color: #ccc; font-size: 9pt; line-height: 1.6;")
        info_layout.addWidget(info_text)
        
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)
        
        # Parts count
        self.parts_label = QtWidgets.QLabel("Parts: 0")
        self.parts_label.setStyleSheet("color: #4ecdc4; font-size: 12pt; padding: 10px;")
        self.parts_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.parts_label)
        
        # Status
        self.status = QtWidgets.QLabel("Ready")
        self.status.setStyleSheet(
            "color: #e74c3c; font-size: 13pt; font-weight: bold; "
            "padding: 15px; background: #0a0a0a; border-radius: 10px;"
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
        self.status.setText("⏳ Loading heart parts...")
        QtWidgets.QApplication.processEvents()
        
        self._load_heart_parts()
        self._setup_scene()
        
        self.status.setText("✅ Ready! Press START")
    
    def _load_heart_parts(self):
        """Load individual heart parts"""
        obj_files = glob.glob(os.path.join(self.parts_folder, "*.obj"))
        obj_files.extend(glob.glob(os.path.join(self.parts_folder, "*.OBJ")))
        obj_files = sorted(list(set(obj_files)))
        
        print(f"\n🔍 Found {len(obj_files)} OBJ files in {self.parts_folder}")
        
        loaded = 0
        for path in obj_files:
            try:
                mesh = pv.read(path)
                if mesh.n_points == 0:
                    continue
                
                mesh = mesh.clean()
                mesh = mesh.compute_normals(auto_orient_normals=True)
                
                name = os.path.basename(path)
                region = classify_heart_part(name)
                color = ANATOMICAL_COLORS.get(region, ANATOMICAL_COLORS['default'])
                
                self.parts.append({
                    'name': name,
                    'mesh': mesh,
                    'color': color,
                    'region': region,
                    'original_center': np.array(mesh.center),
                    'actor': None
                })
                
                print(f"✅ {name[:50]:<50} → {region}")
                loaded += 1
                
            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
        
        print(f"\n✅ Successfully loaded {loaded} heart parts")
        self.parts_label.setText(f"Parts: {loaded}")
    
    def _setup_scene(self):
        """Setup 3D scene"""
        for part in self.parts:
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=0.95,
                smooth_shading=True,
                ambient=0.3,
                diffuse=0.7,
                specular=0.8,
                specular_power=50
            )
            part['actor'] = actor
            
            self.original_positions[part['name']] = part['mesh'].points.copy()
            self.original_centers[part['name']] = part['original_center'].copy()
            self.original_bounds[part['name']] = part['mesh'].bounds
        
        # Lighting
        self.plotter.remove_all_lights()
        
        light1 = pv.Light(position=(20, 20, 20), light_type='scene light')
        light1.intensity = 0.7
        self.plotter.add_light(light1)
        
        light2 = pv.Light(position=(-15, 15, 10), light_type='scene light')
        light2.intensity = 0.4
        self.plotter.add_light(light2)
        
        light3 = pv.Light(position=(0, -15, -10), light_type='scene light')
        light3.intensity = 0.35
        self.plotter.add_light(light3)
        
        # Camera
        self.plotter.reset_camera()
        bounds = self.plotter.bounds
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2
        cz = (bounds[4] + bounds[5]) / 2
        
        self.plotter.camera.position = (cx + 80, cy - 100, cz + 60)
        self.plotter.camera.focal_point = (cx, cy, cz)
        self.plotter.camera.zoom(1.6)
        
        print("✅ Scene ready")
    
    def _toggle(self):
        if self.is_animating:
            self.is_animating = False
            self.timer.stop()
            self.btn_play.setText("▶ START HEARTBEAT")
            self.status.setText("⏸ Paused")
        else:
            self.is_animating = True
            self.timer.start()
            self.btn_play.setText("⏸ PAUSE")
            self.status.setText("💓 Heart beating...")
    
    def _update_cardiac_cycle(self):
        """Complete cardiac cycle animation"""
        if not self.is_animating:
            return
        
        dt = 0.033
        beat_duration = 60.0 / self.heart_rate
        self.time += dt
        
        # Cycle position (0-1)
        t = (self.time % beat_duration) / beat_duration
        
        # Track beats
        if t < 0.02:
            new_beat = int(self.time / beat_duration) + 1
            if new_beat != self.beat_count:
                self.beat_count = new_beat
                self.beat_label.setText(f"Beat: {self.beat_count}")
        
        # === CARDIAC PHASES ===
        # 0.0 - 0.15: Atrial Systole (atria contract)
        # 0.15 - 0.45: Ventricular Systole (ventricles contract)
        # 0.45 - 1.0: Diastole (filling)
        
        if t < 0.15:
            phase_name = "Atrial Systole"
            phase_detail = " \nAtria contracting"
        elif t < 0.45:
            phase_name = "Ventricular Systole"
            phase_detail = "  \nVentricles pumping"
        else:
            phase_name = "Diastole"
            phase_detail = "  \nHeart filling"
        
        self.phase_label.setText(phase_name)
        self.phase_detail.setText(phase_detail)
        
        # Update each part
        for part in self.parts:
            region = part['region']
            orig = self.original_positions[part['name']]
            center = self.original_centers[part['name']]
            bounds = self.original_bounds[part['name']]
            
            new_points = orig.copy()
            
            # === ATRIA ===
            if 'atrium' in region:
                if t < 0.15:
                    # Atrial contraction
                    phase = t / 0.15
                    contraction = 0.10 * self.global_amplitude * smooth_step(phase)
                    vectors = orig - center
                    scale = 1.0 - contraction
                    new_points = center + vectors * scale
                    
                elif t > 0.45:
                    # Filling (expansion)
                    phase = (t - 0.45) / 0.55
                    expansion = 0.06 * self.global_amplitude * smooth_step(phase)
                    vectors = orig - center
                    scale = 1.0 + expansion
                    new_points = center + vectors * scale
            
            # === VENTRICLES ===
            elif 'ventricle' in region:
                if t >= 0.15 and t < 0.45:
                    # Ventricular systole
                    phase = (t - 0.15) / 0.30
                    
                    # Stronger contraction for left ventricle
                    if 'left' in region:
                        contraction = 0.18 * self.global_amplitude * smooth_step(phase)
                    else:
                        contraction = 0.14 * self.global_amplitude * smooth_step(phase)
                    
                    vectors = orig - center
                    
                    # Radial contraction
                    scale = 1.0 - contraction
                    new_points = center + vectors * scale
                    
                    # Apex-to-base motion
                    y_min, y_max = bounds[2], bounds[3]
                    y_range = y_max - y_min if y_max != y_min else 1.0
                    if y_range > 0:
                        y_normalized = (orig[:, 1] - y_min) / y_range
                        longitudinal_shortening = 0.06 * self.global_amplitude * smooth_step(phase) * y_normalized * y_range
                        new_points[:, 1] += longitudinal_shortening
                    
                    # Twisting motion
                    if 'left' in region:
                        twist_angle = -0.10 * self.global_amplitude * np.sin(phase * np.pi)
                    else:
                        twist_angle = -0.06 * self.global_amplitude * np.sin(phase * np.pi)
                    
                    # Apply twist if y-axis has variation
                    if y_range > 0:
                        y_norm_twist = (new_points[:, 1] - center[1]) / (y_range / 2)
                        local_twist = twist_angle * np.clip(y_norm_twist, 0, 1)
                        
                        cos_t = np.cos(local_twist)
                        sin_t = np.sin(local_twist)
                        rel_x = new_points[:, 0] - center[0]
                        rel_z = new_points[:, 2] - center[2]
                        
                        new_points[:, 0] = center[0] + rel_x * cos_t - rel_z * sin_t
                        new_points[:, 2] = center[2] + rel_x * sin_t + rel_z * cos_t
            
            # === AV VALVES (Mitral, Tricuspid) ===
            elif region in ['mitral_valve', 'tricuspid_valve']:
                if t < 0.15:
                    # Open during atrial systole
                    phase = t / 0.15
                    opening = 0.12 * self.global_amplitude * smooth_step(phase)
                    displacement = opening * 3.0
                    new_points[:, 1] += displacement
                    
                elif t >= 0.15 and t < 0.45:
                    # Closed during ventricular systole
                    closing = -0.08 * self.global_amplitude
                    displacement = closing * 3.0
                    new_points[:, 1] += displacement
                    
                elif t >= 0.45:
                    # Gradually open during diastole
                    phase = (t - 0.45) / 0.55
                    opening = 0.10 * self.global_amplitude * smooth_step(phase)
                    displacement = opening * 3.0
                    new_points[:, 1] += displacement
            
            # === SEMILUNAR VALVES (Aortic, Pulmonary) ===
            elif region in ['aortic_valve', 'pulmonary_valve']:
                if t >= 0.15 and t < 0.45:
                    # Open during ventricular systole
                    phase = (t - 0.15) / 0.30
                    opening = 0.15 * self.global_amplitude * smooth_step(phase)
                    
                    vectors = orig - center
                    scale = 1.0 + opening * 0.2
                    new_points = center + vectors * scale
                    
                    displacement = opening * 2.5
                    new_points[:, 1] += displacement
            
            # === PAPILLARY MUSCLES ===
            elif 'papillary' in region:
                if t >= 0.15 and t < 0.45:
                    # Contract with ventricles
                    phase = (t - 0.15) / 0.30
                    contraction = 0.12 * self.global_amplitude * smooth_step(phase)
                    vectors = orig - center
                    scale = 1.0 - contraction
                    new_points = center + vectors * scale
            
            # === CHORDAE TENDINEAE ===
            elif 'chordae' in region:
                if t >= 0.15 and t < 0.45:
                    # Tension during ventricular systole
                    phase = (t - 0.15) / 0.30
                    tension = 0.10 * self.global_amplitude * smooth_step(phase)
                    displacement = tension * 2.5
                    new_points[:, 1] -= displacement
            
            # === SEPTUM ===
            elif 'septum' in region:
                if t >= 0.15 and t < 0.45:
                    # Moves with ventricles
                    phase = (t - 0.15) / 0.30
                    motion = 0.08 * self.global_amplitude * smooth_step(phase)
                    vectors = orig - center
                    scale = 1.0 - motion * 0.5
                    new_points = center + vectors * scale
            
            # === VESSELS ===
            elif region in ['aorta', 'pulmonary_artery', 'vena_cava', 'vessel']:
                if t >= 0.15 and t < 0.50:
                    # Pulse wave
                    phase = (t - 0.15) / 0.35
                    
                    pulse = 0.06 * self.global_amplitude * np.sin(phase * np.pi)
                    vectors = orig - center
                    
                    # Ensure pulse is a scalar
                    pulse_scalar = float(pulse)
                    scale = 1.0 + pulse_scalar
                    new_points = center + vectors * scale
            
            # Update mesh
            part['mesh'].points = new_points
            part['mesh'].compute_normals(auto_orient_normals=True, inplace=True)
        
        self.plotter.render()
    
    def _reset(self):
        """Reset to original state"""
        for part in self.parts:
            part['mesh'].points = self.original_positions[part['name']].copy()
            part['mesh'].compute_normals(auto_orient_normals=True, inplace=True)
        
        self.time = 0.0
        self.beat_count = 0
        self.beat_label.setText("Beat: 0")
        self.phase_label.setText("Ready")
        self.phase_detail.setText("...")
        self.plotter.render()
        self.status.setText("🔄 Reset")
    
    def _update_amplitude(self, val):
        self.global_amplitude = val / 100.0
        self.amp_label.setText(f"{val}%")
    
    def _update_heart_rate(self, val):
        self.heart_rate = val
        self.hr_label.setText(f"{val} BPM")
        self.bpm_label.setText(f"{val} BPM")


def main():
    print("\n" + "="*70)
    print("🫀 REALISTIC HEART CARDIAC CYCLE ANIMATION")
    print("="*70)
    print("Complete anatomical cardiac cycle:")
    print("  ✓ Atrial Systole → Atria contract, push blood")
    print("  ✓ Ventricular Systole → Ventricles contract strongly")
    print("  ✓ Diastole → Heart fills with blood")
    print("  ✓ AV valves (mitral/tricuspid) → Open/close coordination")
    print("  ✓ Semilunar valves (aortic/pulmonary) → Open during pumping")
    print("  ✓ Papillary muscles → Contract and pull")
    print("  ✓ Chordae tendineae → Create tension")
    print("  ✓ Vessels → Pulse wave propagation")
    print("="*70)
    
    current_dir = os.getcwd()
    
    # Look for heart parts folder
    possible_folders = [
        "heart parts",
        "heart_parts",
        "Heart parts",
        "Heart Parts",
        "Heart_parts",
        "parts"
    ]
    
    parts_folder = None
    for folder_name in possible_folders:
        path = os.path.join(current_dir, folder_name)
        if os.path.isdir(path):
            obj_files = glob.glob(os.path.join(path, "*.obj"))
            obj_files.extend(glob.glob(os.path.join(path, "*.OBJ")))
            if obj_files:
                parts_folder = path
                break
    
    if not parts_folder:
        print("\n❌ Heart parts folder not found!")
        print(f"Looking for folders: {', '.join(possible_folders)}")
        print(f"Current directory: {current_dir}")
        print("\nExpected structure:")
        print("  your_directory/")
        print("  └── heart parts/")
        print("      ├── part001.obj")
        print("      ├── part002.obj")
        print("      └── ...\n")
        return
    
    print(f"\n✅ Found heart parts folder: {parts_folder}")
    obj_count = len(glob.glob(os.path.join(parts_folder, "*.obj")))
    print(f"✅ Found {obj_count} OBJ files")
    print("🚀 Launching realistic heart animation...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = RealisticHeartCycle(parts_folder)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()