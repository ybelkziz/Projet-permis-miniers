
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 
🏞️ Mining Permits Automation with ArcPy
CSV to Georeferenced Polygons Conversion with Dynamic Spatial Reference Management

This project processes CSV files containing geographic coordinates (Conformal Conic Projection Zones 1 and 2), converts them into georeferenced polygons, and analyzes intersections with mining authorizations or indices...

📋 Table of Contents
Features

- Prerequisites

- Installation

- Usage

- Data Structure

- Contribution

- License

🚀 Features
CSV → Polygons Conversion :

1. Dynamic transformation of points into polygons using two spatial references (Lambert Zone 1 and 2).

2. Automatic projection switching based on Y-coordinates.

Spatial Analysis :

1. Selection of intersecting mining authorizations via SelectLayerByLocation.

2. Intersection layer generation (Intersect) for technical reporting.

Robustness :

* CSV column validation and error handling.

🛠️ Prerequisites
Software :

* ArcMap 10.2 or later.

* Spatial Analyst extension (recommended).

Languages :

* Python 2.7 (ArcGIS environment).

🔧 Installation
Clone the Repository :

bash
Copy
git clone https://github.com/your_username/Mining-Permits-Project.git  
cd Mining-Permits-Project  
Configuration :

- Modify settings.py to set spatial reference WKIDs.

- Place your CSV file in the data/ folder.

ArcMap Integration :

- Create a new Toolbox in ArcMap.

- Add the src/job_automation.py script and configure inputs/outputs.

🖥️ Usage
Input Parameters :

- Output Geodatabase : Target a File GDB.

- CSV File : Ensure it follows this format.

- Mining Authorizations Layer or indices layers... : An existing point feature layer.

Execution :

- Run the script via the ArcMap Toolbox.

- Results are stored in the specified geodatabase.

📂 Data Structure
Input CSV File
Required columns :

- csv Copy:

BORNE;X;Y;NUM_PM  
0;536879.98;418255.87;2050154  
1;540879.98;418255.87;2050154  
Generated Outputs

- Polygon layers : minepermit_SR1 and/or minepermit_SR2.

- Intersection layer : SSM_INT_PERMIT.

🤝 Contribution
Contributions are welcome!

- Report bugs via Issues.

- Propose enhancements via Pull Requests.

## 📄 License  
This project is licensed under the [MIT License](LICENSE).  

**Copyright © 2025 Youssouf BELKZIZ**  
> The MIT License permits anyone obtaining a copy of this software and associated documentation files to deal in the Software without restriction, including rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell. 
