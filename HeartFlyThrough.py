import os
import glob
import numpy as np
import pyvista as pv
from PyQt5 import QtWidgets, QtCore
from pyvistaqt import BackgroundPlotter
import sys

"""
❤ Heart Fly-through Viewer - ANATOMICAL COLORING
Camera flies around AND through the heart with accurate anatomical colors
"""

# Anatomical heart colors (realistic medical visualization)
HEART_COLORS = {
    # Chambers
    'atrium': (0.85, 0.4, 0.4),          # Light red (oxygenated in left, deoxygenated in right)
    'ventricle': (0.7, 0.2, 0.2),        # Dark red (muscular walls)
    'left': (0.9, 0.3, 0.3),             # Brighter red (oxygenated blood)
    'right': (0.6, 0.25, 0.35),          # Darker red/purple (deoxygenated blood)
    
    # Valves
    'valve': (0.95, 0.85, 0.75),         # Light beige/cream
    'mitral': (0.95, 0.85, 0.75),
    'tricuspid': (0.95, 0.85, 0.75),
    'aortic': (0.95, 0.85, 0.75),
    'pulmonary': (0.95, 0.85, 0.75),
    
    # Major vessels
    'aorta': (0.95, 0.3, 0.25),          # Bright red (oxygenated arterial)
    'pulmonary': (0.5, 0.3, 0.5),        # Purple-ish (deoxygenated to lungs)
    'vena': (0.5, 0.3, 0.4),             # Dark purple (deoxygenated venous)
    'artery': (0.9, 0.35, 0.3),          # Red (arterial)
    'vein': (0.5, 0.3, 0.45),            # Purple (venous)
    
    # Other structures
    'septum': (0.75, 0.3, 0.3),          # Medium red (septal wall)
    'wall': (0.7, 0.25, 0.25),           # Muscle wall
    'apex': (0.65, 0.2, 0.2),            # Darker at apex
    'base': (0.8, 0.35, 0.35),           # Lighter at base
    
    # Default
    'default': (0.75, 0.25, 0.25),       # Medium red
}


def classify_heart_part(filename: str) -> str:
    """Classify heart anatomical parts based on filename"""
    name = filename.lower()
    
    # Valves (check first - most specific)
    if 'mitral' in name or 'bicuspid' in name:
        return 'mitral'
    if 'tricuspid' in name:
        return 'tricuspid'
    if 'aortic' in name and 'valve' in name:
        return 'aortic'
    if 'pulmonary' in name and 'valve' in name:
        return 'pulmonary'
    if 'valve' in name:
        return 'valve'
    
    # Major vessels
    if 'aorta' in name or 'aortic' in name:
        return 'aorta'
    if 'vena' in name or 'cava' in name:
        return 'vena'
    if 'pulmonary' in name and ('artery' in name or 'trunk' in name):
        return 'pulmonary'
    
    # Chambers - specific left/right
    if 'left' in name:
        if 'atrium' in name or 'atrial' in name:
            return 'left'
        if 'ventricle' in name or 'ventricular' in name:
            return 'left'
    if 'right' in name:
        if 'atrium' in name or 'atrial' in name:
            return 'right'
        if 'ventricle' in name or 'ventricular' in name:
            return 'right'
    
    # General chambers
    if 'atrium' in name or 'atrial' in name:
        return 'atrium'
    if 'ventricle' in name or 'ventricular' in name:
        return 'ventricle'
    
    # Vessels general
    if 'artery' in name or 'arterial' in name:
        return 'artery'
    if 'vein' in name or 'venous' in name:
        return 'vein'
    
    # Structures
    if 'septum' in name or 'septal' in name:
        return 'septum'
    if 'wall' in name:
        return 'wall'
    if 'apex' in name:
        return 'apex'
    if 'base' in name:
        return 'base'
    
    return 'default'


class HeartFlythrough(QtWidgets.QMainWindow):
    def __init__(self, heart_parts_folder):
        super().__init__()
        self.heart_parts_folder = heart_parts_folder
        self.parts = []
        
        # Animation state
        self.is_animating = False
        self.animation_progress = 0.0
        self.animation_speed = 0.003
        
        # Heart parameters
        self.center_point = None
        self.heart_bounds = None
        self.current_path_mode = 0
        
        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_camera)
        self.timer.setInterval(33)
        
        self.setWindowTitle("❤ Heart Fly-through - Anatomical Coloring")
        self.resize(1400, 800)
        self.setStyleSheet("""
            QMainWindow { background: #1a1a1a; }
            QWidget { background: #1a1a1a; color: #ffffff; font-family: Arial; }
            QPushButton {
                background: #c41e3a;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton:hover { background: #dc143c; }
            QPushButton:pressed { background: #8b0000; }
            QLabel { color: #ffffff; font-size: 12pt; }
            QSlider::groove:horizontal {
                background: #333;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #c41e3a;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #dc143c;
                border-radius: 4px;
            }
            QComboBox {
                background: #333;
                color: white;
                border: 2px solid #c41e3a;
                padding: 8px;
                border-radius: 4px;
                font-size: 12pt;
            }
        """)
        
        self._build_ui()
        QtCore.QTimer.singleShot(100, self._initialize)
    
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central.setLayout(main_layout)
        
        # Control Panel
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(320)
        panel.setStyleSheet("background: #2a2a2a; border-right: 2px solid #c41e3a;")
        
        panel_layout = QtWidgets.QVBoxLayout()
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(20)
        panel.setLayout(panel_layout)
        
        title = QtWidgets.QLabel("❤ Heart\nFly-through")
        title.setStyleSheet("font-size: 22pt; font-weight: bold; color: #dc143c;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(title)
        
        mode_label = QtWidgets.QLabel("Flight Path:")
        mode_label.setStyleSheet("font-size: 14pt; margin-top: 10px;")
        panel_layout.addWidget(mode_label)
        
        self.path_combo = QtWidgets.QComboBox()
        self.path_combo.addItems([
            "🌀 Spiral Journey",
            "🔄 Circle Around",
            "🫀 Through Chambers",
            "💓 Heartbeat Path",
            "🔍 Detailed Scan"
        ])
        self.path_combo.setCurrentIndex(0)
        self.path_combo.currentIndexChanged.connect(self._change_path_mode)
        panel_layout.addWidget(self.path_combo)
        
        self.btn_play = QtWidgets.QPushButton("▶ PLAY")
        self.btn_play.clicked.connect(self._toggle_animation)
        panel_layout.addWidget(self.btn_play)
        
        btn_reset = QtWidgets.QPushButton("🔄 RESET")
        btn_reset.clicked.connect(self._reset_view)
        panel_layout.addWidget(btn_reset)
        
        speed_label = QtWidgets.QLabel("Speed")
        speed_label.setStyleSheet("font-size: 14pt; margin-top: 20px;")
        panel_layout.addWidget(speed_label)
        
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(3)
        self.speed_slider.valueChanged.connect(self._update_speed)
        panel_layout.addWidget(self.speed_slider)
        
        self.speed_value = QtWidgets.QLabel("Speed: 3")
        self.speed_value.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.speed_value)
        
        opacity_label = QtWidgets.QLabel("Heart Opacity")
        opacity_label.setStyleSheet("font-size: 14pt; margin-top: 20px;")
        panel_layout.addWidget(opacity_label)
        
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._update_opacity)
        panel_layout.addWidget(self.opacity_slider)
        
        self.opacity_value = QtWidgets.QLabel("Opacity: 100%")
        self.opacity_value.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.opacity_value)
        
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #dc143c; font-size: 11pt; margin-top: 20px;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.status_label)
        
        self.progress_label = QtWidgets.QLabel("Progress: 0%")
        self.progress_label.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.progress_label)
        
        self.position_label = QtWidgets.QLabel("Position: Full Heart View")
        self.position_label.setAlignment(QtCore.Qt.AlignCenter)
        self.position_label.setStyleSheet("color: #ff6b6b; font-size: 10pt;")
        panel_layout.addWidget(self.position_label)
        
        panel_layout.addStretch()
        main_layout.addWidget(panel)
        
        # 3D Viewer
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background('#0a0a0a')
        main_layout.addWidget(self.plotter.interactor, 1)
    
    def _initialize(self):
        self.status_label.setText("Loading heart parts...")
        QtWidgets.QApplication.processEvents()
        self._load_heart_parts()
        self._setup_scene()
        self.status_label.setText("✅ Ready to explore!")
    
    def _load_heart_parts(self):
        """Load all heart part OBJ files with anatomical colors"""
        # Find all OBJ files in heart parts folder
        obj_files = glob.glob(os.path.join(self.heart_parts_folder, "*.obj"))
        obj_files.extend(glob.glob(os.path.join(self.heart_parts_folder, "*.OBJ")))
        obj_files = sorted(list(set(obj_files)))
        
        print(f"\nFound {len(obj_files)} heart part files in: {self.heart_parts_folder}")
        
        loaded = 0
        for path in obj_files:
            try:
                mesh = pv.read(path)
                if mesh.n_points == 0:
                    continue
                
                mesh = mesh.clean()
                mesh = mesh.compute_normals(auto_orient_normals=True)
                
                filename = os.path.basename(path)
                part_type = classify_heart_part(filename)
                color = HEART_COLORS.get(part_type, HEART_COLORS['default'])
                
                self.parts.append({
                    'name': filename,
                    'mesh': mesh,
                    'color': color,
                    'type': part_type,
                    'actor': None
                })
                
                print(f"✅ Loaded: {filename[:40]:<40} -> {part_type:<15} Color: {color}")
                loaded += 1
                
            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
        
        print(f"\n✅ Successfully loaded {loaded} heart parts with anatomical colors")
    
    def _setup_scene(self):
        if not self.parts:
            print("❌ No heart parts loaded!")
            QtWidgets.QMessageBox.warning(self, "Warning", "No heart parts found!")
            return
        
        # Add all heart parts with their anatomical colors
        for part in self.parts:
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=1.0,
                smooth_shading=True,
                lighting=True,
                specular=0.4,
                specular_power=15
            )
            part['actor'] = actor
        
        # Professional lighting setup
        self.plotter.remove_all_lights()
        
        # Key light (main)
        key_light = pv.Light()
        key_light.set_direction_angle(30, 30)
        key_light.intensity = 1.2
        self.plotter.add_light(key_light)
        
        # Fill light (softer)
        fill_light = pv.Light()
        fill_light.set_direction_angle(-150, -20)
        fill_light.intensity = 0.5
        self.plotter.add_light(fill_light)
        
        # Back light (rim lighting)
        back_light = pv.Light()
        back_light.set_direction_angle(150, 60)
        back_light.intensity = 0.6
        self.plotter.add_light(back_light)
        
        # Ambient light
        ambient = pv.Light()
        ambient.intensity = 0.3
        self.plotter.add_light(ambient)
        
        # Calculate heart center and bounds
        bounds = self.plotter.bounds
        self.heart_bounds = bounds
        self.center_point = np.array([
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2
        ])
        
        # Calculate appropriate camera distance based on heart size
        heart_size = max(
            bounds[1] - bounds[0],
            bounds[3] - bounds[2],
            bounds[5] - bounds[4]
        )
        
        print(f"\nHeart Center: {self.center_point}")
        print(f"Heart Bounds: {bounds}")
        print(f"Heart Size: {heart_size}")
        
        # Set initial camera position
        camera_distance = heart_size * 2.5
        angle = np.pi / 4
        
        initial_cam_x = self.center_point[0] + camera_distance * np.cos(angle)
        initial_cam_y = self.center_point[1] + camera_distance * np.sin(angle)
        initial_cam_z = self.center_point[2] + camera_distance * 0.3
        
        self.plotter.camera.position = (initial_cam_x, initial_cam_y, initial_cam_z)
        self.plotter.camera.focal_point = tuple(self.center_point)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.render()
        print("✅ Scene ready with anatomical colors")
    
    def _get_heart_size(self):
        """Get the characteristic size of the heart"""
        return max(
            self.heart_bounds[1] - self.heart_bounds[0],
            self.heart_bounds[3] - self.heart_bounds[2],
            self.heart_bounds[5] - self.heart_bounds[4]
        )
    
    def _get_camera_path_position(self, progress):
        mode = self.path_combo.currentIndex()
        if mode == 0:
            return self._spiral_journey_path(progress)
        elif mode == 1:
            return self._circle_around_path(progress)
        elif mode == 2:
            return self._through_chambers_path(progress)
        elif mode == 3:
            return self._heartbeat_path(progress)
        elif mode == 4:
            return self._detailed_scan_path(progress)
        return self._spiral_journey_path(progress)
    
    def _spiral_journey_path(self, t):
        """Spiral from outside to inside and back"""
        cx, cy, cz = self.center_point
        size = self._get_heart_size()
        
        if t < 0.25:
            # Spiral in
            phase_t = t / 0.25
            angle = phase_t * 4 * np.pi
            radius = size * 2.5 * (1 - phase_t)
            height = size * 0.5 * np.sin(phase_t * np.pi)
            
            cam_x = cx + radius * np.cos(angle)
            cam_y = cy + radius * np.sin(angle)
            cam_z = cz + height
            focal = self.center_point
            position_name = f"🌀 Spiraling In ({int(phase_t*100)}%)"
            
        elif t < 0.75:
            # Inside exploration
            phase_t = (t - 0.25) / 0.5
            angle = phase_t * 8 * np.pi
            inner_radius = size * 0.3
            
            cam_x = cx + inner_radius * np.cos(angle)
            cam_y = cy + inner_radius * np.sin(angle)
            cam_z = cz + size * 0.2 * np.sin(phase_t * 4 * np.pi)
            
            focal_offset = size * 0.15
            focal = np.array([
                cx + focal_offset * np.cos(angle + np.pi/4),
                cy + focal_offset * np.sin(angle + np.pi/4),
                cz
            ])
            position_name = f"❤ Inside Heart ({int(phase_t*100)}%)"
            
        else:
            # Spiral out
            phase_t = (t - 0.75) / 0.25
            angle = (1 - phase_t) * 4 * np.pi
            radius = size * 2.5 * phase_t
            height = -size * 0.5 * np.sin(phase_t * np.pi)
            
            cam_x = cx + radius * np.cos(angle)
            cam_y = cy + radius * np.sin(angle)
            cam_z = cz + height
            focal = self.center_point
            position_name = f"🌀 Spiraling Out ({int(phase_t*100)}%)"
        
        return np.array([cam_x, cam_y, cam_z]), focal, np.array([0, 0, 1]), position_name
    
    def _circle_around_path(self, t):
        """Simple circular orbit around the heart"""
        cx, cy, cz = self.center_point
        size = self._get_heart_size()
        
        angle = t * 2 * np.pi
        radius = size * 2
        
        cam_x = cx + radius * np.cos(angle)
        cam_y = cy + radius * np.sin(angle)
        cam_z = cz + size * 0.3 * np.sin(angle * 2)
        
        return (np.array([cam_x, cam_y, cam_z]),
                self.center_point,
                np.array([0, 0, 1]),
                f"🔄 Orbiting ({int(t*360)}°)")
    
    def _through_chambers_path(self, t):
        """Simulate path through heart chambers"""
        cx, cy, cz = self.center_point
        size = self._get_heart_size()
        
        if t < 0.15:
            # Approach from top (superior vena cava entry)
            phase_t = t / 0.15
            distance = size * 3 * (1 - phase_t)
            cam_x = cx
            cam_y = cy + size * 0.3
            cam_z = cz + distance
            focal = self.center_point
            position_name = f"↓ Entering from Top ({int(phase_t*100)}%)"
            
        elif t < 0.35:
            # Right atrium
            phase_t = (t - 0.15) / 0.2
            angle = phase_t * np.pi
            cam_x = cx + size * 0.2 * np.cos(angle)
            cam_y = cy + size * 0.3
            cam_z = cz + size * 0.2 * (1 - phase_t)
            focal = np.array([cx, cy + size * 0.2, cz])
            position_name = f"🫀 Right Atrium ({int(phase_t*100)}%)"
            
        elif t < 0.55:
            # Right ventricle
            phase_t = (t - 0.35) / 0.2
            cam_x = cx + size * 0.15
            cam_y = cy + size * 0.2 * (1 - phase_t * 0.5)
            cam_z = cz - size * 0.3 * phase_t
            focal = np.array([cx, cy, cz - size * 0.2])
            position_name = f"💓 Right Ventricle ({int(phase_t*100)}%)"
            
        elif t < 0.75:
            # Left side passage
            phase_t = (t - 0.55) / 0.2
            angle = phase_t * np.pi
            cam_x = cx - size * 0.2 * phase_t
            cam_y = cy
            cam_z = cz
            focal = np.array([cx - size * 0.3, cy, cz])
            position_name = f"🔄 Crossing to Left Side ({int(phase_t*100)}%)"
            
        else:
            # Exit from apex
            phase_t = (t - 0.75) / 0.25
            distance = size * 3 * phase_t
            cam_x = cx
            cam_y = cy
            cam_z = cz - distance
            focal = self.center_point
            position_name = f"↑ Exiting from Bottom ({int(phase_t*100)}%)"
        
        return np.array([cam_x, cam_y, cam_z]), focal, np.array([0, 0, 1]), position_name
    
    def _heartbeat_path(self, t):
        """Pulsing motion simulating heartbeat rhythm"""
        cx, cy, cz = self.center_point
        size = self._get_heart_size()
        
        # Create heartbeat pulse effect (lub-dub pattern)
        beat_cycle = t * 4  # 4 beats per full cycle
        beat_phase = beat_cycle % 1
        
        if beat_phase < 0.3:
            # Systole (contraction) - quick
            pulse = beat_phase / 0.3
        elif beat_phase < 0.5:
            # Diastole relaxation
            pulse = 1 - (beat_phase - 0.3) / 0.2
        else:
            pulse = 0
        
        # Base circular motion
        angle = t * 2 * np.pi
        base_radius = size * 2
        
        # Apply pulse to camera distance
        pulse_factor = 0.3 * pulse
        radius = base_radius * (1 - pulse_factor)
        
        cam_x = cx + radius * np.cos(angle)
        cam_y = cy + radius * np.sin(angle)
        cam_z = cz + size * 0.5
        
        # Focal point also pulses slightly
        focal = np.array([
            cx,
            cy,
            cz + size * 0.1 * pulse
        ])
        
        beat_phase_percent = int(beat_phase * 100)
        return (np.array([cam_x, cam_y, cam_z]),
                focal,
                np.array([0, 0, 1]),
                f"💓 Heartbeat Rhythm ({beat_phase_percent}%)")
    
    def _detailed_scan_path(self, t):
        """Detailed scanning path covering all angles"""
        cx, cy, cz = self.center_point
        size = self._get_heart_size()
        
        # Vertical scanning motion
        elevation = np.sin(t * 2 * np.pi) * size * 0.6
        
        # Horizontal rotation
        azimuth = t * 6 * np.pi
        radius = size * 2.2
        
        cam_x = cx + radius * np.cos(azimuth)
        cam_y = cy + radius * np.sin(azimuth)
        cam_z = cz + elevation
        
        # Look slightly ahead of current position
        look_ahead = 0.3
        focal_azimuth = azimuth + look_ahead
        focal = np.array([
            cx + size * 0.5 * np.cos(focal_azimuth),
            cy + size * 0.5 * np.sin(focal_azimuth),
            cz + elevation * 0.5
        ])
        
        return (np.array([cam_x, cam_y, cam_z]),
                focal,
                np.array([0, 0, 1]),
                f"🔍 Scanning ({int(t*100)}%)")
    
    def _set_camera_position_by_path(self, progress):
        cam_pos, focal, up, pos_name = self._get_camera_path_position(progress)
        self.plotter.camera.position = tuple(cam_pos)
        self.plotter.camera.focal_point = tuple(focal)
        self.plotter.camera.up = tuple(up)
        self.plotter.render()
        self.position_label.setText(f"Position: {pos_name}")
    
    def _toggle_animation(self):
        if self.is_animating:
            self.is_animating = False
            self.timer.stop()
            self.btn_play.setText("▶ PLAY")
            self.status_label.setText("⏸ Paused")
        else:
            self.is_animating = True
            self.timer.start()
            self.btn_play.setText("⏸ PAUSE")
            self.status_label.setText("▶ Flying...")
    
    def _update_camera(self):
        if not self.is_animating:
            return
        
        self.animation_progress += self.animation_speed
        if self.animation_progress >= 1.0:
            self.animation_progress = 0.0
        
        self._set_camera_position_by_path(self.animation_progress)
        self.progress_label.setText(f"Progress: {int(self.animation_progress * 100)}%")
    
    def _update_speed(self, value):
        self.animation_speed = value * 0.001
        self.speed_value.setText(f"Speed: {value}")
    
    def _update_opacity(self, value):
        opacity = value / 100.0
        for part in self.parts:
            if part['actor']:
                part['actor'].GetProperty().SetOpacity(opacity)
        self.opacity_value.setText(f"Opacity: {value}%")
        self.plotter.render()
    
    def _change_path_mode(self, index):
        self.animation_progress = 0.0
        self.current_path_mode = index
        self._set_camera_position_by_path(0.0)
        self.status_label.setText(f"✅ Path changed!")
    
    def _reset_view(self):
        self.animation_progress = 0.0
        
        size = self._get_heart_size()
        camera_distance = size * 2.5
        angle = np.pi / 4
        
        initial_cam_x = self.center_point[0] + camera_distance * np.cos(angle)
        initial_cam_y = self.center_point[1] + camera_distance * np.sin(angle)
        initial_cam_z = self.center_point[2] + camera_distance * 0.3
        
        self.plotter.camera.position = (initial_cam_x, initial_cam_y, initial_cam_z)
        self.plotter.camera.focal_point = tuple(self.center_point)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.render()
        
        self.opacity_slider.setValue(100)
        self._update_opacity(100)
        
        if self.is_animating:
            self._toggle_animation()
        
        self.status_label.setText("🔄 Reset complete")
        self.position_label.setText("Position: Full Heart View")


def main():
    print("\n" + "="*60)
    print("❤  HEART FLY-THROUGH VIEWER - ANATOMICAL COLORING")
    print("="*60)
    
    # Look for heart parts folder in current directory
    current_dir = os.getcwd()
    
    # Try different possible folder names
    possible_folders = [
        "heart parts",
        "Heart parts",
        "Heart Parts",
        "heart_parts",
        "Heart_parts",
        "heartparts",
        "parts"
    ]
    
    heart_parts_folder = None
    for folder_name in possible_folders:
        path = os.path.join(current_dir, folder_name)
        if os.path.isdir(path):
            # Check if folder contains .obj files
            obj_files = glob.glob(os.path.join(path, "*.obj"))
            obj_files.extend(glob.glob(os.path.join(path, "*.OBJ")))
            if obj_files:
                heart_parts_folder = path
                break
    
    if not heart_parts_folder:
        print(f"\n❌ Heart parts folder not found!")
        print(f"Looking for folders like: {', '.join(possible_folders)}")
        print(f"Current directory: {current_dir}")
        print("\nPlease ensure your heart parts folder contains individual .obj files.")
        print("Expected folder structure:")
        print("  current_directory/")
        print("  └── heart parts/")
        print("      ├── part1.obj")
        print("      ├── part2.obj")
        print("      └── ...\n")
        return
    
    print(f"\n✅ Found heart parts folder: {heart_parts_folder}")
    
    # Count OBJ files
    obj_files = glob.glob(os.path.join(heart_parts_folder, "*.obj"))
    obj_files.extend(glob.glob(os.path.join(heart_parts_folder, "*.OBJ")))
    obj_files = list(set(obj_files))
    
    print(f"✅ Found {len(obj_files)} OBJ files in the folder")
    print("🚀 Launching Heart Fly-through Viewer...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = HeartFlythrough(heart_parts_folder)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()