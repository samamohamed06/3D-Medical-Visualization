import pyvista as pv
import numpy as np
from pathlib import Path
import warnings
import time

warnings.filterwarnings('ignore')
import os
os.environ['PYTHONWARNINGS'] = 'ignore'
pv.set_error_output_file('nul')


class UltraFastFlyThrough:
    """
    ✈ ULTRA FAST FLY-THROUGH
    ════════════════════════════════════════
    🚀 User draws path + Ultra fast rendering
    • Draw your own camera path (5+ points)
    • Optimized loading & rendering
    • Real-time display with black background
    """
    
    def __init__(self):
        self.mesh = None
        self.user_camera_path = []
        self.animation_speed = 0.0005  # 0.5ms per frame = INSANE SPEED! 🚀⚡
    
    def load_file_fast(self, file_path):
        """تحميل سريع جداً"""
        try:
            file_path = Path(file_path)
            print(f"[⏳] Loading: {file_path.name}")
            print(f"    Location: {file_path.parent}")
            
            if not file_path.exists():
                print(f"[✗] File not found!")
                return False
            
            if file_path.suffix.lower() in ['.nii', '.gz']:
                import nibabel as nib
                
                nii = nib.load(str(file_path))
                data = nii.get_fdata()
                
                print(f"  ✓ Shape: {data.shape}")
                print(f"  ✓ Data range: [{data.min():.2f}, {data.max():.2f}]")
                
                # استخدام threshold مباشر (أسرع من contour)
                grid = pv.ImageData(dimensions=data.shape)
                grid['values'] = data.flatten(order='F')
                
                threshold = data.mean() + data.std() * 0.5  # threshold أعلى = نقاط أقل
                print(f"  ✓ Threshold: {threshold:.2f}")
                
                self.mesh = grid.threshold(value=threshold, scalars='values')
                
                # لو فاضي، استخدم contour
                if self.mesh.n_points == 0:
                    print(f"  ⚠ Threshold empty, trying contour...")
                    self.mesh = grid.contour(isosurfaces=3, scalars='values')
                
                print(f"  ✓ Initial points: {self.mesh.n_points}")
                
                # تبسيط للسرعة - تحويل لـ PolyData أولاً
                if self.mesh.n_points > 100000:
                    print(f"  ⚙ Simplifying mesh...")
                    
                    # استخراج السطح الخارجي (أسرع وأصغر)
                    self.mesh = self.mesh.extract_geometry()
                    print(f"      After extract_geometry: {self.mesh.n_points} points")
                    
                    # لو لسه كبير، حوّل لمثلثات وبسّط
                    if self.mesh.n_points > 50000:
                        # تحويل لمثلثات
                        print(f"      Converting to triangles...")
                        self.mesh = self.mesh.triangulate()
                        print(f"      After triangulate: {self.mesh.n_points} points")
                        
                        # الآن نقدر نستخدم decimate
                        print(f"      Decimating...")
                        self.mesh = self.mesh.decimate(0.85)  # احتفظ بـ 15% فقط = أسرع!
                        print(f"      After decimate: {self.mesh.n_points} points")
                
                print(f"[✓] Successfully loaded: {self.mesh.n_points} points\n")
                return True
            else:
                self.mesh = pv.read(str(file_path))
                print(f"[✓] Loaded: {self.mesh.n_points} points\n")
                return True
                
        except Exception as e:
            print(f"[✗] Error loading file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def auto_load_data(self):
        """تحميل dental.nii فقط - لا يوجد بديل"""
        print("\n[🔍] Looking for dental.nii...")
        
        dental_file = Path("dental.nii")
        
        if dental_file.exists():
            print(f"[✓] Found: {dental_file.absolute()}\n")
            return self.load_file_fast(dental_file)
        else:
            print(f"[✗] dental.nii NOT FOUND!")
            print(f"    Expected location: {dental_file.absolute()}")
            print(f"    Please place dental.nii in the same folder as this script.")
            return False
    
    def draw_camera_path(self):
        """رسم مسار الكاميرا يدوياً"""
        if self.mesh is None:
            print("⚠ No model loaded!")
            return False
        
        print("\n[🎯] Draw Camera Path")
        print("═" * 60)
        print("  ⚠  First point should be OUTSIDE the model")
        print("  Click minimum 5 points")
        print("  Close window when finished")
        print("═" * 60 + "\n")
        
        self.user_camera_path = []
        center = self.mesh.center
        bounds = self.mesh.bounds
        
        max_dist = max(
            bounds[1] - bounds[0],
            bounds[3] - bounds[2],
            bounds[5] - bounds[4]
        )
        
        suggested_start = [
            center[0] + max_dist * 2,
            center[1] + max_dist,
            center[2] + max_dist
        ]
        
        # نافذة رسم المسار
        plotter = pv.Plotter(window_size=[1400, 900])
        plotter.background_color = '#000000'  # خلفية سوداء
        
        # عرض النموذج شبه شفاف
        plotter.add_mesh(
            self.mesh, 
            color='#FFE4C4',
            opacity=0.4, 
            smooth_shading=True,
            pbr=True,
            metallic=0.2,
            roughness=0.5
        )
        
        # نقطة البداية المقترحة
        start_marker = pv.Sphere(radius=max_dist * 0.05, center=suggested_start)
        plotter.add_mesh(start_marker, color='#00FF00', opacity=0.8)
        
        path_points = []
        point_actors = []
        line_actors = []
        
        def on_point_picked(picked_point):
            if picked_point is not None and len(picked_point) == 3:
                path_points.append(list(picked_point))
                
                # لون النقطة: أخضر للأولى، أصفر للباقي
                color = '#00FF00' if len(path_points) == 1 else '#FFFF00'
                
                # إضافة كرة عند النقطة
                marker = pv.Sphere(radius=max_dist * 0.03, center=picked_point)
                actor = plotter.add_mesh(marker, color=color, opacity=1.0)
                point_actors.append(actor)
                
                # رسم خط للنقطة السابقة
                if len(path_points) > 1:
                    line = pv.Line(path_points[-2], path_points[-1])
                    line_actor = plotter.add_mesh(line, color='#FF00FF', line_width=3)
                    line_actors.append(line_actor)
                
                # تحديث النص
                status = "🟢 START" if len(path_points) == 1 else f"Point #{len(path_points)}"
                text = (f"Camera Path: {len(path_points)} points\n\n"
                       f"Last: {status}\n\n"
                       f"🟢 Green = START (outside!)\n"
                       f"🟡 Yellow = Path points\n"
                       f"💜 Purple = Path line\n\n"
                       f"Min: 5 points\n"
                       f"Close window when done")
                
                plotter.add_text(
                    text,
                    position='upper_left', 
                    color='white',
                    font_size=14,
                    name='info_text'
                )
                
                print(f"  ✓ {status} at {picked_point}")
        
        # تفعيل اختيار النقاط
        plotter.enable_surface_point_picking(
            callback=on_point_picked,
            show_point=False,
            use_mesh=True,
            show_message=False
        )
        
        # نص البداية
        plotter.add_text(
            "Camera Path: 0 points\n\n"
            "🟢 Small green sphere = Suggested START\n"
            "Click OUTSIDE model first!\n"
            "Then create path inside\n\n"
            "Min: 5 points\n"
            "Close window when done",
            position='upper_left',
            color='white',
            font_size=14,
            name='info_text'
        )
        
        plotter.camera_position = [suggested_start, center, (0, 1, 0)]
        plotter.show()
        
        if len(path_points) < 5:
            print(f"\n⚠ Not enough points! You added {len(path_points)}. Need 5+")
            return False
        
        self.user_camera_path = path_points
        print(f"\n[✓] Path created: {len(path_points)} points\n")
        return True
    
    def play_ultra_fast(self):
        """عرض سريع جداً مع شكل جميل"""
        if not self.user_camera_path or len(self.user_camera_path) < 5:
            print("⚠ Draw camera path first!")
            return False
        
        print("\n[▶] INSANE SPEED FLY-THROUGH 🚀💨")
        print("═" * 60)
        
        try:
            center = self.mesh.center
            bounds = self.mesh.bounds
            height = bounds[3] - bounds[2]
            
            # عدد فريمات أقل = سرعة خيالية!
            num_frames = 100  # كان 200، دلوقتي 100 فقط!
            path_spline = pv.Spline(self.user_camera_path, num_frames)
            camera_positions = path_spline.points
            
            start_point = self.user_camera_path[0]
            
            # نافذة مع خلفية سوداء
            plotter = pv.Plotter(window_size=[1400, 900])
            plotter.background_color = '#000000'  # خلفية سوداء تماماً
            
            # متغيرات
            frame_counter = [0]
            is_playing = [True]
            last_time = [time.time()]
            
            print(f"  Frames: {num_frames}")
            print(f"  Speed: {self.animation_speed}s/frame (INSANE!)")
            print(f"  Press 'q' to stop\n")
            
            def update_fast():
                """تحديث سريع مع شكل جميل"""
                if not is_playing[0] or frame_counter[0] >= num_frames:
                    return
                
                frame = frame_counter[0]
                plotter.clear()
                
                cam_pos = camera_positions[frame]
                
                # النموذج - شكل جميل
                plotter.add_mesh(
                    self.mesh,
                    color='#FFE4C4',  # لون بيج/عظمي
                    opacity=0.85,
                    smooth_shading=True,
                    pbr=True,
                    metallic=0.2,
                    roughness=0.4,
                    specular=0.5
                )
                
                # المسار - خط أخضر مضيء
                plotter.add_mesh(
                    path_spline, 
                    color='#00FF00', 
                    line_width=3,
                    opacity=0.8
                )
                
                # نقطة البداية - كرة خضراء
                start_sphere = pv.Sphere(
                    radius=height * 0.06,
                    center=start_point,
                    theta_resolution=20,
                    phi_resolution=20
                )
                plotter.add_mesh(start_sphere, color='#00FF00', opacity=0.9)
                
                # علامة الكاميرا - كرة حمراء
                cam_marker = pv.Sphere(
                    radius=height * 0.03,
                    center=cam_pos,
                    theta_resolution=15,
                    phi_resolution=15
                )
                plotter.add_mesh(cam_marker, color='#FF0000', opacity=1.0)
                
                # حركة الكاميرا أسرع بكتير!
                look_ahead = min(40, num_frames - frame - 1)  # كان 20، دلوقتي 40!
                look_at = camera_positions[frame + look_ahead] if look_ahead > 0 else center
                
                plotter.camera_position = [cam_pos, look_at, [0, 1, 0]]
                
                # حالة الموقع
                try:
                    is_inside = self.mesh.select_enclosed_points(pv.PolyData([cam_pos]))['SelectedPoints'][0]
                    location = "INSIDE 🔴" if is_inside else "OUTSIDE 🟢"
                    location_color = '#FF4444' if is_inside else '#44FF44'
                except:
                    location = "MOVING"
                    location_color = '#FFFFFF'
                
                # حساب FPS
                progress = int((frame / num_frames) * 100)
                current_time = time.time()
                fps = 1.0 / (current_time - last_time[0] + 0.001)
                last_time[0] = current_time
                
                # نص المعلومات
                plotter.add_text(
                    f"Fly-Through: {progress}%\n"
                    f"Frame: {frame}/{num_frames}\n"
                    f"Camera: {location}\n"
                    f"FPS: {fps:.0f}\n\n"
                    f"🟢 = Start Point\n"
                    f"🔴 = Current Camera\n"
                    f"Press 'q' to stop",
                    position='upper_left',
                    color=location_color,
                    font_size=15,
                    name='info'
                )
                
                frame_counter[0] += 1
                
                if frame % 20 == 0:  # كان 40، دلوقتي 20
                    print(f"  {progress}% | FPS: {fps:.0f} | {location}")
                
                plotter.render()
            
            def stop_animation():
                is_playing[0] = False
                print("\n[⏸] Stopped by user")
            
            plotter.add_key_event('q', stop_animation)
            
            # بدء العرض
            plotter.show(auto_close=False, interactive_update=True)
            
            # Loop أسرع من الصاروخ! 🚀
            while is_playing[0] and not plotter._closed and frame_counter[0] < num_frames:
                update_fast()
                time.sleep(self.animation_speed)  # 0.5ms = INSANE!
            
            if not plotter._closed:
                plotter.show()
            
            print("\n[✓] Animation Complete!")
            print("═" * 60)
            return True
            
        except Exception as e:
            print(f"[✗] Error: {e}")
            import traceback
            traceback.print_exc()
            return False


# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ⚡ ULTRA FAST FLY-THROUGH")
    print("  🎯 User-Defined Path + Black Background")
    print("  📄 Reads: dental.nii ONLY")
    print("="*60)
    
    app = UltraFastFlyThrough()
    
    # تحميل dental.nii فقط
    if app.auto_load_data():
        # رسم المسار يدوياً
        if app.draw_camera_path():
            # تشغيل الأنيميشن
            app.play_ultra_fast()
    else:
        print("\n" + "="*60)
        print("  ⚠ FAILED TO START")
        print("  Please make sure dental.nii is in:")
        print(f"  {Path('dental.nii').absolute()}")
        print("="*60)