import pyvista as pv
import numpy as np
from pathlib import Path

class Heart3DClippingViewer:
    def __init__(self, heart_parts_folder="heart parts"):
        """
        Initialize the 3D Heart Viewer with anatomical colors from individual parts
        
        Args:
            heart_parts_folder: Path to folder containing individual heart part OBJ files
        """
        self.plotter = None
        self.heart_parts_folder = Path(heart_parts_folder)
        self.heart_parts = {}
        self.combined_mesh = None
        
        # Clipping plane positions (in world coordinates)
        self.x_clip = None
        self.y_clip = None
        self.z_clip = None
        self.bounds = None
        
        # Anatomical color scheme matching the reference image
        self.color_scheme = {
            'left': [0.85, 0.25, 0.25],           # Bright red - Left side/Oxygenated
            'right': [0.50, 0.55, 0.85],          # Blue - Right side/Deoxygenated
            'muscle': [0.65, 0.18, 0.15],         # Dark red - Heart muscle
            'valves': [0.95, 0.95, 0.85],         # Cream/white - Valves
        }
        
    def load_heart_parts(self):
        """Load all heart part OBJ files from the folder"""
        if not self.heart_parts_folder.exists():
            print(f"Warning: Folder '{self.heart_parts_folder}' not found!")
            print("Creating synthetic heart instead...")
            return False
        
        obj_files = list(self.heart_parts_folder.glob("*.obj"))
        
        if not obj_files:
            print(f"No OBJ files found in '{self.heart_parts_folder}'")
            return False
        
        print(f"\nLoading {len(obj_files)} heart parts...")
        
        for obj_file in obj_files:
            try:
                mesh = pv.read(str(obj_file))
                part_name = obj_file.stem
                self.heart_parts[part_name] = mesh
                print(f"  ✓ Loaded: {part_name}")
            except Exception as e:
                print(f"  ✗ Error loading {obj_file.name}: {e}")
        
        if not self.heart_parts:
            return False
        
        print(f"\n✓ Successfully loaded {len(self.heart_parts)} heart parts")
        return True
    
    def assign_anatomical_colors(self, mesh, part_name):
        """Assign anatomical colors based on part name and position"""
        part_lower = part_name.lower()
        
        # Determine color based on anatomical keywords
        if 'valve' in part_lower or 'valv' in part_lower:
            color = self.color_scheme['valves']
        elif any(keyword in part_lower for keyword in ['left', 'lv', 'la', 'mitral', 'aortic', 'aorta']):
            color = self.color_scheme['left']
        elif any(keyword in part_lower for keyword in ['right', 'rv', 'ra', 'tricuspid', 'pulmonary', 'vena', 'cava']):
            color = self.color_scheme['right']
        else:
            # Default to heart muscle color
            color = self.color_scheme['muscle']
        
        return color
    
    def combine_heart_parts(self):
        """Combine all heart parts into a single mesh with anatomical coloring"""
        if not self.heart_parts:
            print("No heart parts loaded, creating synthetic heart...")
            return self.create_synthetic_heart()
        
        print("\nCombining heart parts with anatomical colors...")
        
        all_meshes = []
        
        for part_name, mesh in self.heart_parts.items():
            # Assign color to this part
            color = self.assign_anatomical_colors(mesh, part_name)
            
            # Add RGB color to each point
            colors = np.tile(color, (mesh.n_points, 1))
            mesh['colors'] = colors
            
            all_meshes.append(mesh)
        
        # Merge all parts
        combined = all_meshes[0]
        for mesh in all_meshes[1:]:
            combined = combined.merge(mesh)
        
        print(f"✓ Combined mesh: {combined.n_points} points, {combined.n_cells} cells")
        return combined
    
    def create_synthetic_heart(self):
        """Create a synthetic heart with anatomical regions (fallback)"""
        print("Creating synthetic heart with anatomical coloring...")
        
        dims = (80, 80, 100)
        origin = (-40, -40, -50)
        spacing = (1.0, 1.0, 1.0)
        
        x = np.linspace(origin[0], origin[0] + dims[0] * spacing[0], dims[0])
        y = np.linspace(origin[1], origin[1] + dims[1] * spacing[1], dims[1])
        z = np.linspace(origin[2], origin[2] + dims[2] * spacing[2], dims[2])
        
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Create heart shape
        values = np.exp(-((X/22)**2 + (Y/18)**2 + ((Z-5)/28)**2) * 2) * 200
        values += np.random.normal(0, 5, values.shape)
        values = np.clip(values, 0, 255).astype(np.float32)
        
        volume = pv.ImageData(dimensions=dims, spacing=spacing, origin=origin)
        volume['values'] = values.flatten(order='F')
        
        # Extract surface
        surface = volume.contour([100])
        
        # Add anatomical colors based on position
        points = surface.points
        center_x = (points[:, 0].min() + points[:, 0].max()) / 2
        
        colors = np.zeros((surface.n_points, 3))
        # Left side (red)
        left_mask = points[:, 0] > center_x
        colors[left_mask] = self.color_scheme['left']
        # Right side (blue)
        colors[~left_mask] = self.color_scheme['right']
        
        surface['colors'] = colors
        return surface
    
    def update_visualization(self):
        """Update the visualization with current clipping settings"""
        if self.combined_mesh is None or self.plotter is None:
            return
        
        # Remove old actors
        self.plotter.remove_actor('heart_surface')
        self.plotter.remove_actor('x_plane')
        self.plotter.remove_actor('y_plane')
        self.plotter.remove_actor('z_plane')
        
        # Start with full mesh
        clipped = self.combined_mesh.copy()
        
        # Apply X-axis clipping (Sagittal - left/right)
        if self.x_clip is not None:
            clipped = clipped.clip(normal=[1, 0, 0], origin=[self.x_clip, 0, 0])
            plane = pv.Plane(
                center=[self.x_clip, (self.bounds[2]+self.bounds[3])/2, (self.bounds[4]+self.bounds[5])/2],
                direction=[1, 0, 0],
                i_size=abs(self.bounds[3]-self.bounds[2])*1.2,
                j_size=abs(self.bounds[5]-self.bounds[4])*1.2
            )
            self.plotter.add_mesh(plane, color='red', opacity=0.15, name='x_plane')
        
        # Apply Y-axis clipping (Coronal - front/back)
        if self.y_clip is not None:
            clipped = clipped.clip(normal=[0, 1, 0], origin=[0, self.y_clip, 0])
            plane = pv.Plane(
                center=[(self.bounds[0]+self.bounds[1])/2, self.y_clip, (self.bounds[4]+self.bounds[5])/2],
                direction=[0, 1, 0],
                i_size=abs(self.bounds[1]-self.bounds[0])*1.2,
                j_size=abs(self.bounds[5]-self.bounds[4])*1.2
            )
            self.plotter.add_mesh(plane, color='green', opacity=0.15, name='y_plane')
        
        # Apply Z-axis clipping (Axial - top/bottom)
        if self.z_clip is not None:
            clipped = clipped.clip(normal=[0, 0, 1], origin=[0, 0, self.z_clip])
            plane = pv.Plane(
                center=[(self.bounds[0]+self.bounds[1])/2, (self.bounds[2]+self.bounds[3])/2, self.z_clip],
                direction=[0, 0, 1],
                i_size=abs(self.bounds[1]-self.bounds[0])*1.2,
                j_size=abs(self.bounds[3]-self.bounds[2])*1.2
            )
            self.plotter.add_mesh(plane, color='blue', opacity=0.15, name='z_plane')
        
        # Add the clipped mesh with anatomical colors
        if 'colors' in clipped.array_names and clipped.n_points > 0:
            self.plotter.add_mesh(
                clipped,
                scalars='colors',
                rgb=True,
                smooth_shading=True,
                lighting=True,
                specular=0.6,
                specular_power=20,
                name='heart_surface'
            )
        else:
            self.plotter.add_mesh(
                clipped,
                color=self.color_scheme['muscle'],
                smooth_shading=True,
                lighting=True,
                specular=0.6,
                specular_power=20,
                name='heart_surface'
            )
    
    def add_controls(self):
        """Add interactive slider controls for clipping planes"""
        
        def update_x_clip(value):
            x_world = self.bounds[0] + (self.bounds[1] - self.bounds[0]) * value
            self.x_clip = x_world if value < 0.99 else None
            self.update_visualization()
        
        def update_y_clip(value):
            y_world = self.bounds[2] + (self.bounds[3] - self.bounds[2]) * value
            self.y_clip = y_world if value < 0.99 else None
            self.update_visualization()
        
        def update_z_clip(value):
            z_world = self.bounds[4] + (self.bounds[5] - self.bounds[4]) * value
            self.z_clip = z_world if value < 0.99 else None
            self.update_visualization()
        
        # X-axis slider (Red - Sagittal)
        self.plotter.add_slider_widget(
            update_x_clip,
            [0, 1],
            value=1.0,
            title="X-Axis (Left/Right)",
            pointa=(0.02, 0.9),
            pointb=(0.35, 0.9),
            style='modern',
            color='red'
        )
        
        # Y-axis slider (Green - Coronal)
        self.plotter.add_slider_widget(
            update_y_clip,
            [0, 1],
            value=1.0,
            title="Y-Axis (Front/Back)",
            pointa=(0.02, 0.82),
            pointb=(0.35, 0.82),
            style='modern',
            color='green'
        )
        
        # Z-axis slider (Blue - Axial)
        self.plotter.add_slider_widget(
            update_z_clip,
            [0, 1],
            value=1.0,
            title="Z-Axis (Top/Bottom)",
            pointa=(0.02, 0.74),
            pointb=(0.35, 0.74),
            style='modern',
            color='blue'
        )
    
    def show(self):
        """Display the viewer with GUI controls"""
        print("="*70)
        print("🫀 Heart 3D Clipping Viewer - Loading data...")
        print("="*70)
        
        # Load heart parts
        if not self.load_heart_parts():
            print("Using synthetic heart data...")
        
        # Combine all parts with anatomical colors
        self.combined_mesh = self.combine_heart_parts()
        
        if self.combined_mesh is None:
            print("ERROR: Failed to create heart mesh!")
            return
        
        # Get bounds
        self.bounds = self.combined_mesh.bounds
        print(f"\nHeart bounds: {self.bounds}")
        
        # Create plotter
        self.plotter = pv.Plotter(window_size=[1600, 1000])
        self.plotter.set_background('black')
        
        # Add initial mesh
        if 'colors' in self.combined_mesh.array_names:
            self.plotter.add_mesh(
                self.combined_mesh,
                scalars='colors',
                rgb=True,
                smooth_shading=True,
                lighting=True,
                specular=0.6,
                specular_power=20,
                name='heart_surface'
            )
        else:
            self.plotter.add_mesh(
                self.combined_mesh,
                color=self.color_scheme['muscle'],
                smooth_shading=True,
                lighting=True,
                specular=0.6,
                specular_power=20,
                name='heart_surface'
            )
        
        # Add controls
        self.add_controls()
        
        # Add axes
        self.plotter.add_axes(interactive=True, color='white')
        
        # Add title
        title = "🫀 Heart 3D Anatomical Navigator\n"
        title += "Move sliders LEFT to cut through the heart"
        self.plotter.add_text(title, position='upper_left', font_size=12, color='white')
        
        # Add color legend
        legend = "🎨 Color Legend:\n"
        legend += "🔴 Red: Left side / Oxygenated\n"
        legend += "🔵 Blue: Right side / Deoxygenated\n"
        legend += "🟡 Cream: Valves\n"
        legend += "🟤 Dark Red: Heart muscle\n\n"
        legend += "🖱 CONTROLS:\n"
        legend += "Left Drag: Rotate\n"
        legend += "Scroll: Zoom\n"
        legend += "Middle Drag: Pan\n"
        legend += "🔴 Red: X-Cut\n"
        legend += "🟢 Green: Y-Cut\n"
        legend += "🔵 Blue: Z-Cut"
        self.plotter.add_text(legend, position='lower_right', font_size=9, color='lightgray')
        
        # Set initial camera
        self.plotter.camera_position = 'iso'
        self.plotter.camera.zoom(1.2)
        
        print("\n" + "="*70)
        print("✓ Viewer ready with anatomical colors!")
        print("  🔴 Red: Left side (oxygenated blood)")
        print("  🔵 Blue: Right side (deoxygenated blood)")
        print("  🟡 Cream: Valves")
        print("  🟤 Dark red: Heart muscle")
        print("="*70)
        
        # Show the viewer
        self.plotter.show()


def main():
    """Main function to run the viewer"""
    
    print("\n" + "="*70)
    print("🫀 Heart 3D Anatomical Navigator with Clipping Planes")
    print("="*70 + "\n")
    
    # Use heart parts folder
    viewer = Heart3DClippingViewer(heart_parts_folder="heart parts")
    viewer.show()
    
    print("\n✓ Viewer closed. Goodbye!")


if __name__ == "__main__":
    main()