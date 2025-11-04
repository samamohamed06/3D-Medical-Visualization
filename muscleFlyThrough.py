import os
import glob
import numpy as np
import pyvista as pv
from PyQt5 import QtWidgets, QtCore
from pyvistaqt import BackgroundPlotter
import sys

"""
🦴 Spinal Cord Fly-through Viewer
Camera flies through the spinal cord in various paths:
- Vertical Journey (Top→Bottom→Top)
- Spiral Around Spine
- Circular Orbit
- Close Inner Exploration (INSIDE the spinal canal)
"""

# Surface colors for spinal cord components
SURFACE_COLORS = {
    'vertebra':    (0.9, 0.9, 0.85),  # Bone color
    'cervical':    (1.0, 0.3, 0.3),   # Red for cervical
    'thoracic':    (0.3, 0.5, 1.0),   # Blue for thoracic
    'lumbar':      (0.3, 1.0, 0.4),   # Green for lumbar
    'sacral':      (1.0, 0.6, 0.2),   # Orange for sacral
    'cord':        (1.0, 0.9, 0.3),   # Yellow for spinal cord
    'nerve':       (0.9, 0.3, 1.0),   # Purple for nerves
    'disc':        (0.7, 0.7, 0.9),   # Light blue for discs
    'muscle':      (0.8, 0.3, 0.3),   # Red for muscles
    'default':     (0.8, 0.8, 0.8),   # Default gray
}


def is_surface_part(filename: str) -> bool:
    """Check if file is a surface part - accepts all OBJ files"""
    name = filename.lower()
    return name.endswith('.obj')


def classify_region(filename: str) -> str:
    """Classify spinal cord region"""
    low = filename.lower()
    for k in SURFACE_COLORS.keys():
        if k in low:
            return k
    return 'default'


class SpinalCordFlythrough(QtWidgets.QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.parts = []
        
        # Animation state
        self.is_animating = False
        self.animation_progress = 0.0
        self.animation_speed = 0.003
        
        # Spinal cord path parameters
        self.center_point = None
        self.spinal_bounds = None
        self.current_path_mode = 3  # Default to Close Inner (index 3)
        
        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_camera)
        self.timer.setInterval(33)
        
        self.setWindowTitle("🦴 Spinal Cord Fly-through")
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
        
        title = QtWidgets.QLabel("🦴 Spinal Cord\nFly-through")
        title.setStyleSheet("font-size: 22pt; font-weight: bold; color: #14a085;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(title)
        
        mode_label = QtWidgets.QLabel("Flight Path:")
        mode_label.setStyleSheet("font-size: 14pt; margin-top: 10px;")
        panel_layout.addWidget(mode_label)
        
        self.path_combo = QtWidgets.QComboBox()
        self.path_combo.addItems([
            "⬇️ Vertical Journey (Outside View)",
            "🌀 Spiral Around Spine",
            "🔄 Circular Orbit",
            "🎯 INSIDE Spinal Canal"
        ])
        self.path_combo.setCurrentIndex(3)
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
        
        opacity_label = QtWidgets.QLabel("Spine Opacity")
        opacity_label.setStyleSheet("font-size: 14pt; margin-top: 20px;")
        panel_layout.addWidget(opacity_label)
        
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self._update_opacity)
        panel_layout.addWidget(self.opacity_slider)
        
        self.opacity_value = QtWidgets.QLabel("Opacity: 50%")
        self.opacity_value.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.opacity_value)
        
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #14a085; font-size: 11pt; margin-top: 20px;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.status_label)
        
        self.progress_label = QtWidgets.QLabel("Progress: 0%")
        self.progress_label.setAlignment(QtCore.Qt.AlignCenter)
        panel_layout.addWidget(self.progress_label)
        
        self.position_label = QtWidgets.QLabel("Position: Inside Spinal Canal")
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
                print(f"✅ Loaded: {name}")
            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
        print(f"\n✅ Total loaded: {loaded} parts")
    
    def _setup_scene(self):
        if not self.parts:
            print("❌ No parts loaded!")
            return
        
        for part in self.parts:
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=0.5,
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
        self.spinal_bounds = bounds
        self.center_point = np.array([
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2
        ])
        
        print(f"\nSpinal Cord Center: {self.center_point}")
        print(f"Spinal Cord Bounds: {bounds}")
        
        # Start at EXACT CENTER at the top
        initial_cam_x = self.center_point[0]
        initial_cam_y = self.center_point[1]
        initial_cam_z = self.spinal_bounds[5]
        
        self.plotter.camera.position = (initial_cam_x, initial_cam_y, initial_cam_z)
        self.plotter.camera.focal_point = (self.center_point[0], self.center_point[1], initial_cam_z - 50)
        self.plotter.camera.up = (0, 1, 0)
        self.plotter.render()
        
        print("✅ Scene ready - Starting at EXACT CENTER inside spinal canal")
    
    def _get_camera_path_position(self, progress):
        mode = self.path_combo.currentIndex()
        if mode == 0:
            return self._vertical_journey_path(progress)
        elif mode == 1:
            return self._spiral_around_path(progress)
        elif mode == 2:
            return self._circular_orbit_path(progress)
        elif mode == 3:
            return self._close_inner_path(progress)
        return self._close_inner_path(progress)
    
    def _vertical_journey_path(self, t):
        """Fixed vertical path: Top → Bottom → Top (Outside view)"""
        cx, cy, cz = self.center_point
        z_min = self.spinal_bounds[4]
        z_max = self.spinal_bounds[5]
        z_range = z_max - z_min
        
        x_range = self.spinal_bounds[1] - self.spinal_bounds[0]
        y_range = self.spinal_bounds[3] - self.spinal_bounds[2]
        offset_distance = max(x_range, y_range) * 0.8
        
        if t < 0.5:
            phase_t = t / 0.5
            cam_z = z_max - (z_range * phase_t)
            position_name = f"⬇️ Descending ({int(phase_t*100)}%)"
        else:
            phase_t = (t - 0.5) / 0.5
            cam_z = z_min + (z_range * phase_t)
            position_name = f"⬆️ Ascending ({int(phase_t*100)}%)"
        
        cam_x = cx + offset_distance
        cam_y = cy
        
        cam_pos = np.array([cam_x, cam_y, cam_z])
        focal = np.array([cx, cy, cam_z])
        up = np.array([0, 1, 0])
        
        return cam_pos, focal, up, position_name
    
    def _spiral_around_path(self, t):
        """Spiral around the spine while moving vertically"""
        cx, cy, cz = self.center_point
        z_min = self.spinal_bounds[4]
        z_max = self.spinal_bounds[5]
        z_range = z_max - z_min
        
        x_range = self.spinal_bounds[1] - self.spinal_bounds[0]
        y_range = self.spinal_bounds[3] - self.spinal_bounds[2]
        radius = max(x_range, y_range) * 0.7
        
        angle = t * 4 * np.pi
        cam_z = z_max - (z_range * t)
        
        cam_x = cx + radius * np.cos(angle)
        cam_y = cy + radius * np.sin(angle)
        
        cam_pos = np.array([cam_x, cam_y, cam_z])
        focal = np.array([cx, cy, cam_z])
        up = np.array([0, 0, 1])
        
        position_name = f"🌀 Spiraling ({int(t*100)}%)"
        return cam_pos, focal, up, position_name
    
    def _circular_orbit_path(self, t):
        """Circle around the spine at mid-height"""
        cx, cy, cz = self.center_point
        
        x_range = self.spinal_bounds[1] - self.spinal_bounds[0]
        y_range = self.spinal_bounds[3] - self.spinal_bounds[2]
        radius = max(x_range, y_range) * 1.0
        
        angle = t * 2 * np.pi
        
        cam_x = cx + radius * np.cos(angle)
        cam_y = cy + radius * np.sin(angle)
        cam_z = cz
        
        cam_pos = np.array([cam_x, cam_y, cam_z])
        focal = self.center_point
        up = np.array([0, 0, 1])
        
        position_name = f"🔄 Orbiting ({int(t*360)}°)"
        return cam_pos, focal, up, position_name
    
    def _close_inner_path(self, t):
        """
        COMPLETELY INSIDE THE SPINAL CANAL
        Camera travels through the CENTER of the spinal cord canal
        From top to bottom and back - STAYS INSIDE
        """
        cx, cy, cz = self.center_point
        z_min = self.spinal_bounds[4]
        z_max = self.spinal_bounds[5]
        z_range = z_max - z_min
        
        # Move vertically from top to bottom and back
        if t < 0.5:
            # First half: Top to Bottom
            phase_t = t / 0.5
            cam_z = z_max - (z_range * phase_t)
            focal_z = cam_z - z_range * 0.15  # Look ahead downward
            position_name = f"🎯 Inside Canal - Descending ({int(phase_t*100)}%)"
        else:
            # Second half: Bottom to Top
            phase_t = (t - 0.5) / 0.5
            cam_z = z_min + (z_range * phase_t)
            focal_z = cam_z + z_range * 0.15  # Look ahead upward
            position_name = f"🎯 Inside Canal - Ascending ({int(phase_t*100)}%)"
        
        # Camera at EXACT CENTER of the spinal cord
        cam_x = cx
        cam_y = cy
        
        # Look straight along the canal path
        focal_x = cx
        focal_y = cy
        
        cam_pos = np.array([cam_x, cam_y, cam_z])
        focal = np.array([focal_x, focal_y, focal_z])
        up = np.array([0, 1, 0])
        
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
        self._set_camera_position_by_path(0.0)
        self.status_label.setText(f"✅ Path changed!")
    
    def _reset_view(self):
        self.animation_progress = 0.0
        
        # Reset to EXACT CENTER at the top
        initial_cam_x = self.center_point[0]
        initial_cam_y = self.center_point[1]
        initial_cam_z = self.spinal_bounds[5]
        
        self.plotter.camera.position = (initial_cam_x, initial_cam_y, initial_cam_z)
        self.plotter.camera.focal_point = (self.center_point[0], self.center_point[1], initial_cam_z - 50)
        self.plotter.camera.up = (0, 1, 0)
        self.plotter.render()
        
        self.opacity_slider.setValue(50)
        self._update_opacity(50)
        
        if self.is_animating:
            self._toggle_animation()
        
        self.status_label.setText("🔄 Reset complete")
        self.position_label.setText("Position: Exact Center - Top")


def main():
    print("\n" + "="*60)
    print("🦴 SPINAL CORD FLY-THROUGH VIEWER")
    print("="*60)
    
    current_dir = os.getcwd()
    path = os.path.join(current_dir, "spinalcorddataset")
    
    if not os.path.exists(path):
        print(f"\n❌ Folder not found: {path}")
        print("Please make sure 'spinalcorddataset' folder exists in the current directory\n")
        return
    
    files = glob.glob(os.path.join(path, "*.obj"))
    files.extend(glob.glob(os.path.join(path, "*.OBJ")))
    files = sorted(list(set(files)))
    
    if not files:
        print(f"\n❌ No OBJ files found in {path}\n")
        return
    
    print(f"\n✅ Found {len(files)} OBJ files in spinalcorddataset folder")
    print("🚀 Launching Spinal Cord Viewer...")
    print("📍 Camera at EXACT CENTER - stays INSIDE throughout!\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SpinalCordFlythrough(files)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()