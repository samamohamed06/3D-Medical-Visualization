import pyvista as pv
import os
import glob
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from pyvistaqt import BackgroundPlotter
import sys

"""
🧠 Professional Brain Viewer - Enhanced Edition
Fixed Visibility + Better Colors + Maximum Detail Preservation
"""

# Enhanced VIBRANT color palette - MORE SATURATED & BRIGHT
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
    
    'thalamus': [1.0, 0.1, 0.4],             # Very Bright Pink
    'hypothalamus': [0.95, 0.08, 0.35],
    'caudate': [0.6, 0.3, 1.0],              # Very Bright Deep Purple
    'putamen': [0.65, 0.35, 1.0],
    'globus': [0.55, 0.28, 0.98],
    'pallidus': [0.58, 0.32, 1.0],
    'hippocampus': [1.0, 0.8, 0.0],          # Very Bright Amber
    'amygdala': [1.0, 0.75, 0.0],
    'fornix': [0.98, 0.72, 0.0],
    
    'ventricle': [0.0, 0.9, 1.0],            # Very Bright Cyan
    'lateral_ventricle': [0.05, 0.85, 0.98],
    
    'default': [0.9, 0.9, 0.9]               # Bright Gray
}


def classify_part(filename):
    """Classify brain part and assign opacity"""
    name = filename.lower()
    
    internal = {
        'ventricle': 0.35,
        'thalamus': 0.75,
        'caudate': 0.75,
        'putamen': 0.75,
        'hippocampus': 0.85,
        'amygdala': 0.85,
        'fornix': 0.65,
        'globus': 0.75,
        'pallidus': 0.75,
        'hypothalamus': 0.75
    }
    
    for key, opacity in internal.items():
        if key in name:
            return key, opacity
    
    for region in COLORS.keys():
        if region in name:
            return region, 1.0
    
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


class BrainViewerUltimate(QtWidgets.QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.parts = []
        
        self.setWindowTitle("🧠 Professional Brain Viewer - Enhanced Edition")
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
        
        title = QtWidgets.QLabel("🧠 3D Brain Visualization")
        title.setObjectName("titleLabel")
        subtitle = QtWidgets.QLabel("Interactive Anatomical Explorer")
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
        
        header_title = QtWidgets.QLabel("Control Panel")
        header_title.setObjectName("titleLabel")
        header_title.setAlignment(QtCore.Qt.AlignCenter)
        
        header_subtitle = QtWidgets.QLabel("Adjust visualization settings")
        header_subtitle.setObjectName("infoLabel")
        header_subtitle.setAlignment(QtCore.Qt.AlignCenter)
        
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)
        header_card.addLayout(header_layout)
        layout.addWidget(header_card)
        
        opacity_card = ModernCard("🎚️ Opacity Controls")
        
        self.global_slider = ModernSlider("Global Opacity", 0, 100, 100)
        self.global_slider.valueChanged.connect(self._update_global_opacity)
        opacity_card.addWidget(self.global_slider)
        
        self.surface_slider = ModernSlider("Cortex Surface", 0, 100, 100)
        self.surface_slider.valueChanged.connect(self._update_surface_opacity)
        opacity_card.addWidget(self.surface_slider)
        
        self.internal_slider = ModernSlider("Deep Structures", 0, 100, 75)
        self.internal_slider.valueChanged.connect(self._update_internal_opacity)
        opacity_card.addWidget(self.internal_slider)
        
        layout.addWidget(opacity_card)
        
        modes_card = ModernCard("👁️ View Modes")
        
        view_buttons = [
            ("🔄 Reset View", self._reset_view, ""),
            ("🌐 Show All", self._show_all, ""),
            ("🧩 Hide Cortex", self._hide_cortex, "accentButton"),
            ("💎 Deep Only", self._show_deep_only, "accentButton"),
        ]
        
        for text, callback, style_id in view_buttons:
            btn = QtWidgets.QPushButton(text)
            if style_id:
                btn.setObjectName(style_id)
            btn.clicked.connect(callback)
            modes_card.addWidget(btn)
        
        layout.addWidget(modes_card)
        
        regions_card = ModernCard("🎨 Anatomical Regions")
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
        
        list_card = ModernCard("📋 Brain Structures")
        
        search_layout = QtWidgets.QHBoxLayout()
        search_icon = QtWidgets.QLabel("🔍")
        search_icon.setStyleSheet("font-size: 15pt;")
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search anatomical structures...")
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
        
        self.info_label = QtWidgets.QLabel("Initializing brain viewer...")
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
        print("\n🧠 Loading brain meshes...")
        self.info_label.setText("⏳ Loading brain structures...")
        QtWidgets.QApplication.processEvents()
        
        skipped = 0
        loaded = 0
        
        for i, path in enumerate(self.files):
            try:
                # Try reading the mesh
                mesh = pv.read(path)
                
                # Check if mesh is valid
                if mesh.n_points == 0 or mesh.n_cells == 0:
                    print(f"  ⚠️ Empty mesh: {os.path.basename(path)}")
                    skipped += 1
                    continue
                
                # ZERO SMOOTHING - Maximum detail preservation
                if mesh.n_points < 100:
                    # Very small structures - no smoothing at all
                    pass
                else:
                    # Only fix mesh issues, preserve ALL details
                    mesh = mesh.clean(tolerance=0.0)
                
                # Enhanced normal computation for maximum detail visibility
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
                
                if (loaded) % 15 == 0:
                    print(f"  ✓ Loaded: {loaded}/{len(self.files)}")
                    self.info_label.setText(f"⏳ Loading {loaded}/{len(self.files)}...")
                    QtWidgets.QApplication.processEvents()
                    
            except Exception as e:
                print(f"  ⚠️ Error loading {os.path.basename(path)}: {str(e)}")
                skipped += 1
        
        print(f"\n✅ Loaded {loaded} parts successfully (ZERO smoothing = MAX details)")
        if skipped > 0:
            print(f"⚠️  Skipped {skipped} files due to errors")
        
        if loaded == 0:
            print("\n❌ ERROR: No files loaded! Check:")
            print("   1. Are the OBJ files corrupted?")
            print("   2. Try opening one file manually in MeshLab/Blender")
            print("   3. Check file encoding (should be UTF-8)")
            
        self._update_parts_list()
    
    def _setup_scene(self):
        if len(self.parts) == 0:
            self.info_label.setText("❌ No parts loaded! Check console for errors.")
            print("❌ Cannot setup scene - no parts loaded!")
            return
            
        print("🎨 Setting up scene...")
        self.info_label.setText("🎨 Rendering with enhanced materials...")
        QtWidgets.QApplication.processEvents()
        
        for i, part in enumerate(self.parts):
            actor = self.plotter.add_mesh(
                part['mesh'],
                color=part['color'],
                opacity=part['base_opacity'],
                smooth_shading=True,
                pbr=True,
                metallic=0.0,         # Zero metallic for biological tissue
                roughness=0.60,       # Less rough = more detail visibility
                ambient=0.60,         # Higher ambient = better visibility
                diffuse=0.95,         # Very high diffuse
                specular=0.70,        # Higher specular = detail pop
                specular_power=100,   # Sharp highlights for details
                interpolate_before_map=True
            )
            part['actor'] = actor
            
            if (i + 1) % 15 == 0:
                print(f"  ✓ {i + 1}/{len(self.parts)}")
                self.info_label.setText(f"🎨 Rendering {i + 1}/{len(self.parts)}...")
                QtWidgets.QApplication.processEvents()
        
        # Enhanced multi-directional lighting for maximum detail visibility
        lights = [
            (( 900,  800,  900), 2.5, [1.0, 1.0, 1.0]),      # Main key light - BRIGHTER
            ((-700,  700,  800), 1.8, [0.95, 0.98, 1.0]),    # Fill light - BRIGHTER
            ((   0, -600, -700), 1.2, [1.0, 0.98, 0.95]),    # Back light - BRIGHTER
            (( 600, -500,  600), 1.5, [1.0, 1.0, 1.0]),      # Side light - BRIGHTER
            ((   0,    0, -900), 1.6, [0.98, 0.98, 1.0])     # Front light - BRIGHTER
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
        
        info_text = f"""✅ {len(self.parts)} structures loaded
🖱️ Click parts to isolate
🔍 Search by name
🎨 Enhanced colors & details"""
        self.info_label.setText(info_text)
        print("✅ Scene ready!\n")
    
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
    
    def _hide_cortex(self):
        cortical = ['frontal', 'parietal', 'temporal', 'occipital', 'precentral', 'postcentral', 
                   'superior', 'middle', 'inferior', 'cuneus', 'lingual', 'fusiform', 
                   'angular', 'supramarginal', 'precuneus', 'gyrus', 'lobule', 'calcarine']
        
        # IMPORTANT: Also hide ventricles when hiding cortex
        also_hide = ['ventricle', 'lateral_ventricle']
        
        for part in self.parts:
            if part['actor']:
                is_cortex = any(c in part['name'].lower() for c in cortical)
                is_ventricle = any(v in part['name'].lower() for v in also_hide)
                
                if is_cortex or is_ventricle:
                    # COMPLETELY HIDE
                    part['actor'].SetVisibility(False)
                    part['current_opacity'] = 0.0
                    part['visible'] = False
                else:
                    # Show deep structures clearly
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(min(part['base_opacity'] * 1.4, 1.0))
                    part['current_opacity'] = min(part['base_opacity'] * 1.4, 1.0)
                    part['visible'] = True
        self._update_parts_list()
        self.plotter.render()
    
    def _show_deep_only(self):
        deep = ['thalamus', 'caudate', 'putamen', 'hippocampus', 'amygdala', 'ventricle', 'fornix', 'globus', 'pallidus']
        for part in self.parts:
            if part['actor']:
                is_deep = any(d in part['name'].lower() for d in deep)
                if is_deep:
                    part['actor'].SetVisibility(True)
                    part['actor'].GetProperty().SetOpacity(part['base_opacity'])
                    part['current_opacity'] = part['base_opacity']
                    part['visible'] = True
                else:
                    part['actor'].SetVisibility(False)
                    part['current_opacity'] = 0.0
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
        self.surface_slider.setValue(100)
        self.internal_slider.setValue(75)
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
    
    def _update_surface_opacity(self, value):
        opacity = value / 100.0
        surface = ['frontal', 'parietal', 'temporal', 'occipital', 'precentral', 'postcentral',
                  'superior', 'middle', 'inferior', 'cuneus', 'lingual', 'fusiform',
                  'angular', 'supramarginal', 'precuneus', 'gyrus', 'lobule', 'calcarine']
        
        for part in self.parts:
            if part['actor']:
                is_surface = any(s in part['name'].lower() for s in surface)
                if is_surface:
                    if opacity < 0.05:
                        part['actor'].SetVisibility(False)
                        part['visible'] = False
                    else:
                        part['actor'].SetVisibility(True)
                        part['actor'].GetProperty().SetOpacity(opacity)
                        part['current_opacity'] = opacity
                        part['visible'] = True
        self._update_parts_list()
        self.plotter.render()
    
    def _update_internal_opacity(self, value):
        opacity = value / 100.0
        internal = ['thalamus', 'caudate', 'putamen', 'hippocampus', 'amygdala', 'ventricle']
        for part in self.parts:
            if part['actor']:
                if any(i in part['name'].lower() for i in internal):
                    new_opacity = part['base_opacity'] * opacity
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
    print("🧠 PROFESSIONAL BRAIN VIEWER - ENHANCED EDITION")
    print("="*75)
    print("Features:")
    print("  ✓ VIBRANT saturated colors (100% visibility)")
    print("  ✓ Fixed visibility - cortex & ventricles hide completely")
    print("  ✓ ZERO smoothing = MAXIMUM detail preservation")
    print("  ✓ Enhanced lighting (2.5x brighter)")
    print("  ✓ PBR materials optimized for details")
    print("="*75)
    
    # تحديد مسار الفولدر بشكل تلقائي
    # البحث عن فولدر braindataset.obj في المسار الحالي
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
    
    print(f"\n✅ Found {len(files)} OBJ files in: {path}")
    print("🚀 Launching...\n")
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = BrainViewerUltimate(files)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()