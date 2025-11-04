🧠 3D Medical Visualization System
📖 Overview

The 3D Medical Visualization System is an interactive GUI-based application built in Python for exploring and visualizing anatomical systems in 3D.
It allows users to navigate and visualize various human body systems using advanced 3D rendering and navigation techniques.

💡 Features
🧩 Available Anatomical Systems

The application currently supports 4 main anatomical systems, each with interactive visualization and navigation features:

System	Visualization Methods	Navigation Methods
🧠 Nervous System	Surface Rendering, Clipping Plans, Curved MPR	Focus Navigation, Moving Stuff Illustration, Fly-through Navigation
❤️ Cardiovascular System	Surface Rendering, Clipping Plans, Curved MPR	Focus Navigation, Moving Stuff Illustration, Fly-through Navigation
💪 Musculoskeletal System	Surface Rendering, Clipping Plans, Curved MPR	Focus Navigation, Moving Stuff Illustration, Fly-through Navigation
🦷 Mouth/Dental System	Surface Rendering, Clipping Plans, Curved MPR	Focus Navigation, Moving Stuff Illustration, Fly-through Navigation
🧱 System Structure

Each system’s features are implemented as individual Python modules.
Below is the structure used in VS Code:

Task 3/
│
├── main_gui.py
│
├── braindataset/
│   ├── BrainSurfaceRendering.py
│   ├── BrainClippingPlans.py
│   ├── BrainCurvedMPR.py
│   ├── BrainFocusNavigation.py
│   ├── BrainMovingStuffIllustration.py
│   └── BrainFlyThrough.py
│
├── heart parts/
│   ├── HeartSurfaceRendering.py
│   ├── HeartClippingPlans.py
│   ├── HeartCurvedMPR.py
│   ├── HeartFocusNavigation.py
│   ├── HeartMovingStuffIllustration.py
│   └── HeartFlyThrough.py
│
├── muscledataset/
│   ├── MuscleSurfaceRendering.py
│   ├── MuscleClippingPlans.py
│   ├── MuscleCurvedMPR.py
│   ├── MuscleFocusNavigation.py
│   ├── MuscleMovingStuffIllustration.py
│   └── MuscleFlyThrough.py
│
├── dentaldataset/
│   ├── DentalSurfaceRendering.py
│   ├── DentalClippingPlans.py
│   ├── DentalCurvedMPR.py
│   ├── DentalFocusNavigation.py
│   ├── DentalMovingStuffIllustration.py
│   └── DentalFlyThrough.py
│
├── brain.nii
├── heart.nii
├── muscle.nii
├── dental.nii
└── README.md

⚙️ How It Works
🖥️ GUI Overview

Built with PyQt5.

The main window allows selecting one of the 4 anatomical systems.

Each system leads to a feature selection window divided into:

Visualization Methods (3 options)

Navigation Methods (3 options)

🔍 Code Logic

The main file (main_gui.py) dynamically maps all .py modules to their corresponding system.

Each feature file (e.g., BrainSurfaceRendering.py) opens a specific 3D visualization or navigation module.

3D data files (.nii, .obj) are loaded for real medical data visualization.

🚀 How to Run
1️⃣ Install Dependencies

Make sure you have Python 3.10+ and install the required libraries:

pip install PyQt5 vtk nibabel

2️⃣ Run the Application
python main_gui.py

3️⃣ Explore the Systems

Select an anatomical system from the main menu.

📂 File Handling

Each .py feature script corresponds to one visualization or navigation method.
The logic for detecting and mapping these files is handled by:

if 'heart' in file_lower:
    mapping['Cardiovascular System'].append(file)
elif 'brain' in file_lower:
    mapping['Nervous System'].append(file)
elif 'bone' in file_lower or 'skeleton' in file_lower or 'muscle' in file_lower:
    mapping['Musculoskeletal System'].append(file)
elif 'tooth' in file_lower or 'dental' in file_lower or 'mouth' in file_lower:
    mapping['Mouth/Dental System'].append(file)

🧩 Technologies Used

Python 3.10

PyQt5 – GUI framework

VTK (Visualization Toolkit) – 3D rendering and visualization

Nibabel – for reading .nii medical imaging data

OBJ / NIfTI datasets – for anatomical model representation

🧑‍💻 Author

Sama Mohamed
🎓 Biomedical Engineering Project – 3D Medical Visualization Task
📅 2025
Choose one of the 6 visualization/navigation methods.

View and interact with the 3D model.
