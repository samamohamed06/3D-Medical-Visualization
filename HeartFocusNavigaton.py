import pyvista as pv
import vtk
import os
from pathlib import Path

class Heart3DFocusNavigator:
    """3D Heart viewer with focus navigation and anatomical coloring"""
    
    def __init__(self, heart_parts_folder="heart parts"):
        self.heart_parts_folder = heart_parts_folder
        self.plotter = None
        self.actors = {}
        self.meshes = {}
        self.current_focus = None
        
        # Anatomical color scheme (RGB values 0-1)
        self.anatomical_colors = {
            # Arteries - Red/Pink (oxygenated blood)
            'aorta': [0.9, 0.2, 0.2],
            'pulmonary_artery': [0.7, 0.3, 0.3],
            'artery': [0.85, 0.25, 0.25],
            
            # Veins - Blue (deoxygenated blood)
            'vena_cava': [0.3, 0.3, 0.8],
            'pulmonary_vein': [0.8, 0.4, 0.4],
            'vein': [0.4, 0.4, 0.75],
            
            # Left side (oxygenated) - Red tones
            'left_ventricle': [0.8, 0.3, 0.3],
            'left_atrium': [0.9, 0.4, 0.4],
            
            # Right side (deoxygenated) - Blue tones
            'right_ventricle': [0.4, 0.4, 0.7],
            'right_atrium': [0.5, 0.5, 0.8],
            
            # Valves - White/Cream
            'valve': [0.95, 0.95, 0.85],
            'mitral': [0.95, 0.95, 0.85],
            'tricuspid': [0.95, 0.95, 0.85],
            'aortic': [0.95, 0.95, 0.85],
            'pulmonary': [0.95, 0.95, 0.85],
            
            # Myocardium - Reddish brown
            'myocardium': [0.7, 0.25, 0.25],
            'septum': [0.75, 0.3, 0.3],
            
            # Default
            'default': [0.8, 0.6, 0.6]
        }
    
    def get_anatomical_color(self, part_name):
        """Get anatomical color for a heart part based on its name"""
        part_lower = part_name.lower()
        
        # Check for specific matches
        for key, color in self.anatomical_colors.items():
            if key in part_lower:
                return color
        
        # Default color
        return self.anatomical_colors['default']
    
    def load_heart_parts(self):
        """Load all heart parts from the folder"""
        parts_path = Path(self.heart_parts_folder)
        
        if not parts_path.exists():
            print(f"Error: '{self.heart_parts_folder}' folder not found!")
            return {}
        
        loaded_parts = {}
        
        # Load all OBJ, STL, or VTK files
        for file in parts_path.glob('*'):
            if file.suffix.lower() in ['.obj', '.stl', '.vtk', '.ply']:
                try:
                    mesh = pv.read(str(file))
                    part_name = file.stem
                    loaded_parts[part_name] = mesh
                    print(f"Loaded: {part_name}")
                except Exception as e:
                    print(f"Failed to load {file.name}: {e}")
        
        return loaded_parts
    
    def focus_on_part(self, part_name):
        """Focus on a specific heart part, making others transparent"""
        if part_name not in self.actors:
            print(f"Part '{part_name}' not found!")
            return
        
        self.current_focus = part_name
        
        # Update all actors
        for name, actor in self.actors.items():
            if name == part_name:
                # Focused part: full opacity, highlighted
                actor.GetProperty().SetOpacity(1.0)
                actor.GetProperty().SetEdgeVisibility(True)
                actor.GetProperty().SetEdgeColor(1, 1, 1)
                actor.GetProperty().SetLineWidth(2)
            else:
                # Other parts: transparent
                actor.GetProperty().SetOpacity(0.15)
                actor.GetProperty().SetEdgeVisibility(False)
        
        # Camera focus on the selected part
        if part_name in self.meshes:
            bounds = self.meshes[part_name].bounds
            center = self.meshes[part_name].center
            self.plotter.camera.focal_point = center
            
        self.plotter.render()
        print(f"Focused on: {part_name}")
    
    def show_all_parts(self):
        """Show all parts with full opacity"""
        self.current_focus = None
        
        for actor in self.actors.values():
            actor.GetProperty().SetOpacity(1.0)
            actor.GetProperty().SetEdgeVisibility(False)
        
        self.plotter.reset_camera()
        self.plotter.render()
        print("Showing all parts")
    
    def create_viewer(self):
        """Create the interactive 3D viewer"""
        # Load heart parts
        self.meshes = self.load_heart_parts()
        
        if not self.meshes:
            print("No heart parts loaded. Please check the 'heart parts' folder.")
            return
        
        # Create plotter with custom settings
        self.plotter = pv.Plotter(window_size=[1200, 800])
        self.plotter.set_background('black')
        
        # Add each part with anatomical coloring
        for name, mesh in self.meshes.items():
            color = self.get_anatomical_color(name)
            actor = self.plotter.add_mesh(
                mesh,
                color=color,
                opacity=1.0,
                smooth_shading=True,
                show_edges=False,
                name=name
            )
            self.actors[name] = actor
        
        # Prioritize main parts for number keys - with multiple search terms
        priority_parts = [
            ['aorta'],
            ['vena_cava', 'vena cava', 'superior vena', 'inferior vena'],
            ['left_atrium', 'left atrium', 'atrium left'],
            ['right_atrium', 'right atrium', 'atrium right'],
            ['left_ventricle', 'left ventricle', 'ventricle left'],
            ['right_ventricle', 'right ventricle', 'ventricle right']
        ]
        
        # Sort parts: priority parts first, then others alphabetically
        part_names = []
        remaining_parts = []
        
        # Find priority parts
        for search_terms in priority_parts:
            for name in self.meshes.keys():
                name_lower = name.lower()
                if any(term in name_lower for term in search_terms) and name not in part_names:
                    part_names.append(name)
                    break
        
        # Add remaining parts
        for name in sorted(self.meshes.keys()):
            if name not in part_names:
                remaining_parts.append(name)
        
        part_names.extend(remaining_parts)
        
        # Add text instructions
        instructions = [
            "Heart 3D Focus Navigator",
            "─" * 50,
            "Press number keys to focus on parts:",
        ]
        
        # Add all parts with their numbers
        for i, name in enumerate(part_names):
            if i < 9:  # Keys 1-9
                instructions.append(f"  {i+1}. {name}")
            elif i == 9:  # Show there are more parts
                instructions.append(f"  ... and {len(part_names) - 9} more parts")
                break
        
        instructions.extend([
            "",
            "Controls:",
            "  0: Show all parts",
            "  1-9: Focus on specific part",
            "  r: Reset camera",
            "  q: Quit",
            "  Mouse: Rotate/Pan/Zoom"
        ])
        
        self.plotter.add_text(
            "\n".join(instructions),
            position='upper_left',
            font_size=10,
            color='white'
        )
        
        # Add legend for colors
        legend_text = (
            "Color Legend:\n"
            "Red: Oxygenated (Arteries/Left)\n"
            "Blue: Deoxygenated (Veins/Right)\n"
            "Cream: Valves"
        )
        self.plotter.add_text(
            legend_text,
            position='lower_right',
            font_size=9,
            color='lightgray'
        )
        
        # Setup key bindings for all parts
        self.plotter.add_key_event('0', lambda: self.show_all_parts())
        
        # Bind keys 1-9 to the first 9 parts
        for i, name in enumerate(part_names[:9]):
            key = str(i + 1)
            self.plotter.add_key_event(
                key, 
                lambda n=name: self.focus_on_part(n)
            )
        
        # Print all parts mapping to console
        print("\n" + "="*60)
        print("Part Number Mapping:")
        print("="*60)
        for i, name in enumerate(part_names):
            if i < 9:
                print(f"  {i+1}. {name}")
            else:
                print(f"  (Additional parts not bound to keys: {name})")
        print("="*60 + "\n")
        
        # Show the viewer
        self.plotter.show()


def main():
    """Main function to run the heart viewer"""
    print("\n" + "="*60)
    print("3D Heart Anatomical Focus Navigator")
    print("="*60)
    
    # You can specify a different folder path here
    heart_parts_folder = "heart parts"
    
    viewer = Heart3DFocusNavigator(heart_parts_folder)
    viewer.create_viewer()


if __name__ == "__main__":
    main()