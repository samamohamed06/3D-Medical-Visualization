import pyvista as pv
import numpy as np

# تحميل ملف .obj
mesh = pv.read('heart_assembled (1).obj')

# تنظيف الـ mesh
mesh = mesh.clean()

# حساب الـ normals
mesh = mesh.compute_normals(cell_normals=True, point_normals=True, 
                            split_vertices=False, flip_normals=False)

# إنشاء plotter
plotter = pv.Plotter(window_size=[1400, 1000])
plotter.enable_anti_aliasing('ssaa')

# ==============================================================
# الطريقة الصحيحة: نلون كل حاجة بلون القلب الطبيعي
# ==============================================================

# لون عضلة القلب الحقيقي - أحمر لحمي واقعي
heart_color = '#A52A2A'  # Brown-red (لون عضلة القلب الحقيقي)

# إضافة الـ mesh كله بلون واحد واقعي
plotter.add_mesh(mesh,
                color=heart_color,
                smooth_shading=True,
                show_edges=False,
                opacity=1.0,
                ambient=0.25,           # إضاءة محيطية معتدلة
                diffuse=0.65,           # انتشار الضوء
                specular=0.4,           # لمعان خفيف (القلب مش لامع قوي)
                specular_power=20,      # تركيز اللمعان
                pbr=True,               # Physically Based Rendering
                metallic=0.1,           # معدني شوية جداً
                roughness=0.7)          # خشونة عالية (سطح عضوي)

# ==============================================================
# إضاءة واقعية جداً (زي studio lighting)
# ==============================================================

# الضوء الرئيسي - Key Light (قوي من قدام وفوق)
key_light = pv.Light(position=(15, 15, 20), 
                     light_type='scene light',
                     intensity=1.2,
                     color='white')
plotter.add_light(key_light)

# ضوء الملء - Fill Light (ناعم من الجانب)
fill_light = pv.Light(position=(-10, 10, 15), 
                      light_type='scene light',
                      intensity=0.5,
                      color='white')
plotter.add_light(fill_light)

# ضوء خلفي - Rim Light (للحواف والعمق)
rim_light = pv.Light(position=(0, -15, 10), 
                     light_type='scene light',
                     intensity=0.4,
                     color='white')
plotter.add_light(rim_light)

# ضوء علوي ناعم
top_light = pv.Light(position=(0, 0, 25), 
                     light_type='scene light',
                     intensity=0.3,
                     color='white')
plotter.add_light(top_light)

# ==============================================================
# خلفية احترافية
# ==============================================================
plotter.set_background('#F5F5F5', top='#E8E8E8')  # رمادي فاتح gradient

# ==============================================================
# إعدادات الكاميرا
# ==============================================================
plotter.camera_position = 'iso'  # زاوية isometric
plotter.camera.zoom(1.4)
plotter.camera.elevation = 20
plotter.camera.azimuth = 30

# ==============================================================
# واجهة نظيفة
# ==============================================================

# عنوان بسيط
plotter.add_text('Human Heart - 3D Anatomical Model', 
                 position='upper_edge', 
                 font_size=20, 
                 color='#8B0000',
                 font='arial')

# معلومات النموذج
info_text = f"Vertices: {mesh.n_points:,} | Faces: {mesh.n_cells:,}"
plotter.add_text(info_text,
                position='lower_edge',
                font_size=11,
                color='gray',
                font='courier')

# المحاور (اختياري - يمكن إزالتها للشكل الأنظف)
# plotter.add_axes(line_width=2, labels_off=True)

# ==============================================================
# معلومات في الكونسول
# ==============================================================
print("\n" + "="*70)
print("🫀  HUMAN HEART - 3D MODEL")
print("="*70)
print(f"\n📊 Model Statistics:")
print(f"   Vertices: {mesh.n_points:,}")
print(f"   Faces: {mesh.n_cells:,}")
print(f"   Surface Area: {mesh.area:.2f} mm²")
print(f"   Volume: {mesh.volume:.2f} mm³")

bounds = mesh.bounds
dims = [bounds[1]-bounds[0], bounds[3]-bounds[2], bounds[5]-bounds[4]]
print(f"\n📏 Dimensions:")
print(f"   Width (X): {dims[0]:.2f} mm")
print(f"   Depth (Y): {dims[1]:.2f} mm")
print(f"   Height (Z): {dims[2]:.2f} mm")

print(f"\n🎮 Controls:")
print(f"   Left Click + Drag    → Rotate")
print(f"   Right Click + Drag   → Pan")
print(f"   Scroll Wheel         → Zoom")
print(f"   'r'                  → Reset view")
print(f"   's'                  → Screenshot")
print(f"   'q'                  → Quit")
print("="*70 + "\n")

# عرض النموذج
plotter.show()