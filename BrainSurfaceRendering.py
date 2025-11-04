import pyvista as pv
import os
import glob
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from pyvistaqt import BackgroundPlotter
import sys

"""
🧠 Professional Brain Viewer - Surface Only Edition
Cortical Surface Visualization
"""

# Enhanced VIBRANT color palette for surface regions
COLORS = {
    'frontal': [1.0, 0.2, 0.2],              # Very Bright Red
    'precentral': [0.98, 0.3, 0.25],
    'superior_frontal': [0.95, 0.25, 0.18],
    'middle_frontal': [0.97, 0.28, 0.22],
    'inferior_frontal': [0.96, 0.22, 0.15],
    'orbital': [1.0, 0.35, 0.30],
    
    'parietal': [0.1, 0.5, 1.0],             # Very Bright Blue
    'postcentral': [0.15, 0.55, 0.98],
    'superior_parietal': [0.2, 0.6, 1.0],
    'precuneus': [0.12, 0.48, 0.95],
    'angular': [0.22, 0.62, 1.0],
    'supramarginal': [0.18, 0.58, 0.98],
    
    'temporal': [0.2, 0.95, 0.25],           # Very Bright Green
    'superior_temporal': [0.3, 0.98, 0.35],
    'middle_temporal': [0.25, 0.96, 0.30],
    'inferior_temporal': [0.18, 0.92, 0.22],
    'fusiform': [0.35, 1.0, 0.40],
    'parahippocampal': [0.40, 1.0, 0.45],
    
    'occipital': [1.0, 0.55, 0.0],           # Very Bright Orange
    'cuneus': [1.0, 0.6, 0.1],
    'lingual': [1.0, 0.52, 0.0],
    'calcarine': [0.98, 0.5, 0.0],
    
    'insula': [1.0, 0.9, 0.1],               # Very Bright Yellow
    'cingulate': [0.98, 0.85, 0.08],
    
    'cerebellum': [0.85, 0.15, 0.95],        # Very Bright Purple
    'cerebellar': [0.85, 0.15, 0.95],
    
    'default': [0.9, 0.9, 0.9]               # Bright Gray
}


def is_surface_part(filename):
    """Check if this is a surface (cortical) part"""
    name = filename.lower()
    
    # Define surface structures
    surface_keywords = [
        'frontal', 'parietal', 'temporal', 'occipital',
        'precentral', 'postcentral', 'superior', 'middle', 'inferior',
        'cuneus', 'lingual', 'fusiform', 'angular', 'supramarginal',
        'precuneus', 'gyrus', 'lobule', 'calcarine', 'insula',
        'cingulate', 'cerebellum', 'cerebellar'
    ]
    
    # Check if any surface keyword is in the filename
    return any(keyword in name for keyword in surface_keywords)


def classify_part(filename):
    """Classify brain part and assign color"""
    name = filename.lower()
    
    for region in COLORS.keys():
        if region in name:
            return region, 1.0  # Full opacity for all surface parts
    
    return 'default', 1.0


class ModernCard(QtWidgets.QFrame):
    """Material Design 3 Card Widget"""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet("""
            ModernCard {
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
            title_label = QtWidgets.QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    color: #6eb6ff;
                    font-size: 14pt;
                    font-weight: 700;
                    padding-bottom: 10px;
                    letter-spacing: 0.5px;
                }
            """)
            layout.addWidget(title_label)
        
        self.content_layout = layout
        self.setLayout(layout)
    
    def addWidget(self, widget):
        self.content_layout.addWidget(widget)
    
    def addLayout(self, layout):
        self.content_layout.addLayout(layout)


class ModernSlider(QtWidgets.QWidget):
    """Material Design 3 Slider with value display"""
    valueChanged = QtCore.pyqtSignal(int)
    
    def __init__(self, label, min_val=0, max_val=100, default=100, unit="%"):
        super().__init__()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        
        self.label = QtWidgets.QLabel(label)
        self.label.setMinimumWidth(140)
        self.label.setStyleSheet("color: #d5dff5; font-size: 10.5pt; font-weight: 500;")
        
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2d3348;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #6eb6ff;
                width: 20px;
                height: 20px;
                margin: -7px 0;
                border-radius: 10px;
                border: 2px solid #5090d3;
            }
            QSlider::handle:horizontal:hover {
                background: #8ac7ff;
                border-color: #6eb6ff;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6eb6ff, stop:1 #8ac7ff);
                border-radius: 3px;
            }
        """)
        self.slider.valueChanged.connect(self._on_change)
        
        self.unit = unit
        self.value_label = QtWidgets.QLabel(f"{default}{unit}")
        self.value_label.setMinimumWidth(60)
        self.value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.value_label.setStyleSheet("""
            QLabel {
                color: #6eb6ff;
                font-size: 11pt;
                font-weight: 700;
                background-color: #2d3348;
                padding: 6px 12px;
                border-radius: 8px;
            }
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
    
    def setValue(self, value):
        self.slider.setValue(value)


class BrainSurfaceViewer(QtWidgets.QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.parts = []
        
        self.setWindowTitle("🧠 Brain Surface Viewer - Cortex Only")
        self.setGeometry(40, 40, 1920, 1080)
        
        self.setStyleSheet(self._get_material_stylesheet())
        
        self._setup_ui()
        QtCore.QTimer.singleShot(100, self._initialize_brain)
    
    def _get_material_stylesheet(self):
        """Enhanced Material Design 3 Dark Theme"""
        return """
            * {
                font-family: 'Segoe UI', 'San Francisco', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            }
            QMainWindow {
                background-color: #0d0f1a;
            }
            QWidget {
                background-color: #0d0f1a;
                color: #d5dff5;
                font-size: 10.5pt;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6eb6ff, stop:1 #5090d3);
                color: #0d0f1a;
                border: none;
                padding: 12px 22px;
                border-radius: 10px;
                font-weight: 700;
                font-size: 10.5pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8ac7ff, stop:1 #6eb6ff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5090d3, stop:1 #4080c3);
            }
            QPushButton:disabled {
                background: #2d3348;
                color: #6b7394;
            }
            QPushButton#accentButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c47dff, stop:1 #a855f7);
                color: #ffffff;
            }
            QPushButton#accentButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d89fff, stop:1 #c47dff);
            }
            QPushButton#regionButton {
                background-color: #1a1d2e;
                border: 2px solid #2d3348;
                padding: 10px 16px;
                color: #d5dff5;
            }
            QPushButton#regionButton:hover {
                background-color: #252840;
                border-color: #6eb6ff;
            }
            QPushButton#regionButton:pressed {
                background-color: #2d3348;
            }
            QGroupBox {
                border: none;
                background-color: #1a1d2e;
                border-radius: 14px;
                margin-top: 10px;
                padding: 18px;
                font-weight: 700;
                color: #6eb6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 10px;
                color: #6eb6ff;
                font-size: 12pt;
            }
            QListWidget {
                background-color: #1a1d2e;
                border: 1.5px solid #2d3348;
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }
            QListWidget::item {
                padding: 11px;
                border-radius: 8px;
                margin: 3px 0;
                color: #d5dff5;
            }
            QListWidget::item:hover {
                background-color: #252840;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6eb6ff, stop:1 #8ac7ff);
                color: #0d0f1a;
                font-weight: 700;
            }
            QLineEdit {
                background-color: #1a1d2e;
                border: 2px solid #2d3348;
                border-radius: 10px;
                padding: 11px 16px;
                color: #d5dff5;
                selection-background-color: #6eb6ff;
                font-size: 10.5pt;
            }
            QLineEdit:focus {
                border-color: #6eb6ff;
                background-color: #1f2236;
            }
            QLineEdit::placeholder {
                color: #6b7394;
            }
            QLabel {
                color: #d5dff5;
            }
            QLabel#titleLabel {
                color: #6eb6ff;
                font-size: 24pt;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QLabel#subtitleLabel {
                color: #c47dff;
                font-size: 12pt;
                font-weight: 600;
            }
            QLabel#infoLabel {
                color: #9ba5c8;
                font-size: 9.5pt;
                line-height: 1.6;
            }
            QScrollBar:vertical {
                background: #1a1d2e;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #3d4562;
                border-radius: 7px;
                min-height: 35px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4d5572;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QComboBox {
                background-color: #1a1d2e;
                border: 2px solid #2d3348;
                border-radius: 10px;
                padding: 9px 16px;
                min-width: 140px;
                color: #d5dff5;
                font-weight: 600;
            }
            QComboBox:hover {
                border-color: #6eb6ff;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 12px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6eb6ff;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1d2e;
                border: 1.5px solid #2d3348;
                border-radius: 10px;
                padding: 6px;
                selection-background-color: #6eb6ff;
                selection-color: #0d0f1a;
                outline: none;
            }
            QToolTip {
                background-color: #2d3348;
                color: #d5dff5;
                border: 1px solid #3d4562;
                border-radius: 8px;
                padding: 8px;
                font-size: 10pt;
            }
        """
    
    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)
        central.setLayout(main_layout)
        
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        viewer_widget = QtWidgets.QWidget()
        viewer_layout = QtWidgets.QVBoxLayout()
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(14)
        viewer_widget.setLayout(viewer_layout)
        
        toolbar = self._create_toolbar()
        viewer_layout.addWidget(toolbar)
        
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background('#000000')
        viewer_layout.addWidget(self.plotter.interactor)
        
        main_layout.addWidget(viewer_widget, 1)
    
    def _create_toolbar(self):
        toolbar = QtWidgets.QFrame()
        toolbar.setFrameShape(QtWidgets.QFrame.StyledPanel)
        toolbar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1d2e, stop:1 #1f2236);
                border-radius: 14px;
                border: 1.5px solid #2d3348;
            }
        """)
        toolbar.setFixedHeight(80)
        
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(24, 14, 24, 14)
        toolbar.setLayout(layout)
        
        title_container = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(3)
        
        title = QtWidgets.QLabel("🧠 Brain Surface Visualization")
        title.setObjectName("titleLabel")
        subtitle = QtWidgets.QLabel("Cortical Surface Only")
        subtitle.setObjectName("subtitleLabel")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_container.setLayout(title_layout)
        layout.addWidget(title_container)
        
        layout.addStretch()
        
        quality_label = QtWidgets.QLabel("Rendering Quality:")
        quality_label.setStyleSheet("color: #d5dff5; font-weight: 600; font-size: 11pt;")
        layout.addWidget(quality_label)
        
        self.quality_combo = QtWidgets.QComboBox()
        self.quality_combo.addItems(["🔥 Ultra", "⚡ High", "💎 Medium", "🚀 Performance"])
        self.quality_combo.setCurrentIndex(1)
        self.quality_combo.currentIndexChanged.connect(self._change_quality)
        layout.addWidget(self.quality_combo)
        
        return toolbar
    
    def _create_control_panel(self):
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(480)
        
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(18)
        content.setLayout(layout)
        
        header_card = ModernCard()
        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setSpacing(5)
        
        header_title = QtWidgets.QLabel("Surface Control Panel")
        header_title.setObjectName("titleLabel")
        header_title.setAlignment(QtCore.Qt.AlignCenter)
        
        header_subtitle = QtWidgets.QLabel("Cortical visualization settings")
        header_subtitle.setObjectName("infoLabel")
        header_subtitle.setAlignment(QtCore.Qt.AlignCenter)
        
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)
        header_card.addLayout(header_layout)
        layout.addWidget(header_card)
        
        opacity_card = ModernCard("🎚️ Opacity Control")
        
        self.global_slider = ModernSlider("Surface Opacity", 0, 100, 100)
        self.global_slider.valueChanged.connect(self._update_global_opacity)
        opacity_card.addWidget(self.global_slider)
        
        layout.addWidget(opacity_card)
        
        modes_card = ModernCard("👁️ View Modes")
        
        view_buttons = [
            ("🔄 Reset View", self._reset_view, ""),
            ("🌐 Show All", self._show_all, ""),
        ]
        
        for text, callback, style_id in view_buttons:
            btn = QtWidgets.QPushButton(text)
            if style_id:
                btn.setObjectName(style_id)
            btn.clicked.connect(callback)
            modes_card.addWidget(btn)
        
        layout.addWidget(modes_card)
        
        regions_card = ModernCard("🎨 Cortical Lobes")
        regions_grid = QtWidgets.QGridLayout()
        regions_grid.setSpacing(10)
        
        regions = [
            ("🔴 Frontal", 'frontal'),
            ("🔵 Parietal", 'parietal'),
            ("🟢 Temporal", 'temporal'),
            ("🟠 Occipital", 'occipital'),
            ("🟡 Insula", 'insula'),
            ("🟣 Cerebellum", 'cerebellum'),
        ]
        
        for i, (text, region) in enumerate(regions):
            btn = QtWidgets.QPushButton(text)
            btn.setObjectName("regionButton")
            btn.clicked.connect(lambda checked, r=region: self._show_region(r))
            regions_grid.addWidget(btn, i // 2, i % 2)
        
        regions_card.addLayout(regions_grid)
        layout.addWidget(regions_card)
        
        list_card = ModernCard("📋 Surface Structures")
        
        search_layout = QtWidgets.QHBoxLayout()
        search_icon = QtWidgets.QLabel("🔍")
        search_icon.setStyleSheet("font-size: 15pt;")
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search cortical structures...")
        self.search_box.textChanged.connect(self._filter_parts)
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_box)
        list_card.addLayout(search_layout)
        
        self.parts_list = QtWidgets.QListWidget()
        self.parts_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.parts_list.itemDoubleClicked.connect(self._on_item_double_click)
        list_card.addWidget(self.parts_list)
        
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_show = QtWidgets.QPushButton("👁️ Show")
        btn_show.clicked.connect(self._show_selected)
        btn_hide = QtWidgets.QPushButton("🚫 Hide")
        btn_hide.clicked.connect(self._hide_selected)
        btn_isolate = QtWidgets.QPushButton("🎯 Isolate")
        btn_isolate.setObjectName("accentButton")
        btn_isolate.clicked.connect(self._isolate_selected)
        
        btn_layout.addWidget(btn_show)
        btn_layout.addWidget(btn_hide)
        btn_layout.addWidget(btn_isolate)
        list_card.addLayout(btn_layout)
        
        layout.addWidget(list_card)
        
        self.info_label = QtWidgets.QLabel("Initializing surface viewer...")
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        scroll.setWidget(content)
        
        panel_layout = QtWidgets.QVBoxLayout()
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(scroll)
        panel.setLayout(panel_layout)
        
        return panel
    
    def _initialize_brain(self):
        self._load_brain()
        self._setup_scene()
    
    def _load_brain(self):
        print("\n🧠 Loading cortical surface meshes...")
        self.info_label.setText("⏳ Loading surface structures...")
        QtWidgets.QApplication.processEvents()
        
        skipped = 0
        loaded = 0
        surface_only = 0
        
        for i, path in enumerate(self.files):
            try:
                # Check if this is a surface part BEFORE loading
                if not is_surface_part(os.path.basename(path)):
                    skipped += 1
                    continue
                
                # Load only surface parts
                mesh = pv.read(path)
                
                # Check if mesh is valid
                if mesh.n_points == 0 or mesh.n_cells == 0:
                    print(f"  ⚠️ Empty mesh: {os.path.basename(path)}")
                    skipped += 1
                    continue
                
                # ZERO SMOOTHING - Maximum detail preservation
                if mesh.n_points >= 100:
                    mesh = mesh.clean(tolerance=0.0)
                
                # Enhanced normal computation
                mesh = mesh.compute_normals(cell_normals=False, point_normals=True, 
                                           feature_angle=15, auto_orient_normals=True)
                
                name = os.path.basename(path)
                region, opacity = classify_part(name)
                color = COLORS.get(region, COLORS['default'])
                
                self.parts.append({
                    'mesh': mesh,
                    'name': name,
                    'region': region,
                    'color': color,
                    'base_opacity': opacity,
                    'current_opacity': opacity,
                    'actor': None,
                    'visible': True
                })
                
                loaded += 1
                surface_only += 1
                
                if (loaded) % 10 == 0:
                    print(f"  ✓ Loaded: {loaded} surface parts")
                    self.info_label.setText(f"⏳ Loading {loaded} surface structures...")
                    QtWidgets.QApplication.processEvents()
                    
            except Exception as e:
                print(f"  ⚠️ Error loading {os.path.basename(path)}: {str(e)}")
                skipped += 1
        
        print(f"\n✅ Loaded {surface_only} cortical surface parts")
        print(f"⏭️  Skipped {skipped} non-surface structures")
        
        if loaded == 0:
            print("\n❌ ERROR: No surface files loaded!")
            
        self._update_parts_list()
    
    def _setup_scene(self):
        if len(self.parts) == 0:
            self.info_label.setText("❌ No surface parts loaded!")
            print("❌ Cannot setup scene - no parts loaded!")
            return
            
        print("🎨 Setting up surface scene...")
        self.info_label.setText("🎨 Rendering cortical surface...")
        QtWidgets.QApplication.processEvents()
        
        for i, part in enumerate(self.parts):
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=part['base_opacity'],
                smooth_shading=True,
                pbr=True,
                metallic=0.0,
                roughness=0.60,
                ambient=0.60,
                diffuse=0.95,
                specular=0.70,
                specular_power=100,
                interpolate_before_map=True
            )
            part['actor'] = actor
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/{len(self.parts)}")
                self.info_label.setText(f"🎨 Rendering {i + 1}/{len(self.parts)}...")
                QtWidgets.QApplication.processEvents()
        
        # Enhanced lighting
        lights = [
            (( 900,  800,  900), 2.5, [1.0, 1.0, 1.0]),
            ((-700,  700,  800), 1.8, [0.95, 0.98, 1.0]),
            ((   0, -600, -700), 1.2, [1.0, 0.98, 0.95]),
            (( 600, -500,  600), 1.5, [1.0, 1.0, 1.0]),
            ((   0,    0, -900), 1.6, [0.98, 0.98, 1.0])
        ]
        
        for pos, intensity, color in lights:
            light = pv.Light(position=pos, light_type='scene light')
            light.intensity = intensity
            light.diffuse_color = color
            self.plotter.add_light(light)
        
        self.plotter.enable_anti_aliasing('ssaa')
        self.plotter.enable_depth_peeling(number_of_peels=8)
        self.plotter.enable_ssao(kernel_size=128, radius=0.5, bias=0.01, blur=True)
        
        self.plotter.reset_camera()
        self.plotter.camera.elevation = 18
        self.plotter.camera.azimuth = 28
        self.plotter.camera.zoom(1.15)
        
        self.plotter.enable_mesh_picking(callback=self._on_mesh_click, show_message=True, use_actor=True)
        
        info_text = f"""✅ {len(self.parts)} surface structures loaded
🖱️ Click parts to isolate
🔍 Search by name
🎨 Cortical surface only"""
        self.info_label.setText(info_text)
        print("✅ Surface scene ready!\n")
    
    def _change_quality(self, index):
        settings = {
            0: {'aa': 'ssaa', 'peels': 10, 'ssao': 256},
            1: {'aa': 'ssaa', 'peels': 8, 'ssao': 128},
            2: {'aa': 'msaa', 'peels': 6, 'ssao': 64},
            3: {'aa': 'fxaa', 'peels': 4, 'ssao': 32},
        }
        s = settings[index]
        
        self.plotter.disable_anti_aliasing()
        self.plotter.enable_anti_aliasing(s['aa'])
        self.plotter.disable_depth_peeling()
        self.plotter.enable_depth_peeling(number_of_peels=s['peels'])
        print(f"Quality: {self.quality_combo.currentText()}")
    
    def _update_parts_list(self, filter_text=""):
        self.parts_list.clear()
        for part in self.parts:
            if filter_text.lower() in part['name'].lower():
                icon = '✓' if part['visible'] else '✗'
                opacity_bar = '█' * int(part['current_opacity'] * 5)
                self.parts_list.addItem(f"{icon} {part['name'][:52]} {opacity_bar}")
    
    def _filter_parts(self):
        self._update_parts_list(self.search_box.text())
    
    def _on_mesh_click(self, actor):
        for part in self.parts:
            if part['actor'] == actor:
                print(f"🎯 {part['name']}")
                self._isolate_part(part)
                break
    
    def _on_item_double_click(self, item):
        text = item.text()
        name = text.split('█')[0][2:].strip()
        for part in self.parts:
            if part['name'].startswith(name) or name in part['name']:
                self._isolate_part(part)
                break
    
    def _isolate_part(self, target):
        for part in self.parts:
            if part['actor']:
                if part == target:
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(1.0)
                    part['current_opacity'] = 1.0
                    part['visible'] = True
                else:
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(0.02)
                    part['current_opacity'] = 0.02
                    part['visible'] = False
        self._update_parts_list()
        self.plotter.render()
    
    def _show_region(self, region):
        for part in self.parts:
            if part['actor']:
                if region in part['region']:
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(part['base_opacity'])
                    part['current_opacity'] = part['base_opacity']
                    part['visible'] = True
                else:
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(0.04)
                    part['current_opacity'] = 0.04
                    part['visible'] = False
        self._update_parts_list()
        self.plotter.render()
    
    def _show_all(self):
        for part in self.parts:
            part['visible'] = True
            part['current_opacity'] = part['base_opacity']
            if part['actor']:
                part['actor'].SetVisibility(True)
                part['actor'].GetProperty().SetOpacity(part['base_opacity'])
        self._update_parts_list()
        self.plotter.render()
    
    def _reset_view(self):
        self._show_all()
        self.global_slider.setValue(100)
        self.plotter.reset_camera()
        self.plotter.camera.elevation = 18
        self.plotter.camera.azimuth = 28
        self.plotter.camera.zoom(1.15)
        self.plotter.render()
    
    def _update_global_opacity(self, value):
        factor = value / 100.0
        for part in self.parts:
            if part['actor'] and part['visible']:
                new_opacity = part['base_opacity'] * factor
                part['actor'].GetProperty().SetOpacity(new_opacity)
                part['current_opacity'] = new_opacity
        self.plotter.render()
    
    def _show_selected(self):
        for item in self.parts_list.selectedItems():
            text = item.text()
            name = text.split('█')[0][2:].strip()
            for part in self.parts:
                if part['name'].startswith(name) or name in part['name']:
                    if part['actor']:
                        part['actor'].SetVisibility(True)
                        part['actor'].GetProperty().SetOpacity(part['base_opacity'])
                        part['current_opacity'] = part['base_opacity']
                        part['visible'] = True
        self._update_parts_list()
        self.plotter.render()
    
    def _hide_selected(self):
        for item in self.parts_list.selectedItems():
            text = item.text()
            name = text.split('█')[0][2:].strip()
            for part in self.parts:
                if part['name'].startswith(name) or name in part['name']:
                    if part['actor']:
                        part['actor'].SetVisibility(False)
                        part['current_opacity'] = 0.0
                        part['visible'] = False
        self._update_parts_list()
        self.plotter.render()
    
    def _isolate_selected(self):
        selected_names = []
        for item in self.parts_list.selectedItems():
            text = item.text()
            name = text.split('█')[0][2:].strip()
            selected_names.append(name)
        
        if not selected_names:
            return
        
        for part in self.parts:
            if part['actor']:
                is_selected = any(name in part['name'] for name in selected_names)
                if is_selected:
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(part['base_opacity'])
                    part['current_opacity'] = part['base_opacity']
                    part['visible'] = True
                else:
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(0.02)
                    part['current_opacity'] = 0.02
                    part['visible'] = False
        self._update_parts_list()
        self.plotter.render()


def main():
    print("\n" + "="*75)
    print("🧠 BRAIN SURFACE VIEWER - CORTEX ONLY EDITION")
    print("="*75)
    print("Features:")
    print("  ✓ Surface (cortical) structures ONLY")
    print("  ✓ VIBRANT saturated colors")
    print("  ✓ ZERO smoothing = MAXIMUM detail preservation")
    print("  ✓ Enhanced lighting (2.5x brighter)")
    print("  ✓ PBR materials optimized for details")
    print("="*75)
    
    # تحديد مسار الفولدر بشكل تلقائي
    current_dir = os.getcwd()
    path = os.path.join(current_dir, "braindataset.obj")
    
    if not os.path.exists(path):
        print(f"\n❌ Folder not found: {path}")
        print("Please make sure 'braindataset.obj' folder exists in the current directory.\n")
        return
    
    files = glob.glob(os.path.join(path, "*.obj"))
    files.extend(glob.glob(os.path.join(path, "*.OBJ")))
    files = sorted(list(set(files)))
    
    if not files:
        print(f"\n❌ No OBJ files found in: {path}\n")
        return
    
    print(f"\n✅ Found {len(files)} total OBJ files")
    print("🔍 Filtering for surface structures only...")
    
    surface_files = [f for f in files if is_surface_part(os.path.basename(f))]
    print(f"✅ {len(surface_files)} surface structures will be loaded")
    print(f"⏭️  {len(files) - len(surface_files)} deep structures will be skipped")
    print("🚀 Launching surface viewer...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = BrainSurfaceViewer(files)  # نمرر كل الملفات والتصفية ستتم داخلياً
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()