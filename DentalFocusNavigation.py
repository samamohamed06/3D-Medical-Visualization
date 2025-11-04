import pyvista as pv
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')
import os
os.environ['PYTHONWARNINGS'] = 'ignore'
pv.set_error_output_file('nul')


class FixedNavigationApp:
    """
    🎮 FIXED NAVIGATION - التحكم التفاعلي
    ════════════════════════════════════════
    المميزات:
    • تقطيع أفقي تشريحي (5 طبقات)
    • التحكم بلوحة المفاتيح
    • دوران بالماوس
    """
    
    def _init_(self):
        self.mesh = None
        self.current_file = None
    
    def load_file(self, file_path):
        """تحميل ملف 3D"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                print(f"[✗] File not found: {file_path}")
                return False
            
            if file_path.suffix.lower() in ['.nii', '.gz']:
                import nibabel as nib
                print(f"[⏳] Loading NII file: {file_path.name}...")
                nii = nib.load(str(file_path))
                data = nii.get_fdata()
                
                print(f"  Data shape: {data.shape}")
                print(f"  Data range: [{data.min():.2f}, {data.max():.2f}]")
                
                # إنشاء ImageData من البيانات
                grid = pv.ImageData(dimensions=data.shape)
                grid['values'] = data.flatten(order='F')
                
                # إنشاء الـ mesh بـ contour أو threshold
                threshold = data.mean() + data.std() * 0.5
                print(f"  Using threshold: {threshold:.2f}")
                
                self.mesh = grid.contour(isosurfaces=5, scalars='values')
                
                # لو الـ mesh فاضي، جرب threshold
                if self.mesh.n_points == 0:
                    print("  [⚠] Contour empty, trying threshold...")
                    self.mesh = grid.threshold(value=threshold, scalars='values')
                
                print(f"  Mesh points: {self.mesh.n_points}")
                print(f"  Mesh cells: {self.mesh.n_cells}")
            else:
                self.mesh = pv.read(str(file_path))
            
            self.current_file = str(file_path)
            print(f"[✓] Loaded successfully: {file_path.name}")
            return True
            
        except Exception as e:
            print(f"[✗] Error loading file: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_dicom_folder(self, folder_path):
        """تحميل مجلد DICOM"""
        try:
            import pydicom
            from pydicom import dcmread
            
            folder_path = Path(folder_path)
            dicom_files = sorted(list(folder_path.glob('*.dcm')))
            
            if not dicom_files:
                dicom_files = [f for f in folder_path.iterdir() if f.is_file()]
            
            if not dicom_files:
                print("[✗] No DICOM files found")
                return False
            
            first_slice = dcmread(str(dicom_files[0]))
            img_shape = (int(first_slice.Rows), int(first_slice.Columns), len(dicom_files))
            volume = np.zeros(img_shape)
            
            for i, dicom_file in enumerate(dicom_files):
                ds = dcmread(str(dicom_file))
                volume[:, :, i] = ds.pixel_array
            
            grid = pv.ImageData(dimensions=volume.shape)
            grid['values'] = volume.flatten(order='F')
            self.mesh = grid.contour(isosurfaces=5)
            
            self.current_file = str(folder_path)
            print(f"[✓] Loaded {len(dicom_files)} DICOM slices")
            return True
            
        except Exception as e:
            print(f"[✗] Error: {str(e)}")
            return False
    
    def create_demo_tooth(self):
        """إنشاء سن تجريبي"""
        crown = pv.Sphere(radius=1.0, center=(0, 1, 0), theta_resolution=50, phi_resolution=50)
        crown = crown.scale([1.0, 1.4, 1.0]).triangulate()
        
        root = pv.Cone(center=(0, -0.5, 0), direction=(0, -1, 0), 
                       height=2.5, radius=0.6, resolution=50).triangulate()
        
        try:
            tooth = crown.boolean_union(root)
        except:
            tooth = crown + root
        
        self.mesh = tooth.smooth(n_iter=100, relaxation_factor=0.15)
        print("[✓] Demo tooth created")
        return self.mesh
    
    def run_fixed_navigation(self):
        """تشغيل Fixed Navigation"""
        if self.mesh is None:
            print("⚠ Load a model first!")
            return False
        
        print("\n[▶] FIXED NAVIGATION - Anatomical Horizontal Slicing")
        print("═" * 60)
        
        plotter = pv.Plotter(window_size=[1400, 900])
        plotter.background_color = '#0a0a0a'
        
        center = self.mesh.center
        bounds = self.mesh.bounds
        y_range = bounds[3] - bounds[2]
        num_slices = 5
        
        parts = []
        slice_meshes = []
        
        # تقسيم إلى 5 طبقات تشريحية
        for i in range(num_slices):
            y_max = bounds[3] - (y_range / num_slices) * i
            y_min = bounds[3] - (y_range / num_slices) * (i + 1)
            
            try:
                part = self.mesh.clip_box(
                    bounds=[bounds[0], bounds[1], y_min, y_max, bounds[4], bounds[5]],
                    invert=False
                )
                
                if part.n_points > 0:
                    colors = ['#FFFFFF', '#FFE4C4', '#FFDAB9', '#FFB380', '#CD853F']
                    names = ['Crown/Teeth', 'Upper Jaw', 'Middle', 'Lower Jaw', 'Roots']
                    
                    slice_meshes.append(part.copy())
                    
                    actor = plotter.add_mesh(
                        part,
                        color=colors[i],
                        opacity=0.95,
                        smooth_shading=True,
                        pbr=True,
                        metallic=0.2,
                        roughness=0.4
                    )
                    
                    parts.append({
                        'index': i,
                        'name': names[i],
                        'mesh': part,
                        'actor': actor,
                        'visible': True,
                        'offset': 0.0
                    })
            except:
                pass
        
        if not parts:
            print("  [!] No parts created")
            return False
        
        max_offset = y_range * 0.3
        
        def move_slice(slice_index, direction):
            """تحريك طبقة"""
            if slice_index < len(parts):
                part = parts[slice_index]
                
                if direction == 'up':
                    part['offset'] = min(part['offset'] + 0.05, max_offset)
                elif direction == 'down':
                    part['offset'] = max(part['offset'] - 0.05, -max_offset)
                elif direction == 'reset':
                    part['offset'] = 0.0
                
                plotter.remove_actor(part['actor'])
                
                moved_mesh = slice_meshes[slice_index].copy()
                moved_mesh.translate([0, part['offset'], 0], inplace=True)
                
                colors = ['#FFFFFF', '#FFE4C4', '#FFDAB9', '#FFB380', '#CD853F']
                new_actor = plotter.add_mesh(
                    moved_mesh,
                    color=colors[slice_index],
                    opacity=0.95,
                    smooth_shading=True,
                    pbr=True,
                    metallic=0.2,
                    roughness=0.4
                )
                
                part['actor'] = new_actor
                part['mesh'] = moved_mesh
                plotter.render()
                
                print(f"  {part['name']}: offset {part['offset']:.2f}")
        
        def toggle_visibility(slice_index):
            """إظهار/إخفاء طبقة"""
            if slice_index < len(parts):
                parts[slice_index]['visible'] = not parts[slice_index]['visible']
                parts[slice_index]['actor'].SetVisibility(parts[slice_index]['visible'])
                plotter.render()
                print(f"  {parts[slice_index]['name']}: {'ON' if parts[slice_index]['visible'] else 'OFF'}")
        
        instructions = (
            "🦷 ANATOMICAL Horizontal Slicing\n\n"
            "Layers (top→bottom):\n"
            "  [1] = Crown/Teeth\n"
            "  [2] = Upper Jaw\n"
            "  [3] = Middle\n"
            "  [4] = Lower Jaw\n"
            "  [5] = Roots\n\n"
            "Controls:\n"
            "  [1-5] = Toggle layer\n"
            "  [W] = Move UP\n"
            "  [S] = Move DOWN\n"
            "  [R] = Reset\n\n"
            "Mouse: Rotate/Zoom"
        )
        
        plotter.add_text(instructions, position='upper_left', color='white', font_size=11)
        
        selected_slice = [0]
        
        def on_key(key):
            if key in ['1', '2', '3', '4', '5']:
                idx = int(key) - 1
                if idx < len(parts):
                    selected_slice[0] = idx
                    toggle_visibility(idx)
            elif key == 'w':
                move_slice(selected_slice[0], 'up')
            elif key == 's':
                move_slice(selected_slice[0], 'down')
            elif key == 'r':
                move_slice(selected_slice[0], 'reset')
        
        for i in range(len(parts)):
            plotter.add_key_event(str(i + 1), lambda k=str(i+1): on_key(k))
        
        plotter.add_key_event('w', lambda: on_key('w'))
        plotter.add_key_event('s', lambda: on_key('s'))
        plotter.add_key_event('r', lambda: on_key('r'))
        
        plotter.camera_position = [(5, 3, 5), center, (0, 1, 0)]
        
        print("\n  ✓ Anatomical layers created!")
        print("  Select with 1-5, move with W/S")
        print("═" * 60 + "\n")
        
        plotter.show()
        return True


# ═══════════════════════════════════════════════════════════════
# 🚀 تشغيل البرنامج
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🎮 FIXED NAVIGATION - Interactive Control")
    print("="*60)
    
    app = FixedNavigationApp()
    
    # البحث عن ملف dental.nii في المجلدات المحتملة
    possible_paths = [
        "dental.nii",
        "dental.nii.gz",
        "data/dental.nii",
        "data/dental.nii.gz",
        "./dental.nii",
        "../dental.nii",
    ]
    
    loaded = False
    for path in possible_paths:
        if Path(path).exists():
            print(f"\n[🔍] Found file: {path}")
            if app.load_file(path):
                loaded = True
                break
    
    # لو مش لاقي الملف، استخدم Demo
    if not loaded:
        print("\n[ℹ] dental.nii not found, using demo tooth...")
        print("  💡 Place dental.nii in the same folder as this script")
        app.create_demo_tooth()
    
    if app.mesh is not None:
        app.run_fixed_navigation()
    else:
        print("⚠ No data loaded!")