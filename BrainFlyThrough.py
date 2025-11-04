import os
import glob
import numpy as np
import pyvista as pv
from PyQt5 import QtWidgets, QtCore
from pyvistaqt import BackgroundPlotter
import sys

"""
🧠 Brain Fly-through Viewer - ENHANCED VERSION
Camera flies around AND inside the brain with clear inner surface exploration
"""

# Surface colors
SURFACE_COLORS = {
    'frontal':     (1.0, 0.3, 0.3),
    'parietal':    (0.3, 0.5, 1.0),
    'temporal':    (0.3, 1.0, 0.4),
    'occipital':   (1.0, 0.6, 0.2),
    'insula':      (1.0, 0.9, 0.3),
    'cerebellum':  (0.9, 0.3, 1.0),
    'cingulate':   (0.7, 0.7, 0.9),
    'default':     (0.8, 0.8, 0.8),
}


def is_surface_part(filename: str) -> bool:
    """Check if surface part"""
    name = filename.lower()
    surface_keywords = [
        'frontal', 'parietal', 'temporal', 'occipital',
        'precentral', 'postcentral', 'superior', 'middle', 'inferior',
        'cuneus', 'lingual', 'fusiform', 'angular', 'supramarginal',
        'precuneus', 'gyrus', 'lobule', 'calcarine', 'insula',
        'cingulate', 'cerebellum', 'cerebellar'
    ]
    return any(keyword in name for keyword in surface_keywords)


def classify_region(filename: str) -> str:
    """Classify region"""
    low = filename.lower()
    for k in SURFACE_COLORS.keys():
        if k in low:
            return k
    return 'default'


class EnhancedBrainFlythrough(QtWidgets.QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.parts = []
        
        # Animation state
        self.is_animating = False
        self.animation_progress = 0.0
        self.animation_speed = 0.003
        
        # Camera path parameters
        self.center_point = None
        self.brain_bounds = None
        self.current_path_mode = 4
        
        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_camera)
        self.timer.setInterval(33)
        
        self.setWindowTitle("🧠 Brain Fly-through - ENHANCED")
        self.resize(1400, 800)
        self.setStyleSheet("""
            QMainWindow { background: #1a1a1a; }
            QWidget { background: #1a1a1a; color: #ffffff; font-family: Arial; }
            QPushButton {
                background: #0d7377;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton:hover { background: #14a085; }
            QPushButton:pressed { background: #0a5a5c; }
            QLabel { color: #ffffff; font-size: 12pt; }
            QSlider::groove:horizontal {
                background: #333;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0d7377;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #14a085;
                border-radius: 4px;
            }
            QComboBox {
                background: #333;
                color: white;
                border: 2px solid #0d7377;
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
        panel.setStyleSheet("background: #2a2a2a; border-right: 2px solid #0d7377;")
        
        panel_layout = QtWidgets.QVBoxLayout()
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(20)
        panel.setLayout(panel_layout)
        
        title = QtWidgets.QLabel("🧠 Enhanced\nFly-through")
        title.setStyleSheet("font-size: 22pt; font-weight: bold; color: #14a085;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(title)
        
        mode_label = QtWidgets.QLabel("Flight Path:")
        mode_label.setStyleSheet("font-size: 14pt; margin-top: 10px;")
        panel_layout.addWidget(mode_label)
        
        self.path_combo = QtWidgets.QComboBox()
        self.path_combo.addItems([
            "🌀 Spiral Journey",
            "🔄 Circle Outside",
            "🎯 Deep Dive Inside",
            "🌊 Wave Pattern",
            "♾️ Figure-8 Path"
        ])
        self.path_combo.setCurrentIndex(4)
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
        
        opacity_label = QtWidgets.QLabel("Brain Opacity")
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
        self.status_label.setStyleSheet("color: #14a085; font-size: 11pt; margin-top: 20px;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.status_label)
        
        self.progress_label = QtWidgets.QLabel("Progress: 0%")
        self.progress_label.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.progress_label)
        
        self.position_label = QtWidgets.QLabel("Position: Full Brain View")
        self.position_label.setAlignment(QtCore.Qt.AlignCenter)
        self.position_label.setStyleSheet("color: #ffaa00; font-size: 10pt;")
        panel_layout.addWidget(self.position_label)
        
        panel_layout.addStretch()
        main_layout.addWidget(panel)
        
        # 3D Viewer
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background('#0a0a0a')
        main_layout.addWidget(self.plotter.interactor, 1)
    
    def _initialize(self):
        self.status_label.setText("Loading...")
        QtWidgets.QApplication.processEvents()
        self._load_meshes()
        self._setup_scene()
        self.status_label.setText("✅ Ready to explore!")
    
    def _load_meshes(self):
        loaded = 0
        for path in self.files:
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
                color = SURFACE_COLORS.get(region, SURFACE_COLORS['default'])
                self.parts.append({
                    'name': name,
                    'mesh': mesh,
                    'color': color,
                    'actor': None
                })
                loaded += 1
            except Exception as e:
                print(f"Error loading {path}: {e}")
        print(f"✅ Loaded {loaded} parts")
    
    def _setup_scene(self):
        if not self.parts:
            print("❌ No parts loaded!")
            return
        
        for part in self.parts:
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=1.0,
                smooth_shading=True,
                lighting=True
            )
            part['actor'] = actor
        
        self.plotter.remove_all_lights()
        
        main_light = pv.Light()
        main_light.set_direction_angle(30, 30)
        main_light.intensity = 1.0
        self.plotter.add_light(main_light)
        
        fill_light1 = pv.Light()
        fill_light1.set_direction_angle(-150, -30)
        fill_light1.intensity = 0.6
        self.plotter.add_light(fill_light1)
        
        fill_light2 = pv.Light()
        fill_light2.set_direction_angle(90, 0)
        fill_light2.intensity = 0.4
        self.plotter.add_light(fill_light2)
        
        ambient_light = pv.Light()
        ambient_light.intensity = 0.3
        self.plotter.add_light(ambient_light)
        
        bounds = self.plotter.bounds
        self.brain_bounds = bounds
        self.center_point = np.array([
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2
        ])
        
        print(f"Brain Center: {self.center_point}")
        print(f"Brain Bounds: {bounds}")
        
        camera_distance = 400
        angle = np.pi / 4
        
        initial_cam_x = self.center_point[0] + camera_distance * np.cos(angle)
        initial_cam_y = self.center_point[1] + camera_distance * np.sin(angle)
        initial_cam_z = self.center_point[2] + 100
        
        self.plotter.camera.position = (initial_cam_x, initial_cam_y, initial_cam_z)
        self.plotter.camera.focal_point = tuple(self.center_point)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.render()
        print("✅ Scene ready")
    
    def _get_camera_path_position(self, progress):
        mode = self.path_combo.currentIndex()
        if mode == 0:
            return self._spiral_journey_path(progress)
        elif mode == 1:
            return self._circle_outside_path(progress)
        elif mode == 2:
            return self._deep_dive_path(progress)
        elif mode == 3:
            return self._wave_pattern_path(progress)
        elif mode == 4:
            return self._figure8_path(progress)
        return self._circle_outside_path(progress)
    
    def _spiral_journey_path(self, t):
        cx, cy, cz = self.center_point
        if t < 0.3:
            phase_t = t / 0.3
            angle = phase_t * 4 * np.pi
            radius = 400 * (1 - phase_t)
            height = 100 * np.sin(phase_t * np.pi)
            cam_x = cx + radius * np.cos(angle)
            cam_y = cy + radius * np.sin(angle)
            cam_z = cz + height
            focal = self.center_point
            position_name = f"🌀 Spiraling In ({int(phase_t*100)}%)"
        elif t < 0.7:
            phase_t = (t - 0.3) / 0.4
            angle = phase_t * 6 * np.pi
            inner_radius = 50 + 30 * np.sin(phase_t * 4 * np.pi)
            cam_x = cx + inner_radius * np.cos(angle)
            cam_y = cy + inner_radius * np.sin(angle)
            cam_z = cz + 40 * np.sin(phase_t * 3 * np.pi)
            focal_offset = 30
            focal_x = cx + focal_offset * np.cos(angle + np.pi/4)
            focal_y = cy + focal_offset * np.sin(angle + np.pi/4)
            focal_z = cz + 20 * np.cos(phase_t * 5 * np.pi)
            focal = np.array([focal_x, focal_y, focal_z])
            position_name = f"🎯 Inside Brain ({int(phase_t*100)}%)"
        else:
            phase_t = (t - 0.7) / 0.3
            angle = (1 - phase_t) * 4 * np.pi
            radius = 400 * phase_t
            height = -100 * np.sin(phase_t * np.pi)
            cam_x = cx + radius * np.cos(angle)
            cam_y = cy + radius * np.sin(angle)
            cam_z = cz + height
            focal = self.center_point
            position_name = f"🌀 Spiraling Out ({int(phase_t*100)}%)"
        cam_pos = np.array([cam_x, cam_y, cam_z])
        up = np.array([0, 0, 1])
        return cam_pos, focal, up, position_name
    
    def _circle_outside_path(self, t):
        cx, cy, cz = self.center_point
        angle = t * 2 * np.pi
        radius = 300
        cam_x = cx + radius * np.cos(angle)
        cam_y = cy + radius * np.sin(angle)
        cam_z = cz
        return (np.array([cam_x, cam_y, cam_z]), 
                self.center_point, 
                np.array([0, 0, 1]),
                f"🔄 Orbiting ({int(t*360)}°)")
    
    def _deep_dive_path(self, t):
        cx, cy, cz = self.center_point
        if t < 0.2:
            phase_t = t / 0.2
            distance = 400 * (1 - phase_t)
            cam_pos = np.array([cx + distance, cy, cz + 100 * (1 - phase_t)])
            focal = self.center_point
            position_name = f"🚀 Approaching ({int(phase_t*100)}%)"
        elif t < 0.8:
            phase_t = (t - 0.2) / 0.6
            angle = phase_t * 8 * np.pi
            r = 60 * np.sin(phase_t * 2 * np.pi)
            cam_x = cx + r * np.cos(angle)
            cam_y = cy + r * np.sin(angle)
            cam_z = cz + 50 * np.sin(phase_t * 6 * np.pi)
            cam_pos = np.array([cam_x, cam_y, cam_z])
            focal_x = cx + 40 * np.cos(angle + np.pi/3)
            focal_y = cy + 40 * np.sin(angle + np.pi/3)
            focal_z = cz
            focal = np.array([focal_x, focal_y, focal_z])
            position_name = f"🎯 Deep Inside ({int(phase_t*100)}%)"
        else:
            phase_t = (t - 0.8) / 0.2
            distance = 400 * phase_t
            cam_pos = np.array([cx - distance, cy, cz + 100 * phase_t])
            focal = self.center_point
            position_name = f"🚀 Exiting ({int(phase_t*100)}%)"
        return cam_pos, focal, np.array([0, 0, 1]), position_name
    
    def _wave_pattern_path(self, t):
        cx, cy, cz = self.center_point
        angle = t * 4 * np.pi
        wave_amplitude = 150
        forward_distance = 300 * (2 * t - 1)
        cam_x = cx + forward_distance
        cam_y = cy + wave_amplitude * np.sin(angle)
        cam_z = cz + 100 * np.cos(angle * 0.5)
        focal_x = cx + forward_distance + 50
        focal_y = cy + wave_amplitude * np.sin(angle + 0.5)
        focal_z = cz
        return (np.array([cam_x, cam_y, cam_z]),
                np.array([focal_x, focal_y, focal_z]),
                np.array([0, 0, 1]),
                f"🌊 Wave Pattern ({int(t*100)}%)")
    
    def _figure8_path(self, t):
        cx, cy, cz = self.center_point
        z_range = self.brain_bounds[5] - self.brain_bounds[4]
        bottom_z = self.brain_bounds[4]
        
        if t < 0.15:
            phase_t = t / 0.15
            approach_distance = 500 * (1 - phase_t)
            angle_approach = phase_t * np.pi / 2
            cam_x = cx + approach_distance * np.cos(angle_approach) * 0.7
            cam_y = cy + approach_distance * np.sin(angle_approach) * 0.7
            cam_z = bottom_z - 200 + (200 * phase_t)
            focal = np.array([cx, cy, bottom_z + 30])
            position_name = f"🎯 Approaching Bottom ({int(phase_t*100)}%)"
        elif t < 0.22:
            phase_t = (t - 0.15) / 0.07
            entry_height = z_range * 0.3 * phase_t
            entry_radius = 35 * np.sin(phase_t * np.pi)
            entry_angle = phase_t * np.pi * 2
            cam_x = cx + entry_radius * np.cos(entry_angle)
            cam_y = cy + entry_radius * np.sin(entry_angle)
            cam_z = bottom_z + entry_height
            focal = np.array([
                cx + 20 * np.cos(entry_angle + np.pi/4),
                cy + 20 * np.sin(entry_angle + np.pi/4),
                cz
            ])
            position_name = f"🚪 Entering ({int(phase_t*100)}%)"
        elif t < 0.78:
            phase_t = (t - 0.22) / 0.56
            angle = phase_t * 8 * np.pi
            scale_xy = 95
            scale_z = z_range * 0.25
            denominator = 1 + np.sin(angle)**2
            cam_x = cx + (scale_xy * np.cos(angle)) / denominator
            cam_y = cy + (scale_xy * np.sin(angle) * np.cos(angle)) / denominator
            cam_z = cz + scale_z * np.sin(angle * 2) * 0.8
            look_ahead = 0.5
            future_angle = angle + look_ahead
            future_denom = 1 + np.sin(future_angle)**2
            focal_x = cx + (scale_xy * 1.15 * np.cos(future_angle)) / future_denom
            focal_y = cy + (scale_xy * 1.15 * np.sin(future_angle) * np.cos(future_angle)) / future_denom
            focal_z = cz + scale_z * np.sin(future_angle * 2) * 0.8
            focal = np.array([focal_x, focal_y, focal_z])
            wobble = 8 * np.sin(angle * 3)
            cam_x += wobble * np.cos(angle + np.pi/2)
            cam_y += wobble * np.sin(angle + np.pi/2)
            position_name = f"♾️ Exploring Inner Surface ({int(phase_t*100)}%)"
        elif t < 0.85:
            phase_t = (t - 0.78) / 0.07
            exit_height = z_range * 0.3 * (1 - phase_t)
            exit_radius = 35 * np.sin((1 - phase_t) * np.pi)
            exit_angle = np.pi + phase_t * np.pi * 2
            cam_x = cx + exit_radius * np.cos(exit_angle)
            cam_y = cy + exit_radius * np.sin(exit_angle)
            cam_z = bottom_z + exit_height
            focal = np.array([cx, cy, bottom_z - 30])
            position_name = f"🚪 Exiting ({int(phase_t*100)}%)"
        else:
            phase_t = (t - 0.85) / 0.15
            exit_distance = 500 * phase_t
            angle_exit = np.pi / 2 + phase_t * np.pi / 2
            cam_x = cx + exit_distance * np.cos(angle_exit) * 0.7
            cam_y = cy + exit_distance * np.sin(angle_exit) * 0.7
            cam_z = bottom_z - 200 * phase_t
            focal = np.array([cx, cy, cz])
            position_name = f"👋 Viewing Full Brain ({int(phase_t*100)}%)"
        cam_pos = np.array([cam_x, cam_y, cam_z])
        up = np.array([0, 0, 1])
        return cam_pos, focal, up, position_name
    
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
        if index == 4:
            camera_distance = 400
            angle = np.pi / 4
            initial_cam_x = self.center_point[0] + camera_distance * np.cos(angle)
            initial_cam_y = self.center_point[1] + camera_distance * np.sin(angle)
            initial_cam_z = self.center_point[2] + 100
            self.plotter.camera.position = (initial_cam_x, initial_cam_y, initial_cam_z)
            self.plotter.camera.focal_point = tuple(self.center_point)
            self.plotter.camera.up = (0, 0, 1)
            self.plotter.render()
            self.position_label.setText("Position: Full Brain View")
        else:
            self._set_camera_position_by_path(0.0)
        self.status_label.setText(f"✅ Path changed!")
    
    def _reset_view(self):
        self.animation_progress = 0.0
        camera_distance = 400
        angle = np.pi / 4
        initial_cam_x = self.center_point[0] + camera_distance * np.cos(angle)
        initial_cam_y = self.center_point[1] + camera_distance * np.sin(angle)
        initial_cam_z = self.center_point[2] + 100
        self.plotter.camera.position = (initial_cam_x, initial_cam_y, initial_cam_z)
        self.plotter.camera.focal_point = tuple(self.center_point)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.render()
        self.opacity_slider.setValue(100)
        self._update_opacity(100)
        if self.is_animating:
            self._toggle_animation()
        self.status_label.setText("🔄 Reset complete")
        self.position_label.setText("Position: Full Brain View")


def main():
    print("\n" + "="*60)
    print("🧠 BRAIN FLY-THROUGH VIEWER - ENHANCED VERSION")
    print("="*60)
    
    current_dir = os.getcwd()
    path = os.path.join(current_dir, "braindataset.obj")
    
    if not os.path.exists(path):
        print(f"\n❌ Folder not found: {path}\n")
        return
    
    files = glob.glob(os.path.join(path, "*.obj"))
    files.extend(glob.glob(os.path.join(path, "*.OBJ")))
    files = sorted(list(set(files)))
    
    if not files:
        print(f"\n❌ No OBJ files found\n")
        return
    
    print(f"\n✅ Found {len(files)} files")
    print("🚀 Launching Enhanced Viewer...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = EnhancedBrainFlythrough(files)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()