import pyvista as pv
import os
import glob
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from pyvistaqt import BackgroundPlotter
import vtk  # استخدم VTK مباشرة
import sys
import nibabel as nib  # ✅ إضافة nibabel لقراءة .nii

"""
🔪 Professional Brain Clipping Planes Viewer
Interactive Surgical Visualization with Multiple Clipping Planes + Slice Edges
"""

# ألوان طبية احترافية
MEDICAL_COLORS = {
    'frontal': [0.98, 0.52, 0.47],
    'parietal': [0.47, 0.68, 0.97],
    'temporal': [1.0, 0.90, 0.32],
    'occipital': [0.90, 0.54, 0.95],
    'insula': [1.0, 0.75, 0.40],
    'cerebellum': [0.55, 0.90, 0.60],
    'thalamus': [0.88, 0.42, 0.65],
    'caudate': [0.62, 0.48, 0.93],
    'putamen': [0.65, 0.50, 0.96],
    'hippocampus': [0.98, 0.80, 0.28],
    'amygdala': [0.96, 0.77, 0.25],
    'ventricle': [0.68, 0.85, 0.94],
    'default': [0.88, 0.88, 0.88]
}


def classify_part(filename):
    name = filename.lower()
    internal = {
        'ventricle': 0.40, 'thalamus': 0.80, 'caudate': 0.80,
        'putamen': 0.80, 'hippocampus': 0.85, 'amygdala': 0.85
    }
    for key, opacity in internal.items():
        if key in name:
            return key, opacity
    for region in MEDICAL_COLORS.keys():
        if region in name:
            return region, 1.0
    return 'default', 1.0


class ModernCard(QtWidgets.QFrame):
    def __init__(self, title=""):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1d2e;
                border: 1.5px solid #2d3348;
                border-radius: 14px;
                padding: 4px;
            }
        """)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        if title:
            label = QtWidgets.QLabel(title)
            label.setStyleSheet("color: #6eb6ff; font-size: 14pt; font-weight: 700;")
            layout.addWidget(label)
        self.content_layout = layout
        self.setLayout(layout)
    def addWidget(self, widget):
        self.content_layout.addWidget(widget)


class ModernSlider(QtWidgets.QWidget):
    valueChanged = QtCore.pyqtSignal(int)
    def __init__(self, label, min_val=-100, max_val=100, default=0, unit=""):
        super().__init__()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(label)
        self.label.setMinimumWidth(80)
        self.label.setStyleSheet("color: #d5dff5; font-size: 10.5pt;")
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { background: #2d3348; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #6eb6ff; width: 20px; height: 20px; margin: -7px 0; border-radius: 10px; }
            QSlider::sub-page:horizontal { background: #6eb6ff; border-radius: 3px; }
        """)
        self.slider.valueChanged.connect(self._on_change)
        self.unit = unit
        self.value_label = QtWidgets.QLabel(f"{default}{self.unit}")
        self.value_label.setMinimumWidth(60)
        self.value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.value_label.setStyleSheet("""
            color: #6eb6ff; font-weight: 700; background-color: #2d3348; padding: 6px 12px; border-radius: 8px;
        """)
        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)
        self.setLayout(layout)
    def _on_change(self, value):
        self.value_label.setText(f"{value}{self.unit}")
        self.valueChanged.emit(value)
    def value(self):
        return self.slider.value()


class ClippingPlanesViewer(QtWidgets.QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.parts = []
        # طيارات العرض والقصّ
        self.plane_actors = []
        self.vtk_planes = []
        # إبراز حواف القطع
        self.slice_actors = []
        self.all_mesh = None

        self.setWindowTitle("🔪 Professional Brain Clipping Viewer")
        self.setGeometry(40, 40, 1920, 1080)
        self.setStyleSheet(self._get_stylesheet())
        self._setup_ui()
        QtCore.QTimer.singleShot(100, self._initialize)
    
    def _get_stylesheet(self):
        return """
            * { font-family: 'Segoe UI', Arial; }
            QMainWindow, QWidget { background-color: #0d0f1a; color: #d5dff5; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6eb6ff, stop:1 #5090d3);
                color: #0d0f1a; border: none; padding: 12px 22px; border-radius: 10px; font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8ac7ff, stop:1 #6eb6ff);
            }
            QPushButton#accent { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #c47dff, stop:1 #a855f7); color: white; }
            QPushButton#danger { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff6b6b, stop:1 #ee5a5a); color: white; }
            QCheckBox { color: #d5dff5; spacing: 8px; }
            QCheckBox::indicator { width: 20px; height: 20px; border-radius: 4px; border: 2px solid #2d3348; background-color: #1a1d2e; }
            QCheckBox::indicator:checked { background-color: #6eb6ff; border-color: #6eb6ff; }
        """
    
    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        central.setLayout(layout)
        # Control Panel
        panel = self._create_panel()
        layout.addWidget(panel)
        # Viewer
        viewer_widget = QtWidgets.QWidget()
        viewer_layout = QtWidgets.QVBoxLayout()
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_widget.setLayout(viewer_layout)
        toolbar = self._create_toolbar()
        viewer_layout.addWidget(toolbar)
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background('#000000')
        viewer_layout.addWidget(self.plotter.interactor)
        layout.addWidget(viewer_widget, 1)
    
    def _create_toolbar(self):
        toolbar = QtWidgets.QFrame()
        toolbar.setStyleSheet("""
            QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1d2e, stop:1 #1f2236);
                     border-radius: 14px; border: 1.5px solid #2d3348; }
        """)
        toolbar.setFixedHeight(80)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(24, 14, 24, 14)
        toolbar.setLayout(layout)
        title = QtWidgets.QLabel("🔪 3D Brain Clipping Visualization")
        title.setStyleSheet("color: #6eb6ff; font-size: 24pt; font-weight: 800;")
        subtitle = QtWidgets.QLabel("Interactive Surgical View")
        subtitle.setStyleSheet("color: #c47dff; font-size: 12pt; font-weight: 600;")
        title_layout = QtWidgets.QVBoxLayout()
        title_layout.setSpacing(3)
        title_layout.addWidget(title); title_layout.addWidget(subtitle)
        layout.addLayout(title_layout); layout.addStretch()
        return toolbar
    
    def _create_panel(self):
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(520)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(18)
        content.setLayout(layout)

        # Header
        header = ModernCard()
        title = QtWidgets.QLabel("Clipping Control Panel")
        title.setStyleSheet("color: #6eb6ff; font-size: 18pt; font-weight: 800;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        header.addWidget(title)
        layout.addWidget(header)

        # Clipping Planes
        self._create_clipping_controls(layout)

        # Display options
        disp = ModernCard("🖼 Display Options")
        self.show_edges = QtWidgets.QCheckBox("Show intersection edges on planes")
        self.show_edges.setChecked(True)
        self.show_edges.stateChanged.connect(lambda _: self._update_intersections())
        disp.addWidget(self.show_edges)
        layout.addWidget(disp)

        # Preset Views
        presets_card = ModernCard("📐 Preset Views")
        for text, func in [
            ("🔪 Sagittal Cut (X)", lambda: self._preset_cut('x')),
            ("🔪 Coronal Cut (Y)", lambda: self._preset_cut('y')),
            ("🔪 Axial Cut (Z)", lambda: self._preset_cut('z')),
            ("🧠 Show Deep Structures", self._show_deep),
        ]:
            btn = QtWidgets.QPushButton(text)
            if "Deep" in text: btn.setObjectName("accent")
            btn.clicked.connect(func)
            presets_card.addWidget(btn)
        layout.addWidget(presets_card)

        # Actions
        actions_card = ModernCard("⚡ Quick Actions")
        reset_btn = QtWidgets.QPushButton("🔄 Reset All")
        reset_btn.clicked.connect(self._reset_all)
        actions_card.addWidget(reset_btn)
        clear_btn = QtWidgets.QPushButton("🗑 Clear Planes")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._clear_planes)
        actions_card.addWidget(clear_btn)
        layout.addWidget(actions_card)

        self.info_label = QtWidgets.QLabel("Initializing...")
        self.info_label.setStyleSheet("color: #9ba5c8;")
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info_label)

        scroll.setWidget(content)
        panel_layout = QtWidgets.QVBoxLayout()
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(scroll)
        panel.setLayout(panel_layout)
        return panel
    
    def _create_clipping_controls(self, layout):
        # X
        x_card = ModernCard("🔴 X-Axis (Sagittal)")
        self.x_enable = QtWidgets.QCheckBox("Enable X Clipping")
        self.x_enable.stateChanged.connect(lambda: self._update_clipping('x'))
        x_card.addWidget(self.x_enable)
        self.x_slider = ModernSlider("Position", -100, 100, 0)
        self.x_slider.valueChanged.connect(lambda: self._update_clipping('x'))
        x_card.addWidget(self.x_slider)
        layout.addWidget(x_card)
        # Y
        y_card = ModernCard("🟢 Y-Axis (Coronal)")
        self.y_enable = QtWidgets.QCheckBox("Enable Y Clipping")
        self.y_enable.stateChanged.connect(lambda: self._update_clipping('y'))
        y_card.addWidget(self.y_enable)
        self.y_slider = ModernSlider("Position", -100, 100, 0)
        self.y_slider.valueChanged.connect(lambda: self._update_clipping('y'))
        y_card.addWidget(self.y_slider)
        layout.addWidget(y_card)
        # Z
        z_card = ModernCard("🔵 Z-Axis (Axial)")
        self.z_enable = QtWidgets.QCheckBox("Enable Z Clipping")
        self.z_enable.stateChanged.connect(lambda: self._update_clipping('z'))
        z_card.addWidget(self.z_enable)
        self.z_slider = ModernSlider("Position", -100, 100, 0)
        self.z_slider.valueChanged.connect(lambda: self._update_clipping('z'))
        z_card.addWidget(self.z_slider)
        layout.addWidget(z_card)
    
    def _initialize(self):
        self._load_brain()
        self._setup_scene()
    
    def _load_brain(self):
        print("\n🧠 Loading dental data...")
        self.info_label.setText("⏳ Loading dental.nii...")
        QtWidgets.QApplication.processEvents()
        
        # ✅ قراءة dental.nii
        for i, path in enumerate(self.files):
            try:
                # ✅ تحقق إذا كان الملف .nii
                if path.lower().endswith('.nii') or path.lower().endswith('.nii.gz'):
                    nii = nib.load(path)
                    data = nii.get_fdata()
                    
                    print(f"  ✓ Shape: {data.shape}")
                    print(f"  ✓ Data range: [{data.min():.2f}, {data.max():.2f}]")
                    
                    # تحويل إلى PyVista mesh
                    grid = pv.ImageData(dimensions=data.shape)
                    grid['values'] = data.flatten(order='F')
                    
                    threshold = data.mean() + data.std() * 0.5
                    print(f"  ✓ Threshold: {threshold:.2f}")
                    
                    mesh = grid.threshold(value=threshold, scalars='values')
                    
                    if mesh.n_points == 0:
                        print(f"  ⚠ Threshold empty, trying contour...")
                        mesh = grid.contour(isosurfaces=3, scalars='values')
                    
                    print(f"  ✓ Initial points: {mesh.n_points}")
                    
                    # تبسيط
                    if mesh.n_points > 100000:
                        print(f"  ⚙ Simplifying mesh...")
                        mesh = mesh.extract_geometry()
                        print(f"      After extract_geometry: {mesh.n_points} points")
                        
                        if mesh.n_points > 50000:
                            print(f"      Converting to triangles...")
                            mesh = mesh.triangulate()
                            print(f"      After triangulate: {mesh.n_points} points")
                            
                            print(f"      Decimating...")
                            mesh = mesh.decimate(0.85)
                            print(f"      After decimate: {mesh.n_points} points")
                    
                    mesh = mesh.compute_normals()
                    
                    name = os.path.basename(path)
                    region, opacity = classify_part(name)
                    color = MEDICAL_COLORS.get(region, MEDICAL_COLORS['default'])
                    
                    self.parts.append({
                        'mesh': mesh,
                        'name': name,
                        'region': region,
                        'color': color,
                        'opacity': opacity,
                        'actor': None
                    })
                    
                    print(f"✅ Loaded dental.nii with {mesh.n_points} points")
                else:
                    # ✅ لو مش .nii، اقرأه عادي (للتوافق)
                    mesh = pv.read(path)
                    if mesh.n_points == 0:
                        continue
                    if mesh.n_points > 100:
                        mesh = mesh.smooth(n_iter=5, relaxation_factor=0.05)
                    mesh = mesh.compute_normals()
                    name = os.path.basename(path)
                    region, opacity = classify_part(name)
                    color = MEDICAL_COLORS.get(region, MEDICAL_COLORS['default'])
                    self.parts.append({
                        'mesh': mesh,
                        'name': name,
                        'region': region,
                        'color': color,
                        'opacity': opacity,
                        'actor': None
                    })
                
                if (i + 1) % 15 == 0:
                    self.info_label.setText(f"⏳ {i + 1}/{len(self.files)}")
                    QtWidgets.QApplication.processEvents()
            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
                pass
        
        print(f"✅ Loaded {len(self.parts)} parts")
    
    def _setup_scene(self):
        if not self.parts:
            return
        print("🎨 Setting up scene...")
        for part in self.parts:
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=part['opacity'],
                smooth_shading=True,
                pbr=True,
                metallic=0.03,
                roughness=0.55,
                ambient=0.40,
                diffuse=0.88,
                specular=0.65
            )
            part['actor'] = actor
        # Lights
        for pos, intensity, color in [
            ((1000, 800, 1200), 2.2, [1, 1, 1]),
            ((-700, 600, 800), 1.6, [0.98, 0.99, 1]),
            ((600, -400, 700), 1.4, [1, 0.99, 0.98]),
            ((0, 0, -1000), 1.8, [1, 1, 1]),
        ]:
            light = pv.Light(position=pos, light_type='scene light')
            light.intensity = intensity
            light.diffuse_color = color
            self.plotter.add_light(light)
        self.plotter.enable_anti_aliasing('ssaa')
        self.plotter.enable_depth_peeling(10)
        self.plotter.reset_camera()
        self.plotter.camera.elevation = 20
        self.plotter.camera.azimuth = 30
        self.plotter.camera.zoom(1.25)
        # اجمع كل الأجزاء في Mesh واحد لاستخراج حواف التقاطع بسرعة
        try:
            self.all_mesh = pv.append_polydata([p['mesh'] for p in self.parts]).clean().triangulate()
        except Exception:
            # احتياطي
            base = self.parts[0]['mesh'].copy()
            for p in self.parts[1:]:
                try:
                    base = base.merge(p['mesh'])
                except Exception:
                    pass
            self.all_mesh = base.clean().triangulate()
        self.info_label.setText(f"✅ {len(self.parts)} loaded\n🔪 Use sliders to clip")
        print("✅ Ready!\n")
    
    def _update_clipping(self, axis):
        # امسح طيارات العرض القديمة
        for a in self.plane_actors:
            try: self.plotter.remove_actor(a)
            except Exception: pass
        self.plane_actors = []

        bounds = self.plotter.bounds
        center = [
            (bounds[0] + bounds[1]) / 2.0,
            (bounds[2] + bounds[3]) / 2.0,
            (bounds[4] + bounds[5]) / 2.0,
        ]

        # حدّد الطيارات الفعلية
        self.vtk_planes = []
        # أحجام طيارات العرض
        size_x = (bounds[1] - bounds[0]) * 1.6
        size_y = (bounds[3] - bounds[2]) * 1.6
        size_z = (bounds[5] - bounds[4]) * 1.6

        plane_vis_style = dict(opacity=0.35, smooth_shading=True, pbr=True,
                               metallic=0.0, roughness=0.9, ambient=0.6, diffuse=0.4, specular=0.1)

        # X
        if self.x_enable.isChecked():
            pos = center[0] + (self.x_slider.value() / 100.0) * (bounds[1] - bounds[0]) / 2.0
            x_plane = vtk.vtkPlane(); x_plane.SetOrigin(pos, center[1], center[2]); x_plane.SetNormal(1.0, 0.0, 0.0)
            self.vtk_planes.append(x_plane)
            vis = pv.Plane(center=[pos, center[1], center[2]], direction=[1, 0, 0], i_size=size_y, j_size=size_z)
            a = self.plotter.add_mesh(vis, color='#bfbfbf', **plane_vis_style)
            self.plane_actors.append(a)

        # Y
        if self.y_enable.isChecked():
            pos = center[1] + (self.y_slider.value() / 100.0) * (bounds[3] - bounds[2]) / 2.0
            y_plane = vtk.vtkPlane(); y_plane.SetOrigin(center[0], pos, center[2]); y_plane.SetNormal(0.0, 1.0, 0.0)
            self.vtk_planes.append(y_plane)
            vis = pv.Plane(center=[center[0], pos, center[2]], direction=[0, 1, 0], i_size=size_x, j_size=size_z)
            a = self.plotter.add_mesh(vis, color='#bfbfbf', **plane_vis_style)
            self.plane_actors.append(a)

        # Z
        if self.z_enable.isChecked():
            pos = center[2] + (self.z_slider.value() / 100.0) * (bounds[5] - bounds[4]) / 2.0
            z_plane = vtk.vtkPlane(); z_plane.SetOrigin(center[0], center[1], pos); z_plane.SetNormal(0.0, 0.0, 1.0)
            self.vtk_planes.append(z_plane)
            vis = pv.Plane(center=[center[0], center[1], pos], direction=[0, 0, 1], i_size=size_x, j_size=size_y)
            a = self.plotter.add_mesh(vis, color='#bfbfbf', **plane_vis_style)
            self.plane_actors.append(a)

        # طبّق القصّ على مستوى المابر
        for part in self.parts:
            actor = part.get('actor')
            if not actor: continue
            try:
                mapper = actor.GetMapper() if hasattr(actor, "GetMapper") else getattr(actor, "mapper", None)
                if mapper is None: continue
                if hasattr(mapper, "RemoveAllClippingPlanes"):
                    mapper.RemoveAllClippingPlanes()
                for pl in self.vtk_planes:
                    mapper.AddClippingPlane(pl)
            except Exception:
                pass

        # حدّث إبراز حواف التقاطع
        self._update_intersections()
        self.plotter.render()
    
    def _update_intersections(self):
        # إزالة الحواف القديمة
        for a in self.slice_actors:
            try: self.plotter.remove_actor(a)
            except Exception: pass
        self.slice_actors = []

        if not self.show_edges.isChecked() or self.all_mesh is None or len(self.vtk_planes) == 0:
            self.plotter.render(); return

        bounds = self.plotter.bounds
        diag = np.linalg.norm([bounds[1]-bounds[0], bounds[3]-bounds[2], bounds[5]-bounds[4]])
        radius = max(diag * 0.002, 0.25)  # سمك الخط

        for pl in self.vtk_planes:
            origin = list(pl.GetOrigin()); normal = list(pl.GetNormal())
            try:
                slc = self.all_mesh.slice(origin=origin, normal=normal)
            except Exception:
                continue
            if slc.n_points < 2:
                continue
            tubes = slc.tube(radius=radius, capping=True, n_sides=32)
            a = self.plotter.add_mesh(
                tubes, color='#f0f0f0', ambient=0.7, diffuse=0.25, specular=0.2, smooth_shading=True
            )
            self.slice_actors.append(a)

    def _preset_cut(self, axis):
        self._clear_planes()
        if axis == 'x':
            self.x_enable.setChecked(True); self.x_slider.slider.setValue(0)
        elif axis == 'y':
            self.y_enable.setChecked(True); self.y_slider.slider.setValue(0)
        elif axis == 'z':
            self.z_enable.setChecked(True); self.z_slider.slider.setValue(0)
    
    def _show_deep(self):
        deep = ['thalamus', 'caudate', 'putamen', 'hippocampus', 'amygdala']
        for part in self.parts:
            if part['actor']:
                if any(d in part['name'].lower() for d in deep):
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(part['opacity'])
                else:
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(0.05)
        self.plotter.render()
    
    def _reset_all(self):
        self._clear_planes()
        for part in self.parts:
            if part['actor']:
                part['actor'].SetVisibility(True)
                part['actor'].GetProperty().SetOpacity(part['opacity'])
        self.plotter.reset_camera()
        self.plotter.camera.elevation = 20
        self.plotter.camera.azimuth = 30
        self.plotter.camera.zoom(1.25)
        self.plotter.render()
    
    def _clear_planes(self):
        self.x_enable.setChecked(False); self.y_enable.setChecked(False); self.z_enable.setChecked(False)
        self.x_slider.slider.setValue(0); self.y_slider.slider.setValue(0); self.z_slider.slider.setValue(0)
        for a in self.plane_actors:
            try: self.plotter.remove_actor(a)
            except Exception: pass
        self.plane_actors = []; self.vtk_planes = []
        for a in self.slice_actors:
            try: self.plotter.remove_actor(a)
            except Exception: pass
        self.slice_actors = []
        # أزل طيارات القصّ من المابرز
        for part in self.parts:
            actor = part.get('actor')
            if not actor: continue
            try:
                mapper = actor.GetMapper() if hasattr(actor, "GetMapper") else getattr(actor, "mapper", None)
                if mapper and hasattr(mapper, "RemoveAllClippingPlanes"):
                    mapper.RemoveAllClippingPlanes()
            except Exception:
                pass
        self.plotter.render()


def main():
    print("\n" + "="*70)
    print("🔪 PROFESSIONAL BRAIN CLIPPING VIEWER")
    print("="*70)
    
    # ✅ تحديد مسار dental.nii تلقائياً
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "dental.nii")
    
    print(f"\n📁 Looking for dental.nii at: {path}")
    
    if not os.path.exists(path):
        print(f"\n❌ File 'dental.nii' not found at: {path}")
        print("Please make sure 'dental.nii' exists in the same directory as this script.\n")
        return
    
    files = [path]  # ✅ ملف واحد فقط
    
    print(f"\n✅ Found dental.nii")
    print("🚀 Launching...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ClippingPlanesViewer(files)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()