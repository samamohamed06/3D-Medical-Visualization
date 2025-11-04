#!/usr/bin/env python3
# -- coding: utf-8 --
"""
Spine, Spinal Cord and Muscles Visualization with Interactive Clipping Planes
Reads OBJ files from multiple folders
Compatible with PyVista 0.37+
"""

import numpy as np
import pyvista as pv
import vtk
import os
import glob

# Force on-screen rendering
os.environ['PYVISTA_OFF_SCREEN'] = '0'
pv.OFF_SCREEN = False
pv.global_theme.multi_samples = 4

print("="*70)
print("HIGH QUALITY SPINE, SPINAL CORD & MUSCLES VISUALIZATION")
print("="*70)

# Define folder paths
MUSCLES_PATH = r"E:\Task 3\muscelsdataset"
VERTEBRAE_PATH = r"E:\Task 3\spinalcorddataset"
SPINAL_CORD_PATH = r"C:\Users\hp\Downloads\project_3\bones\bones"

# Load OBJ files from folders
components = []

def load_obj_files(folder_path, category):
    """Load all OBJ files from a folder"""
    print(f"\n📁 Loading {category} from: {folder_path}")
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return []
    
    obj_files = glob.glob(os.path.join(folder_path, "*.obj"))
    
    if len(obj_files) == 0:
        print(f"⚠ No .obj files found in {folder_path}")
        return []
    
    print(f"Found {len(obj_files)} OBJ files")
    
    loaded = []
    for obj_file in obj_files:
        filename = os.path.basename(obj_file)
        try:
            mesh = pv.read(obj_file)
            
            # Clean and smooth the mesh
            mesh = mesh.clean()
            mesh = mesh.smooth(n_iter=15, relaxation_factor=0.1)
            
            # Calculate center Z coordinate
            cz = np.mean(mesh.points[:, 2])
            
            loaded.append({
                'mesh': mesh,
                'name': filename,
                'category': category,
                'cz': cz
            })
            
            print(f"  ✅ Loaded: {filename} ({len(mesh.points)} vertices)")
            
        except Exception as e:
            print(f"  ❌ Error loading {filename}: {e}")
    
    return loaded

# Load muscles
muscles = load_obj_files(MUSCLES_PATH, "muscle")

# Load vertebrae (bones)
vertebrae = load_obj_files(VERTEBRAE_PATH, "vertebra")

# Load spinal cord
spinal_cord = load_obj_files(SPINAL_CORD_PATH, "spinal_cord")

# Sort vertebrae by Z coordinate and assign numbers
vertebrae.sort(key=lambda x: x['cz'], reverse=True)
for idx, vert in enumerate(vertebrae):
    vert['number'] = idx + 1

# Combine all components
components = vertebrae + spinal_cord + muscles

print(f"\n✅ Total loaded: {len(components)} objects")
print(f"   - {len(vertebrae)} vertebrae (numbered 1-{len(vertebrae)})")
print(f"   - {len(spinal_cord)} spinal cord")
print(f"   - {len(muscles)} muscles")

if len(components) == 0:
    print("❌ No objects found!")
    exit(1)

# Create plotter
plotter = pv.Plotter(window_size=(1920, 1080))
plotter.set_background((0.1, 0.12, 0.15))

# Enable quality features
try:
    plotter.enable_anti_aliasing()
    plotter.enable_eye_dome_lighting()
except:
    print("⚠ Some rendering features not available")

# Add objects to scene
actors = []
vertebra_colors = [
    (0.92, 0.72, 0.52),
    (0.88, 0.68, 0.48),
    (0.84, 0.64, 0.44),
    (0.90, 0.70, 0.50),
    (0.86, 0.66, 0.46),
]

# Lighter red colors for muscles
muscle_colors = [
    (1.0, 0.5, 0.5),
    (1.0, 0.55, 0.55),
    (0.95, 0.45, 0.45),
    (1.0, 0.6, 0.6),
    (0.98, 0.52, 0.52),
]

spinal_cord_colors = [
    (0.95, 0.95, 0.95),
    (0.90, 0.90, 0.92),
    (0.92, 0.92, 0.94),
    (0.94, 0.94, 0.96),
]

print("\nAdding objects to scene...")
vertebra_idx = 0
muscle_idx = 0
spinal_idx = 0

for comp in components:
    if comp['category'] == 'vertebra':
        color = vertebra_colors[vertebra_idx % len(vertebra_colors)]
        vertebra_idx += 1
    elif comp['category'] == 'spinal_cord':
        color = spinal_cord_colors[spinal_idx % len(spinal_cord_colors)]
        spinal_idx += 1
    else:  # muscle
        color = muscle_colors[muscle_idx % len(muscle_colors)]
        muscle_idx += 1
    
    actor = plotter.add_mesh(
        comp['mesh'],
        color=color,
        smooth_shading=True,
        specular=0.5,
        specular_power=30,
        ambient=0.4,
        diffuse=0.8,
        show_edges=False
    )
    
    actors.append(actor)
    comp['actor'] = actor
    
    if comp['category'] == 'vertebra':
        print(f"  Added vertebra #{comp['number']}: {comp['name']}")
    else:
        print(f"  Added {comp['category']}: {comp['name']}")

# Add labels for vertebrae
print("\nAdding vertebra labels...")
for vert in vertebrae:
    center = vert['mesh'].center
    plotter.add_point_labels(
        [center],
        [f"V{vert['number']}"],
        font_size=20,
        point_size=1,
        text_color='yellow',
        shape_opacity=0.5,
        always_visible=False
    )

# Calculate scene bounds
all_points = np.vstack([c['mesh'].points for c in components])
bounds = [
    all_points[:, 0].min(), all_points[:, 0].max(),
    all_points[:, 1].min(), all_points[:, 1].max(),
    all_points[:, 2].min(), all_points[:, 2].max()
]
center = [(bounds[i] + bounds[i+1]) / 2 for i in [0, 2, 4]]

print(f"\nBounds: X=[{bounds[0]:.1f}, {bounds[1]:.1f}]")
print(f"        Y=[{bounds[2]:.1f}, {bounds[3]:.1f}]")
print(f"        Z=[{bounds[4]:.1f}, {bounds[5]:.1f}]")

# ============================================================================
# CLIPPING SYSTEM
# ============================================================================

clip_state = {
    'x': None, 'y': None, 'z': None,
    'x_on': False, 'y_on': False, 'z_on': False
}

def apply_clips():
    """Apply active clipping planes to all actors"""
    for actor in actors:
        actor.mapper.RemoveAllClippingPlanes()
        if clip_state['x_on'] and clip_state['x']:
            actor.mapper.AddClippingPlane(clip_state['x'])
        if clip_state['y_on'] and clip_state['y']:
            actor.mapper.AddClippingPlane(clip_state['y'])
        if clip_state['z_on'] and clip_state['z']:
            actor.mapper.AddClippingPlane(clip_state['z'])

def cb_x(normal, origin):
    """Callback for X plane widget"""
    plane = vtk.vtkPlane()
    plane.SetNormal(1, 0, 0)
    plane.SetOrigin(origin)
    clip_state['x'] = plane
    apply_clips()

def cb_y(normal, origin):
    """Callback for Y plane widget"""
    plane = vtk.vtkPlane()
    plane.SetNormal(0, 1, 0)
    plane.SetOrigin(origin)
    clip_state['y'] = plane
    apply_clips()

def cb_z(normal, origin):
    """Callback for Z plane widget"""
    plane = vtk.vtkPlane()
    plane.SetNormal(0, 0, 1)
    plane.SetOrigin(origin)
    clip_state['z'] = plane
    apply_clips()

# Add plane widgets (start disabled)
try:
    wx = plotter.add_plane_widget(
        callback=cb_x,
        bounds=bounds,
        normal=(1, 0, 0),
        origin=center
    )
    wy = plotter.add_plane_widget(
        callback=cb_y,
        bounds=bounds,
        normal=(0, 1, 0),
        origin=center
    )
    wz = plotter.add_plane_widget(
        callback=cb_z,
        bounds=bounds,
        normal=(0, 0, 1),
        origin=center
    )
    
    wx.SetEnabled(0)
    wy.SetEnabled(0)
    wz.SetEnabled(0)
    
    print("\n✅ Clipping widgets initialized")
except Exception as e:
    print(f"\n⚠ Plane widgets error: {e}")
    wx = wy = wz = None

# Keyboard controls for clipping
def toggle_x():
    if wx is None:
        return
    clip_state['x_on'] = not clip_state['x_on']
    wx.SetEnabled(1 if clip_state['x_on'] else 0)
    status = 'ON' if clip_state['x_on'] else 'OFF'
    print(f"🔴 Sagittal clipping (X): {status}")
    if clip_state['x_on']:
        cb_x(wx.GetNormal(), wx.GetOrigin())
    else:
        apply_clips()

def toggle_y():
    if wy is None:
        return
    clip_state['y_on'] = not clip_state['y_on']
    wy.SetEnabled(1 if clip_state['y_on'] else 0)
    status = 'ON' if clip_state['y_on'] else 'OFF'
    print(f"🟢 Coronal clipping (Y): {status}")
    if clip_state['y_on']:
        cb_y(wy.GetNormal(), wy.GetOrigin())
    else:
        apply_clips()

def toggle_z():
    if wz is None:
        return
    clip_state['z_on'] = not clip_state['z_on']
    wz.SetEnabled(1 if clip_state['z_on'] else 0)
    status = 'ON' if clip_state['z_on'] else 'OFF'
    print(f"🔵 Axial clipping (Z): {status}")
    if clip_state['z_on']:
        cb_z(wz.GetNormal(), wz.GetOrigin())
    else:
        apply_clips()

def clear_all():
    if wx is None:
        return
    clip_state.update({'x_on': False, 'y_on': False, 'z_on': False})
    wx.SetEnabled(0)
    wy.SetEnabled(0)
    wz.SetEnabled(0)
    for actor in actors:
        actor.mapper.RemoveAllClippingPlanes()
    print("🧹 All clipping cleared")

plotter.add_key_event('x', toggle_x)
plotter.add_key_event('y', toggle_y)
plotter.add_key_event('z', toggle_z)
plotter.add_key_event('c', clear_all)

# ============================================================================
# VISIBILITY CONTROLS
# ============================================================================

visibility_state = {'muscles': True, 'vertebrae': True, 'spinal_cord': True}

def toggle_muscles():
    """Toggle muscles visibility"""
    visibility_state['muscles'] = not visibility_state['muscles']
    status = 'ON' if visibility_state['muscles'] else 'OFF'
    print(f"💪 Muscles visibility: {status}")
    
    for comp in components:
        if comp['category'] == 'muscle':
            comp['actor'].SetVisibility(visibility_state['muscles'])
    plotter.render()

def toggle_vertebrae():
    """Toggle vertebrae visibility"""
    visibility_state['vertebrae'] = not visibility_state['vertebrae']
    status = 'ON' if visibility_state['vertebrae'] else 'OFF'
    print(f"🦴 Vertebrae visibility: {status}")
    
    for comp in components:
        if comp['category'] == 'vertebra':
            comp['actor'].SetVisibility(visibility_state['vertebrae'])
    plotter.render()

def toggle_spinal_cord():
    """Toggle spinal cord visibility"""
    visibility_state['spinal_cord'] = not visibility_state['spinal_cord']
    status = 'ON' if visibility_state['spinal_cord'] else 'OFF'
    print(f"🧠 Spinal cord visibility: {status}")
    
    for comp in components:
        if comp['category'] == 'spinal_cord':
            comp['actor'].SetVisibility(visibility_state['spinal_cord'])
    plotter.render()

plotter.add_key_event('m', toggle_muscles)
plotter.add_key_event('v', toggle_vertebrae)
plotter.add_key_event('t', toggle_spinal_cord)

# ============================================================================
# FOCUS NAVIGATION - FOCUS ON VERTEBRAE BY NUMBER
# ============================================================================

current_focus = None
transparency_level = 2  # Default transparency level (1=light, 2=medium, 3=high, 4=hide)

def focus_on_vertebra_number(vert_num):
    """Focus on specific vertebra by its number"""
    global current_focus
    
    found = None
    for vert in vertebrae:
        if vert['number'] == vert_num:
            found = vert
            break
    
    if not found:
        print(f"⚠ Vertebra #{vert_num} not found!")
        return
    
    current_focus = vert_num
    print(f"🎯 Focus on VERTEBRA #{vert_num}: {found['name']}")
    
    # Apply transparency based on current level
    apply_transparency_level()
    
    # Move camera to vertebra
    mesh_center = found['mesh'].center
    plotter.camera_position = [
        (mesh_center[0] + 150, mesh_center[1] + 150, mesh_center[2] + 150),
        tuple(mesh_center),
        (0, 0, 1)
    ]
    plotter.camera.zoom(2.5)
    plotter.render()

def apply_transparency_level():
    """Apply current transparency level to all objects"""
    global current_focus, transparency_level
    
    if current_focus is None:
        return
    
    # Define opacity levels for different transparency settings
    opacity_levels = {
        1: 0.5,   # Light transparency
        2: 0.25,  # Medium transparency
        3: 0.1,   # High transparency
        4: 0.0    # Hidden
    }
    
    other_opacity = opacity_levels.get(transparency_level, 0.25)
    
    for comp in components:
        if comp['category'] == 'vertebra' and comp.get('number') == current_focus:
            comp['actor'].prop.opacity = 1.0
            comp['actor'].prop.color = (1.0, 0.85, 0.2)  # Bright yellow
            comp['actor'].SetVisibility(True)
        else:
            comp['actor'].prop.opacity = other_opacity
            if transparency_level == 4:
                comp['actor'].SetVisibility(False)
            else:
                comp['actor'].SetVisibility(True)
    
    plotter.render()

def increase_transparency():
    """Increase transparency of non-focused parts"""
    global transparency_level
    if current_focus is None:
        print("⚠ Focus on a vertebra first (use numbers or Page Up/Down)")
        return
    
    transparency_level = min(4, transparency_level + 1)
    level_names = {1: "Light", 2: "Medium", 3: "High", 4: "Hidden"}
    print(f"👁 Transparency level: {level_names[transparency_level]}")
    apply_transparency_level()

def decrease_transparency():
    """Decrease transparency of non-focused parts"""
    global transparency_level
    if current_focus is None:
        print("⚠ Focus on a vertebra first (use numbers or Page Up/Down)")
        return
    
    transparency_level = max(1, transparency_level - 1)
    level_names = {1: "Light", 2: "Medium", 3: "High", 4: "Hidden"}
    print(f"👁 Transparency level: {level_names[transparency_level]}")
    apply_transparency_level()

def reset_focus():
    """Reset to show all objects"""
    global current_focus, transparency_level
    current_focus = None
    transparency_level = 2  # Reset to medium
    print("🔄 Reset focus - showing all objects")
    
    vertebra_idx = 0
    muscle_idx = 0
    spinal_idx = 0
    
    for comp in components:
        comp['actor'].prop.opacity = 1.0
        comp['actor'].SetVisibility(True)
        if comp['category'] == 'vertebra':
            comp['actor'].prop.color = vertebra_colors[vertebra_idx % len(vertebra_colors)]
            vertebra_idx += 1
        elif comp['category'] == 'spinal_cord':
            comp['actor'].prop.color = spinal_cord_colors[spinal_idx % len(spinal_cord_colors)]
            spinal_idx += 1
        else:
            comp['actor'].prop.color = muscle_colors[muscle_idx % len(muscle_colors)]
            muscle_idx += 1
    
    plotter.reset_camera()
    plotter.camera.zoom(1.3)
    plotter.render()

plotter.add_key_event('r', reset_focus)

# Add transparency controls
plotter.add_key_event('plus', increase_transparency)
plotter.add_key_event('equal', increase_transparency)  # For keyboards without numpad
plotter.add_key_event('minus', decrease_transparency)

# Bind number keys 1-9 to vertebrae
def make_focus_callback(vertebra_num):
    """Create a callback function for a specific vertebra number"""
    def callback():
        focus_on_vertebra_number(vertebra_num)
    return callback

for i in range(1, min(10, len(vertebrae) + 1)):
    plotter.add_key_event(str(i), make_focus_callback(i))

# Navigation with Page Up/Down
def next_vertebra():
    """Focus on next vertebra"""
    global current_focus
    if current_focus is None:
        focus_on_vertebra_number(1)
    else:
        next_num = current_focus + 1
        if next_num <= len(vertebrae):
            focus_on_vertebra_number(next_num)
        else:
            print(f"⚠ Already at last vertebra #{len(vertebrae)}")

def prev_vertebra():
    """Focus on previous vertebra"""
    global current_focus
    if current_focus is None:
        focus_on_vertebra_number(len(vertebrae))
    else:
        prev_num = current_focus - 1
        if prev_num >= 1:
            focus_on_vertebra_number(prev_num)
        else:
            print(f"⚠ Already at first vertebra #1")

plotter.add_key_event('Next', next_vertebra)  # Page Down
plotter.add_key_event('Prior', prev_vertebra)  # Page Up

# ============================================================================
# CAMERA AND UI
# ============================================================================

# Set initial camera
plotter.camera_position = 'iso'
plotter.reset_camera()
plotter.camera.zoom(1.3)

# Add axes and grid
plotter.add_axes(line_width=3, labels_off=False)
plotter.show_grid(color='gray')

# Instructions text
instructions = """CONTROLS:
[X] Sagittal plane
[Y] Coronal plane
[Z] Axial plane
[C] Clear clipping
[M] Toggle muscles
[V] Toggle vertebrae
[T] Toggle spinal cord
[R] Reset focus
[1-9] Focus vertebra #
[PgUp/PgDn] Next/Prev
[+/-] Transparency"""

plotter.add_text(
    instructions,
    position='upper_left',
    font_size=11,
    color='white',
    font='courier'
)

info_text = f"{len(vertebrae)} Vertebrae | {len(spinal_cord)} Spinal Cord | {len(muscles)} Muscles"
plotter.add_text(
    info_text,
    position='upper_right',
    font_size=12,
    color='yellow'
)

# Print vertebrae list
print("\n" + "="*70)
print("VERTEBRAE LIST:")
for vert in vertebrae:
    print(f"  Vertebra #{vert['number']:2d} - {vert['name']}")
print("="*70)

# Print controls
print("\nKEYBOARD CONTROLS:")
print("  [X] = Sagittal clipping (Left/Right)")
print("  [Y] = Coronal clipping (Front/Back)")
print("  [Z] = Axial clipping (Top/Bottom)")
print("  [C] = Clear all clipping")
print("  [M] = Toggle muscles visibility")
print("  [V] = Toggle vertebrae visibility")
print("  [T] = Toggle spinal cord visibility")
print("  [R] = Reset focus")
print("  [1-9] = Focus on vertebra by number")
print("  [Page Up] = Previous vertebra")
print("  [Page Down] = Next vertebra")
print("  [+] = Increase transparency (hide outer parts)")
print("  [-] = Decrease transparency (show outer parts)")
print("="*70)
print("MOUSE CONTROLS:")
print("  Left-drag = Rotate")
print("  Right-drag = Pan")
print("  Scroll = Zoom")
print("="*70)
print("\n🎨 Opening visualization window...")
print("="*70)

# Show the window
plotter.show()

print("\n✅ Visualization closed. Done!")