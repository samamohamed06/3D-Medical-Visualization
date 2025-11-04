import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from scipy.ndimage import map_coordinates, zoom
from scipy.interpolate import splprep, splev
import time

class InteractiveCurvedMPR:
    def __init__(self, data, downsample_factor=2):
        self.original_data = data
        self.ds_factor = downsample_factor
        
        # تصغير البيانات للسرعة
        self.data = zoom(data, 1/downsample_factor, order=1)
        self.data = (self.data - self.data.min()) / (self.data.max() - self.data.min() + 1e-10)
        
        print(f"Data shape: {self.data.shape}")
        
        # الإعدادات - محسّنة للأوعية الدموية
        self.current_slice_ax = self.data.shape[2] // 2
        self.current_slice_cor = self.data.shape[1] // 2
        self.current_slice_sag = self.data.shape[0] // 2
        
        self.points = []  # نقاط المسار
        self.curve_factor = 0.3  # انحناء أقل للأوعية الدموية
        self.active_view = 'axial'  # الـ view النشط
        self.mpr_height = 120  # ارتفاع مناسب للأورطي
        self.mpr_points = 350  # دقة عالية لتفاصيل الأوعية
        
        # إنشاء الواجهة
        self.setup_ui()
        
    def setup_ui(self):
        """إنشاء الواجهة التفاعلية"""
        self.fig = plt.figure(figsize=(22, 12))
        self.fig.patch.set_facecolor('#0a0a0a')  # خلفية داكنة جداً للأوعية
        
        # Grid layout احترافي
        gs = self.fig.add_gridspec(3, 4, height_ratios=[1, 0.05, 2], hspace=0.3, wspace=0.2,
                                   left=0.04, right=0.98, top=0.96, bottom=0.05)
        
        # Axial view
        self.ax_axial = self.fig.add_subplot(gs[0, 0])
        self.ax_axial.set_facecolor('#000000')
        self.ax_axial.set_title('AXIAL VIEW', fontweight='bold', color='white', fontsize=14,
                               pad=10,
                               bbox=dict(boxstyle='round,pad=0.6', facecolor='#E91E63', 
                                       edgecolor='#F48FB1', linewidth=2, alpha=0.95))
        self.img_axial = self.ax_axial.imshow(self.data[:, :, self.current_slice_ax].T, 
                                              cmap='hot', origin='lower', picker=True, vmin=0, vmax=1)
        self.ax_axial.axis('off')
        
        # Coronal view
        self.ax_coronal = self.fig.add_subplot(gs[0, 1])
        self.ax_coronal.set_facecolor('#000000')
        self.ax_coronal.set_title('CORONAL VIEW', fontweight='bold', color='white', fontsize=14,
                                 pad=10,
                                 bbox=dict(boxstyle='round,pad=0.6', facecolor='#E91E63',
                                         edgecolor='#F48FB1', linewidth=2, alpha=0.95))
        self.img_coronal = self.ax_coronal.imshow(self.data[:, self.current_slice_cor, :].T, 
                                                  cmap='hot', origin='lower', picker=True, vmin=0, vmax=1)
        self.ax_coronal.axis('off')
        
        # Sagittal view
        self.ax_sagittal = self.fig.add_subplot(gs[0, 2])
        self.ax_sagittal.set_facecolor('#000000')
        self.ax_sagittal.set_title('SAGITTAL VIEW', fontweight='bold', color='white', fontsize=14,
                                  pad=10,
                                  bbox=dict(boxstyle='round,pad=0.6', facecolor='#E91E63',
                                          edgecolor='#F48FB1', linewidth=2, alpha=0.95))
        self.img_sagittal = self.ax_sagittal.imshow(self.data[self.current_slice_sag, :, :].T, 
                                                    cmap='hot', origin='lower', picker=True, vmin=0, vmax=1)
        self.ax_sagittal.axis('off')
        
        # معلومات احترافية
        self.ax_info_top = self.fig.add_subplot(gs[0, 3])
        self.ax_info_top.set_facecolor('#0a0a0a')
        self.ax_info_top.axis('off')
        info_instructions = (
            "╔═══════════════════════╗\n"
            "║   AORTA MPR GUIDE     ║\n"
            "╠═══════════════════════╣\n"
            "║                       ║\n"
            "║  🫀 WORKFLOW          ║\n"
            "║                       ║\n"
            "║  1️⃣  Trace aorta path  ║\n"
            "║     by clicking       ║\n"
            "║                       ║\n"
            "║  2️⃣  Start from aortic ║\n"
            "║     root downward     ║\n"
            "║                       ║\n"
            "║  3️⃣  Min 2 points      ║\n"
            "║     required          ║\n"
            "║                       ║\n"
            "║  4️⃣  Adjust curvature  ║\n"
            "║     for aortic arch   ║\n"
            "║                       ║\n"
            "║  5️⃣  Generate curved   ║\n"
            "║     reconstruction    ║\n"
            "║                       ║\n"
            "╚═══════════════════════╝"
        )
        self.info_text_top = self.ax_info_top.text(0.05, 0.5, info_instructions,
                                                   fontsize=10, family='monospace',
                                                   verticalalignment='center', color='white',
                                                   bbox=dict(boxstyle='round,pad=1', 
                                                           facecolor='#1a1a1a', alpha=0.95,
                                                           edgecolor='#E91E63', linewidth=2.5))
        
        # MPR result - مساحة كبيرة
        self.ax_mpr = self.fig.add_subplot(gs[2, :])
        self.ax_mpr.set_facecolor('#000000')
        self.ax_mpr.set_title('⬤ AORTA CURVED MULTIPLANAR RECONSTRUCTION ⬤', 
                             fontweight='bold', fontsize=17, color='#FF1744',
                             pad=18,
                             bbox=dict(boxstyle='round,pad=0.8', facecolor='#0a0a0a',
                                     edgecolor='#FF1744', linewidth=3, alpha=0.95))
        self.ax_mpr.text(0.5, 0.5, '🫀 Ready to generate Aorta MPR • Trace path above', 
                        ha='center', va='center', fontsize=15, color='#F48FB1',
                        transform=self.ax_mpr.transAxes, style='italic', fontweight='bold')
        self.ax_mpr.axis('off')
        
        # الأزرار والتحكم - تصميم مناسب للأوعية الدموية
        ax_generate = plt.axes([0.35, 0.015, 0.14, 0.035])
        self.btn_generate = Button(ax_generate, '▶ GENERATE MPR', 
                                   color='#D32F2F', hovercolor='#FF1744')
        self.btn_generate.label.set_fontsize(12)
        self.btn_generate.label.set_fontweight('bold')
        self.btn_generate.label.set_color('white')
        self.btn_generate.on_clicked(self.generate_mpr)
        
        ax_clear = plt.axes([0.50, 0.015, 0.12, 0.035])
        self.btn_clear = Button(ax_clear, '✖ CLEAR ALL', 
                               color='#424242', hovercolor='#616161')
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
        
        # Slider احترافي
        ax_curve = plt.axes([0.12, 0.025, 0.18, 0.02])
        self.slider_curve = Slider(ax_curve, 'Curvature', 0.0, 1.0, 
                                  valinit=0.3, valstep=0.05, 
                                  color='#E91E63', alpha=0.8)
        self.slider_curve.label.set_fontsize(11)
        self.slider_curve.label.set_fontweight('bold')
        self.slider_curve.on_changed(self.update_curve_factor)
        
        # توصيل أحداث الماوس
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # رسم المؤشرات الأولية بتصميم مناسب للأوعية
        self.line_axial, = self.ax_axial.plot([], [], '-', color='#00E5FF', linewidth=3, alpha=0.9)
        self.points_axial, = self.ax_axial.plot([], [], 'o', color='#FFEA00', markersize=12, 
                                                markeredgecolor='white', markeredgewidth=3, alpha=1)
        
        self.line_coronal, = self.ax_coronal.plot([], [], '-', color='#00E5FF', linewidth=3, alpha=0.9)
        self.points_coronal, = self.ax_coronal.plot([], [], 'o', color='#FFEA00', markersize=12, 
                                                    markeredgecolor='white', markeredgewidth=3, alpha=1)
        
        self.line_sagittal, = self.ax_sagittal.plot([], [], '-', color='#00E5FF', linewidth=3, alpha=0.9)
        self.points_sagittal, = self.ax_sagittal.plot([], [], 'o', color='#FFEA00', markersize=12, 
                                                      markeredgecolor='white', markeredgewidth=3, alpha=1)
        
        # نص المعلومات العلوي
        self.info_text = self.fig.text(0.5, 0.985, self.get_info_text(), 
                                       fontsize=12, family='monospace', ha='center',
                                       fontweight='bold', color='#FF1744',
                                       bbox=dict(boxstyle='round,pad=0.7', facecolor='#1a1a1a', 
                                               alpha=0.95, edgecolor='#E91E63', linewidth=2.5))
        
        plt.tight_layout()
    
    def get_info_text(self):
        """نص المعلومات"""
        return (f"🫀 Path Points: {len(self.points)} | "
                f"Curvature: {self.curve_factor:.2f} | "
                f"MPR Resolution: {self.mpr_points}×{self.mpr_height} ●")
    
    def on_click(self, event):
        """معالجة نقرات الماوس"""
        if event.inaxes in [self.ax_axial, self.ax_coronal, self.ax_sagittal]:
            if event.button == 1:  # Left click
                x, y = int(event.xdata), int(event.ydata)
                
                # تحديد الإحداثيات ثلاثية الأبعاد حسب الـ view
                if event.inaxes == self.ax_axial:
                    point = [x, y, self.current_slice_ax]
                elif event.inaxes == self.ax_coronal:
                    point = [x, self.current_slice_cor, y]
                elif event.inaxes == self.ax_sagittal:
                    point = [self.current_slice_sag, x, y]
                
                self.points.append(point)
                print(f"Added aorta point {len(self.points)}: {point}")
                
                self.update_display()
    
    def update_display(self):
        """تحديث العرض"""
        if len(self.points) == 0:
            # مسح الخطوط
            self.line_axial.set_data([], [])
            self.points_axial.set_data([], [])
            self.line_coronal.set_data([], [])
            self.points_coronal.set_data([], [])
            self.line_sagittal.set_data([], [])
            self.points_sagittal.set_data([], [])
        else:
            points_arr = np.array(self.points)
            
            # Axial view
            self.points_axial.set_data(points_arr[:, 0], points_arr[:, 1])
            if len(self.points) >= 2:
                curve = self.create_curve()
                self.line_axial.set_data(curve[:, 0], curve[:, 1])
            else:
                self.line_axial.set_data([], [])
            
            # Coronal view
            self.points_coronal.set_data(points_arr[:, 0], points_arr[:, 2])
            if len(self.points) >= 2:
                self.line_coronal.set_data(curve[:, 0], curve[:, 2])
            else:
                self.line_coronal.set_data([], [])
            
            # Sagittal view
            self.points_sagittal.set_data(points_arr[:, 1], points_arr[:, 2])
            if len(self.points) >= 2:
                self.line_sagittal.set_data(curve[:, 1], curve[:, 2])
            else:
                self.line_sagittal.set_data([], [])
        
        self.info_text.set_text(self.get_info_text())
        self.fig.canvas.draw_idle()
    
    def create_curve(self):
        """إنشاء منحنى من النقاط"""
        if len(self.points) < 2:
            return np.array([])
        
        points_arr = np.array(self.points, dtype=float)
        
        if len(self.points) == 2:
            # منحنى بين نقطتين
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
            # استخدام كل النقاط
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
        """إنشاء منحنى بدقة عالية للـ MPR"""
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
        """توليد الـ Curved MPR"""
        if len(self.points) < 2:
            print("⚠ Need at least 2 points to trace aorta!")
            self.ax_mpr.clear()
            self.ax_mpr.text(0.5, 0.5, '⚠ Add at least 2 points to trace the aorta!', 
                           ha='center', va='center', fontsize=16, color='red', fontweight='bold')
            self.ax_mpr.axis('off')
            self.fig.canvas.draw_idle()
            return
        
        print("\n" + "="*50)
        print("Generating Aorta Curved MPR...")
        start_time = time.time()
        
        # إنشاء المسار بنقاط أكثر للوضوح
        curve = self.create_curve_high_res()
        
        # استخراج MPR
        mpr_image = self.extract_mpr(curve)
        
        # تحسين التباين - مهم للأوعية الدموية
        if mpr_image.max() > 0:
            # Adaptive histogram equalization
            p1, p99 = np.percentile(mpr_image[mpr_image > 0], (1, 99))
            mpr_enhanced = np.clip((mpr_image - p1) / (p99 - p1 + 1e-10), 0, 1)
            
            # زيادة الـ contrast للأوعية
            mpr_enhanced = np.power(mpr_enhanced, 0.75)
        else:
            mpr_enhanced = mpr_image
        
        # عرض النتيجة بجودة أعلى
        self.ax_mpr.clear()
        self.ax_mpr.set_facecolor('#000000')
        
        # استخدام aspect ratio محسّن
        aspect_ratio = mpr_enhanced.shape[0] / mpr_enhanced.shape[1]
        
        # استخدام colormap مناسب للأوعية الدموية
        im = self.ax_mpr.imshow(mpr_enhanced, cmap='hot', 
                                aspect=aspect_ratio * 2.2,
                                interpolation='lanczos',
                                vmin=0, vmax=1)
        
        # إضافة colorbar احترافي
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(self.ax_mpr)
        cax = divider.append_axes("right", size="1.2%", pad=0.18)
        cax.set_facecolor('#0a0a0a')
        cbar = plt.colorbar(im, cax=cax)
        cbar.set_label('INTENSITY', fontsize=11, fontweight='bold', color='white')
        cbar.ax.tick_params(labelsize=9, colors='white')
        cbar.outline.set_edgecolor('#E91E63')
        cbar.outline.set_linewidth(2)
        
        self.ax_mpr.set_title(f'🫀 AORTA CURVED MPR  |  {time.time()-start_time:.2f}s  |  High Resolution ⬤', 
                             fontweight='bold', fontsize=16, color='#FF1744',
                             pad=15,
                             bbox=dict(boxstyle='round,pad=0.8', facecolor='#0a0a0a',
                                     edgecolor='#FF1744', linewidth=3, alpha=0.98))
        self.ax_mpr.set_xlabel('Position along aortic path  →', fontsize=13, fontweight='bold', color='#F48FB1')
        self.ax_mpr.set_ylabel('⟂  Vessel cross-section (voxels)', fontsize=13, fontweight='bold', color='#F48FB1')
        self.ax_mpr.grid(True, alpha=0.15, linestyle='--', linewidth=1, color='#E91E63')
        
        # تحسين ticks
        self.ax_mpr.tick_params(labelsize=10, colors='#90A4AE')
        self.ax_mpr.spines['bottom'].set_color('#E91E63')
        self.ax_mpr.spines['left'].set_color('#E91E63')
        self.ax_mpr.spines['bottom'].set_linewidth(2)
        self.ax_mpr.spines['left'].set_linewidth(2)
        self.ax_mpr.spines['top'].set_visible(False)
        self.ax_mpr.spines['right'].set_visible(False)
        
        # إضافة معلومات تفصيلية
        path_length = np.sum(np.linalg.norm(np.diff(curve, axis=0), axis=1))
        info_str = (f"📊 Resolution: {mpr_enhanced.shape[1]}×{mpr_enhanced.shape[0]} px  |  "
                   f"📏 Aorta Length: {path_length:.1f} voxels  |  "
                   f"↪ Curve: {self.curve_factor:.2f}")
        self.ax_mpr.text(0.02, 0.98, info_str, transform=self.ax_mpr.transAxes,
                        fontsize=10.5, verticalalignment='top', fontweight='bold', color='white',
                        bbox=dict(boxstyle='round,pad=0.6', facecolor='#1a1a1a', alpha=0.95, 
                                edgecolor='#E91E63', linewidth=2))
        
        # إضافة مقياس على المحور X
        num_ticks = 6
        x_ticks = np.linspace(0, mpr_enhanced.shape[1]-1, num_ticks)
        x_labels = [f'{i*100/(num_ticks-1):.0f}%' for i in range(num_ticks)]
        self.ax_mpr.set_xticks(x_ticks)
        self.ax_mpr.set_xticklabels(x_labels)
        
        self.fig.canvas.draw_idle()
        print(f"✓ Aorta MPR generated in {time.time()-start_time:.1f} seconds")
        print(f"  Resolution: {mpr_enhanced.shape}")
        print("="*50)
    
    def extract_mpr(self, curve_path):
        """استخراج Curved MPR"""
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
        """حساب الاتجاهات العمودية"""
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
        """مسح كل النقاط"""
        self.points = []
        self.ax_mpr.clear()
        self.ax_mpr.set_title('🫀 AORTA CURVED MPR - Trace path and click "Generate MPR" ★', 
                             fontweight='bold', fontsize=13, color='#FF1744')
        self.ax_mpr.axis('off')
        self.update_display()
        print("✓ All points cleared")
    
    def undo_last(self, event):
        """التراجع عن آخر نقطة"""
        if self.points:
            removed = self.points.pop()
            print(f"✓ Removed point: {removed}")
            self.update_display()
    
    def update_curve_factor(self, val):
        """تحديث معامل الانحناء"""
        self.curve_factor = val
        if len(self.points) >= 2:
            self.update_display()
    
    def show(self):
        """عرض الواجهة"""
        plt.show()

def main():
    """البرنامج الرئيسي"""
    print("="*60)
    print("INTERACTIVE AORTA CURVED MPR VIEWER")
    print("="*60)
    
    # تحميل البيانات
    print("\n🫀 Loading aorta data...")
    file_path = "Aorta.nii"
    img = nib.load(file_path)
    data = img.get_fdata()
    
    print(f"Original volume: {data.shape}")
    print("\n🫀 Starting interactive aorta viewer...")
    print("\nInstructions:")
    print("  1. Click on any view (Axial/Coronal/Sagittal) to trace aorta path")
    print("  2. Add at least 2 points along the vessel")
    print("  3. Start from aortic root and trace downward")
    print("  4. Adjust 'Curvature' slider for aortic arch")
    print("  5. Click 'Generate MPR' to create the curved reconstruction")
    print("  6. Use 'Undo Last' to remove last point")
    print("  7. Use 'Clear Points' to start over")
    print("\n" + "="*60 + "\n")
    
    # إنشاء وعرض الـ viewer
    viewer = InteractiveCurvedMPR(data, downsample_factor=2)
    viewer.show()

if __name__ == "__main__":
    main()