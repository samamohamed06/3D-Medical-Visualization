import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from scipy.ndimage import map_coordinates, zoom, binary_fill_holes, binary_dilation
from scipy.interpolate import splprep, splev
import time
from pathlib import Path

try:
    import trimesh
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False

try:
    from skimage import measure
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False


def obj_to_volume_advanced(folder_path, resolution=256):
    """
    تحويل OBJ إلى volume 3D بطريقة محسّنة جداً
    """
    folder_path = Path(folder_path)
    obj_files = list(folder_path.glob('*.obj'))
    
    if not obj_files:
        raise ValueError(f"No .obj files found in {folder_path}")
    
    obj_file = obj_files[0]
    print(f"📂 Loading: {obj_file.name}")
    
    if not HAS_TRIMESH:
        raise ImportError("Please install: pip install trimesh")
    
    # تحميل الـ mesh
    mesh = trimesh.load(str(obj_file))
    
    print(f"✓ Mesh loaded:")
    print(f"  Vertices: {len(mesh.vertices):,}")
    print(f"  Faces: {len(mesh.faces):,}")
    
    # حساب الحدود
    bounds = mesh.bounds
    extent = bounds[1] - bounds[0]
    
    print(f"  Bounding box: {extent}")
    
    # حساب حجم الـ grid بناءً على أكبر بُعد
    max_extent = extent.max()
    voxel_size = max_extent / resolution
    
    grid_dims = (extent / voxel_size).astype(int) + 2
    grid_dims = np.minimum(grid_dims, resolution)  # حد أقصى
    
    print(f"\n🔧 Creating voxel grid: {grid_dims}")
    print(f"  Voxel size: {voxel_size:.3f}")
    
    # إنشاء voxel grid محسّن
    print("⚙ Voxelizing mesh (this may take a moment)...")
    
    # الطريقة 1: استخدام trimesh voxelization
    try:
        voxelized = mesh.voxelized(pitch=voxel_size)
        volume = voxelized.matrix.astype(float)
        
        print(f"✓ Initial voxelization: {volume.sum():.0f} filled voxels")
        
        # ملء الثقوب الداخلية
        print("🔧 Filling internal holes...")
        volume = binary_fill_holes(volume).astype(float)
        
        # توسيع خفيف لربط الأجزاء المنفصلة
        print("🔧 Connecting components...")
        structure = np.ones((3, 3, 3))
        volume = binary_dilation(volume, structure=structure, iterations=3).astype(float)
        
        print(f"✓ After processing: {volume.sum():.0f} filled voxels")
        
    except Exception as e:
        print(f"⚠ Voxelization failed: {e}")
        print("Trying alternative method...")
        
        # الطريقة البديلة: sampling من السطح
        n_samples = 200000
        points, _ = trimesh.sample.sample_surface(mesh, n_samples)
        
        # تحويل النقاط إلى indices
        normalized = (points - bounds[0]) / voxel_size
        indices = normalized.astype(int)
        
        # إنشاء volume
        volume = np.zeros(grid_dims, dtype=float)
        
        for idx in indices:
            if all(0 <= idx[i] < grid_dims[i] for i in range(3)):
                volume[idx[0], idx[1], idx[2]] = 1.0
        
        # ملء وتوسيع
        volume = binary_fill_holes(volume).astype(float)
        structure = np.ones((3, 3, 3))
        volume = binary_dilation(volume, structure=structure, iterations=4).astype(float)
    
    print(f"\n✅ Final volume: {volume.shape}")
    print(f"   Filled: {100 * volume.sum() / volume.size:.2f}%")
    
    if volume.sum() == 0:
        raise ValueError("⚠ Volume is empty! Check your OBJ file.")
    
    return volume


class InteractiveCurvedMPR:
    def __init__(self, data, downsample_factor=2):
        self.original_data = data
        self.ds_factor = downsample_factor
        
        # تصغير البيانات
        if downsample_factor > 1:
            print(f"⬇ Downsampling by {downsample_factor}x...")
            self.data = zoom(data, 1/downsample_factor, order=1)
        else:
            self.data = data.copy()
        
        # تطبيع
        if self.data.max() > 0:
            self.data = (self.data - self.data.min()) / (self.data.max() - self.data.min() + 1e-10)
        
        print(f"✓ Working data shape: {self.data.shape}")
        
        # الإعدادات
        self.current_slice_ax = self.data.shape[2] // 2
        self.current_slice_cor = self.data.shape[1] // 2
        self.current_slice_sag = self.data.shape[0] // 2
        
        self.points = []
        self.curve_factor = 0.4
        self.active_view = 'sagittal'
        self.mpr_height = 140
        self.mpr_points = 300
        
        self.setup_ui()
        
    def setup_ui(self):
        """إنشاء الواجهة التفاعلية"""
        self.fig = plt.figure(figsize=(22, 12))
        self.fig.patch.set_facecolor('#1a1a1a')
        
        gs = self.fig.add_gridspec(3, 4, height_ratios=[1, 0.05, 2], hspace=0.3, wspace=0.2,
                                   left=0.04, right=0.98, top=0.96, bottom=0.05)
        
        spinal_cmap = 'gray'
        
        # Axial view
        self.ax_axial = self.fig.add_subplot(gs[0, 0])
        self.ax_axial.set_facecolor('#000000')
        self.ax_axial.set_title('AXIAL - SPINAL', fontweight='bold', color='white', fontsize=14,
                               pad=10,
                               bbox=dict(boxstyle='round,pad=0.6', facecolor='#2196F3', 
                                       edgecolor='#64B5F6', linewidth=2, alpha=0.95))
        self.img_axial = self.ax_axial.imshow(self.data[:, :, self.current_slice_ax].T, 
                                              cmap=spinal_cmap, origin='lower', picker=True, vmin=0, vmax=1)
        self.ax_axial.axis('off')
        
        # Coronal view
        self.ax_coronal = self.fig.add_subplot(gs[0, 1])
        self.ax_coronal.set_facecolor('#000000')
        self.ax_coronal.set_title('CORONAL - SPINAL', fontweight='bold', color='white', fontsize=14,
                                 pad=10,
                                 bbox=dict(boxstyle='round,pad=0.6', facecolor='#4CAF50',
                                         edgecolor='#81C784', linewidth=2, alpha=0.95))
        self.img_coronal = self.ax_coronal.imshow(self.data[:, self.current_slice_cor, :].T, 
                                                  cmap=spinal_cmap, origin='lower', picker=True, vmin=0, vmax=1)
        self.ax_coronal.axis('off')
        
        # Sagittal view
        self.ax_sagittal = self.fig.add_subplot(gs[0, 2])
        self.ax_sagittal.set_facecolor('#000000')
        self.ax_sagittal.set_title('SAGITTAL - SPINAL ⭐', fontweight='bold', color='white', fontsize=14,
                                  pad=10,
                                  bbox=dict(boxstyle='round,pad=0.6', facecolor='#F44336',
                                          edgecolor='#E57373', linewidth=2, alpha=0.95))
        self.img_sagittal = self.ax_sagittal.imshow(self.data[self.current_slice_sag, :, :].T, 
                                                    cmap=spinal_cmap, origin='lower', picker=True, vmin=0, vmax=1)
        self.ax_sagittal.axis('off')
        
        # معلومات
        self.ax_info_top = self.fig.add_subplot(gs[0, 3])
        self.ax_info_top.set_facecolor('#1a1a1a')
        self.ax_info_top.axis('off')
        info_instructions = (
            "╔═══════════════════════╗\n"
            "║ SPINAL CORD WORKFLOW  ║\n"
            "╠═══════════════════════╣\n"
            "║                       ║\n"
            "║  1️⃣  Click SAGITTAL    ║\n"
            "║     view (red) first  ║\n"
            "║                       ║\n"
            "║  2️⃣  Follow spine      ║\n"
            "║     centerline        ║\n"
            "║                       ║\n"
            "║  3️⃣  Min 2 points      ║\n"
            "║     (3-5 recommended) ║\n"
            "║                       ║\n"
            "║  4️⃣  Adjust curvature  ║\n"
            "║     slider            ║\n"
            "║                       ║\n"
            "║  5️⃣  Generate MPR      ║\n"
            "║     reconstruction    ║\n"
            "║                       ║\n"
            "╚═══════════════════════╝"
        )
        self.info_text_top = self.ax_info_top.text(0.05, 0.5, info_instructions,
                                                   fontsize=10.5, family='monospace',
                                                   verticalalignment='center', color='white',
                                                   bbox=dict(boxstyle='round,pad=1', 
                                                           facecolor='#263238', alpha=0.95,
                                                           edgecolor='#00BCD4', linewidth=2.5))
        
        # MPR result
        self.ax_mpr = self.fig.add_subplot(gs[2, :])
        self.ax_mpr.set_facecolor('#000000')
        self.ax_mpr.set_title('⬤ SPINAL CORD CURVED MPR ⬤', 
                             fontweight='bold', fontsize=17, color='#00E676',
                             pad=18,
                             bbox=dict(boxstyle='round,pad=0.8', facecolor='#1a1a1a',
                                     edgecolor='#00E676', linewidth=3, alpha=0.95))
        self.ax_mpr.text(0.5, 0.5, '🦴 Ready • Click points on SAGITTAL view', 
                        ha='center', va='center', fontsize=15, color='#90A4AE',
                        transform=self.ax_mpr.transAxes, style='italic', fontweight='bold')
        self.ax_mpr.axis('off')
        
        # الأزرار
        ax_generate = plt.axes([0.35, 0.015, 0.14, 0.035])
        self.btn_generate = Button(ax_generate, '▶ GENERATE MPR', 
                                   color='#00C853', hovercolor='#00E676')
        self.btn_generate.label.set_fontsize(12)
        self.btn_generate.label.set_fontweight('bold')
        self.btn_generate.label.set_color('white')
        self.btn_generate.on_clicked(self.generate_mpr)
        
        ax_clear = plt.axes([0.50, 0.015, 0.12, 0.035])
        self.btn_clear = Button(ax_clear, '✖ CLEAR ALL', 
                               color='#D32F2F', hovercolor='#F44336')
        self.btn_clear.label.set_fontsize(12)
        self.btn_clear.label.set_fontweight('bold')
        self.btn_clear.label.set_color('white')
        self.btn_clear.on_clicked(self.clear_points)
        
        ax_undo = plt.axes([0.63, 0.015, 0.1, 0.035])
        self.btn_undo = Button(ax_undo, '↶ UNDO', 
                              color='#FF6F00', hovercolor='#FF9800')
        self.btn_undo.label.set_fontsize(12)
        self.btn_undo.label.set_fontweight('bold')
        self.btn_undo.label.set_color('white')
        self.btn_undo.on_clicked(self.undo_last)
        
        # Slider
        ax_curve = plt.axes([0.12, 0.025, 0.18, 0.02])
        self.slider_curve = Slider(ax_curve, 'Curvature', 0.0, 1.0, 
                                  valinit=0.4, valstep=0.05, 
                                  color='#2196F3', alpha=0.8)
        self.slider_curve.label.set_fontsize(11)
        self.slider_curve.label.set_fontweight('bold')
        self.slider_curve.on_changed(self.update_curve_factor)
        
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # رسم المؤشرات
        self.line_axial, = self.ax_axial.plot([], [], '-', color='#FF1744', linewidth=3, alpha=0.9)
        self.points_axial, = self.ax_axial.plot([], [], 'o', color='#00E676', markersize=12, 
                                                markeredgecolor='white', markeredgewidth=3, alpha=1)
        
        self.line_coronal, = self.ax_coronal.plot([], [], '-', color='#FF1744', linewidth=3, alpha=0.9)
        self.points_coronal, = self.ax_coronal.plot([], [], 'o', color='#00E676', markersize=12, 
                                                    markeredgecolor='white', markeredgewidth=3, alpha=1)
        
        self.line_sagittal, = self.ax_sagittal.plot([], [], '-', color='#FF1744', linewidth=3, alpha=0.9)
        self.points_sagittal, = self.ax_sagittal.plot([], [], 'o', color='#00E676', markersize=12, 
                                                      markeredgecolor='white', markeredgewidth=3, alpha=1)
        
        self.info_text = self.fig.text(0.5, 0.985, self.get_info_text(), 
                                       fontsize=12, family='monospace', ha='center',
                                       fontweight='bold', color='#00E676',
                                       bbox=dict(boxstyle='round,pad=0.7', facecolor='#263238', 
                                               alpha=0.95, edgecolor='#00BCD4', linewidth=2.5))
        
        plt.tight_layout()
    
    def get_info_text(self):
        return (f"● Selected Points: {len(self.points)} | "
                f"Curvature: {self.curve_factor:.2f} | "
                f"Resolution: {self.mpr_points}×{self.mpr_height} ●")
    
    def on_click(self, event):
        if event.inaxes in [self.ax_axial, self.ax_coronal, self.ax_sagittal]:
            if event.button == 1:
                x, y = int(event.xdata), int(event.ydata)
                
                if event.inaxes == self.ax_axial:
                    point = [x, y, self.current_slice_ax]
                elif event.inaxes == self.ax_coronal:
                    point = [x, self.current_slice_cor, y]
                elif event.inaxes == self.ax_sagittal:
                    point = [self.current_slice_sag, x, y]
                
                self.points.append(point)
                print(f"Added point {len(self.points)}: {point}")
                self.update_display()
    
    def update_display(self):
        if len(self.points) == 0:
            self.line_axial.set_data([], [])
            self.points_axial.set_data([], [])
            self.line_coronal.set_data([], [])
            self.points_coronal.set_data([], [])
            self.line_sagittal.set_data([], [])
            self.points_sagittal.set_data([], [])
        else:
            points_arr = np.array(self.points)
            
            self.points_axial.set_data(points_arr[:, 0], points_arr[:, 1])
            if len(self.points) >= 2:
                curve = self.create_curve()
                self.line_axial.set_data(curve[:, 0], curve[:, 1])
            else:
                self.line_axial.set_data([], [])
            
            self.points_coronal.set_data(points_arr[:, 0], points_arr[:, 2])
            if len(self.points) >= 2:
                self.line_coronal.set_data(curve[:, 0], curve[:, 2])
            else:
                self.line_coronal.set_data([], [])
            
            self.points_sagittal.set_data(points_arr[:, 1], points_arr[:, 2])
            if len(self.points) >= 2:
                self.line_sagittal.set_data(curve[:, 1], curve[:, 2])
            else:
                self.line_sagittal.set_data([], [])
        
        self.info_text.set_text(self.get_info_text())
        self.fig.canvas.draw_idle()
    
    def create_curve(self):
        if len(self.points) < 2:
            return np.array([])
        
        points_arr = np.array(self.points, dtype=float)
        
        if len(self.points) == 2:
            start, end = points_arr[0], points_arr[1]
            mid = (start + end) / 2
            direction = end - start
            
            if abs(direction[0]) > abs(direction[2]):
                perpendicular = np.array([-direction[1], direction[0], 0])
            else:
                perpendicular = np.array([0, -direction[2], direction[1]])
            
            perpendicular = perpendicular / (np.linalg.norm(perpendicular) + 1e-10)
            
            control_points = np.array([
                start,
                start + direction * 0.25 + perpendicular * np.linalg.norm(direction) * self.curve_factor * 0.5,
                mid + perpendicular * np.linalg.norm(direction) * self.curve_factor,
                end - direction * 0.25 + perpendicular * np.linalg.norm(direction) * self.curve_factor * 0.5,
                end
            ])
        else:
            control_points = points_arr
        
        try:
            tck, u = splprep([control_points[:, 0], control_points[:, 1], control_points[:, 2]], 
                            s=0, k=min(3, len(control_points)-1))
            u_new = np.linspace(0, 1, 100)
            curve = np.array(splev(u_new, tck)).T
            return curve
        except:
            return points_arr
    
    def create_curve_high_res(self):
        if len(self.points) < 2:
            return np.array([])
        
        points_arr = np.array(self.points, dtype=float)
        
        if len(self.points) == 2:
            start, end = points_arr[0], points_arr[1]
            mid = (start + end) / 2
            direction = end - start
            
            if abs(direction[0]) > abs(direction[2]):
                perpendicular = np.array([-direction[1], direction[0], 0])
            else:
                perpendicular = np.array([0, -direction[2], direction[1]])
            
            perpendicular = perpendicular / (np.linalg.norm(perpendicular) + 1e-10)
            
            control_points = np.array([
                start,
                start + direction * 0.25 + perpendicular * np.linalg.norm(direction) * self.curve_factor * 0.5,
                mid + perpendicular * np.linalg.norm(direction) * self.curve_factor,
                end - direction * 0.25 + perpendicular * np.linalg.norm(direction) * self.curve_factor * 0.5,
                end
            ])
        else:
            control_points = points_arr
        
        try:
            tck, u = splprep([control_points[:, 0], control_points[:, 1], control_points[:, 2]], 
                            s=0, k=min(3, len(control_points)-1))
            u_new = np.linspace(0, 1, self.mpr_points)
            curve = np.array(splev(u_new, tck)).T
            return curve
        except:
            return points_arr
    
    def generate_mpr(self, event):
        if len(self.points) < 2:
            print("⚠ Need at least 2 points!")
            self.ax_mpr.clear()
            self.ax_mpr.text(0.5, 0.5, '⚠ Add at least 2 points!', 
                           ha='center', va='center', fontsize=16, color='red', fontweight='bold')
            self.ax_mpr.axis('off')
            self.fig.canvas.draw_idle()
            return
        
        print("\n" + "="*50)
        print("Generating Spinal Cord MPR...")
        start_time = time.time()
        
        curve = self.create_curve_high_res()
        mpr_image = self.extract_mpr(curve)
        
        if mpr_image.max() > 0:
            p1, p99 = np.percentile(mpr_image[mpr_image > 0], (1, 99))
            mpr_enhanced = np.clip((mpr_image - p1) / (p99 - p1 + 1e-10), 0, 1)
            mpr_enhanced = np.power(mpr_enhanced, 0.8)
        else:
            mpr_enhanced = mpr_image
        
        self.ax_mpr.clear()
        self.ax_mpr.set_facecolor('#000000')
        
        aspect_ratio = mpr_enhanced.shape[0] / mpr_enhanced.shape[1]
        
        im = self.ax_mpr.imshow(mpr_enhanced, cmap='gray', 
                                aspect=aspect_ratio * 2.2,
                                interpolation='lanczos',
                                vmin=0, vmax=1)
        
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(self.ax_mpr)
        cax = divider.append_axes("right", size="1.2%", pad=0.18)
        cax.set_facecolor('#1a1a1a')
        cbar = plt.colorbar(im, cax=cax)
        cbar.set_label('INTENSITY', fontsize=11, fontweight='bold', color='white')
        cbar.ax.tick_params(labelsize=9, colors='white')
        cbar.outline.set_edgecolor('#00BCD4')
        cbar.outline.set_linewidth(2)
        
        self.ax_mpr.set_title(f'🦴 SPINAL MPR  |  {time.time()-start_time:.2f}s  |  High Res ⬤', 
                             fontweight='bold', fontsize=16, color='#00E676',
                             pad=15,
                             bbox=dict(boxstyle='round,pad=0.8', facecolor='#1a1a1a',
                                     edgecolor='#00E676', linewidth=3, alpha=0.98))
        self.ax_mpr.set_xlabel('Position along spine  →', fontsize=13, fontweight='bold', color='#64B5F6')
        self.ax_mpr.set_ylabel('⟂  Distance', fontsize=13, fontweight='bold', color='#64B5F6')
        self.ax_mpr.grid(True, alpha=0.15, linestyle='--', linewidth=1, color='#00BCD4')
        
        self.ax_mpr.tick_params(labelsize=10, colors='#90A4AE')
        self.ax_mpr.spines['bottom'].set_color('#00BCD4')
        self.ax_mpr.spines['left'].set_color('#00BCD4')
        self.ax_mpr.spines['bottom'].set_linewidth(2)
        self.ax_mpr.spines['left'].set_linewidth(2)
        self.ax_mpr.spines['top'].set_visible(False)
        self.ax_mpr.spines['right'].set_visible(False)
        
        path_length = np.sum(np.linalg.norm(np.diff(curve, axis=0), axis=1))
        info_str = (f"📊 Resolution: {mpr_enhanced.shape[1]}×{mpr_enhanced.shape[0]} px  |  "
                   f"📏 Length: {path_length:.1f} voxels  |  "
                   f"↪ Curve: {self.curve_factor:.2f}")
        self.ax_mpr.text(0.02, 0.98, info_str, transform=self.ax_mpr.transAxes,
                        fontsize=10.5, verticalalignment='top', fontweight='bold', color='white',
                        bbox=dict(boxstyle='round,pad=0.6', facecolor='#263238', alpha=0.95, 
                                edgecolor='#00BCD4', linewidth=2))
        
        num_ticks = 6
        x_ticks = np.linspace(0, mpr_enhanced.shape[1]-1, num_ticks)
        x_labels = [f'{i*100/(num_ticks-1):.0f}%' for i in range(num_ticks)]
        self.ax_mpr.set_xticks(x_ticks)
        self.ax_mpr.set_xticklabels(x_labels)
        
        self.fig.canvas.draw_idle()
        print(f"✓ MPR done in {time.time()-start_time:.1f}s")
        print(f"  Resolution: {mpr_enhanced.shape}")
        print("="*50)
    
    def extract_mpr(self, curve_path):
        num_points = len(curve_path)
        normals = self.compute_normals(curve_path)
        
        height = self.mpr_height
        mpr_image = np.zeros((height, num_points))
        width_range = np.linspace(-height/2, height/2, height)
        
        print("Progress: ", end="", flush=True)
        step = max(1, num_points // 10)
        
        for i in range(num_points):
            if i % step == 0:
                print("█", end="", flush=True)
            
            center = curve_path[i]
            normal = normals[i]
            
            for j, offset in enumerate(width_range):
                sample_point = center + normal * offset
                
                if all(0 <= sample_point[k] < self.data.shape[k]-1 for k in range(3)):
                    coords = sample_point.reshape(3, 1)
                    value = map_coordinates(self.data, coords, order=1, mode='constant', cval=0.0)
                    mpr_image[j, i] = value[0]
        
        print(" ✓")
        return mpr_image
    
    def compute_normals(self, curve):
        n_points = len(curve)
        normals = np.zeros_like(curve)
        
        for i in range(n_points):
            if i == 0:
                tangent = curve[i+1] - curve[i]
            elif i == n_points - 1:
                tangent = curve[i] - curve[i-1]
            else:
                tangent = (curve[i+1] - curve[i-1]) / 2
            
            tangent = tangent / (np.linalg.norm(tangent) + 1e-10)
            
            if abs(tangent[2]) < 0.9:
                normal = np.cross(tangent, np.array([0, 0, 1]))
            else:
                normal = np.cross(tangent, np.array([1, 0, 0]))
            
            normals[i] = normal / (np.linalg.norm(normal) + 1e-10)
        
        return normals
    
    def clear_points(self, event):
        self.points = []
        self.ax_mpr.clear()
        self.ax_mpr.set_title('🦴 SPINAL CORD MPR - Click points', 
                             fontweight='bold', fontsize=13, color='red')
        self.ax_mpr.axis('off')
        self.update_display()
        print("✓ All cleared")
    
    def undo_last(self, event):
        if self.points:
            removed = self.points.pop()
            print(f"✓ Removed: {removed}")
            self.update_display()
    
    def update_curve_factor(self, val):
        self.curve_factor = val
        if len(self.points) >= 2:
            self.update_display()
    
    def show(self):
        plt.show()


def main():
    print("="*60)
    print("🦴 SPINAL CORD CURVED MPR VIEWER")
    print("="*60)
    
    folder_name = "spinalcorddataset"
    
    try:
        print(f"\n📂 Loading from: {folder_name}")
        print("⏳ This may take 30-60 seconds...\n")
        
        # تحويل OBJ لـ volume
        data = obj_to_volume_advanced(folder_name, resolution=256)
        
        print(f"\n✅ Ready!")
        print(f"Volume: {data.shape}")
        print("\n🚀 Starting viewer...\n")
        
        # إنشاء الـ viewer
        viewer = InteractiveCurvedMPR(data, downsample_factor=2)
        viewer.show()
        
    except FileNotFoundError:
        print(f"❌ ERROR: Folder '{folder_name}' not found!")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()