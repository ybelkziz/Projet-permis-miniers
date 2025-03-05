# -*- coding: utf-8 -*-
import arcpy
import csv
import os
import settings  # Configuration file containing spatial references

# -----------------------------------------------------------
# ARCPY ENVIRONMENT CONFIGURATION
# -----------------------------------------------------------
# Define the ArcPy workspace where results will be stored
arcpy.env.workspace = arcpy.GetParameterAsText(0)
# Allow overwriting existing files without confirmation
arcpy.env.overwriteOutput = True

# Retrieve parameters passed to the ArcGIS tool
in_dir = arcpy.GetParameterAsText(1)  # Directory containing the CSV file
csvFile = arcpy.GetParameterAsText(2)  # Name of the CSV file to process
fc_AUT_path = arcpy.GetParameterAsText(3)  # Path to the reference Feature Class (autorizations or permits...)
y_threshold = float(arcpy.GetParameterAsText(4))  # Threshold for selecting the spatial reference

# Define the base name for Feature Classes
fc_base_name = "minepermit"
# Path where the intersection results will be stored
intersectSSMPermit = os.path.join(arcpy.env.workspace, "SSM_INT_PERMIT")

# Define spatial references based on the Y threshold
sr1 = arcpy.SpatialReference(settings.SR1)  # Used if Y < threshold (e.g., 300000)
sr2 = arcpy.SpatialReference(settings.SR2)  # Used if Y >= threshold

# -----------------------------------------------------------
# STEP 1: READING THE CSV FILE AND GROUPING DATA
# -----------------------------------------------------------
in_csv = os.path.join(in_dir, csvFile)
sr1_needed, sr2_needed = False, False  # Flags to track which SRs are needed
grouped_data = {}  # Dictionary to group points by NUM_PM and SR

try:
    # Open and read the CSV file
    with open(in_csv, "r") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        header = next(csv_reader)  # Read the first line (header)

        # Check if the required columns are present
        required_columns = ["BORNE", "X", "Y", "NUM_PM"]
        if header != required_columns:
            print("Error: Missing columns in the CSV file.")
            arcpy.AddMessage("Error: Missing columns in the CSV file.")
            exit()

        # Iterate through each row in the CSV file
        for row in csv_reader:
            try:
                X = float(row[1])  # X coordinate
                Y = float(row[2])  # Y coordinate
                NUM_PM = float(row[3])  # Permit number

                # Determine the spatial reference based on Y value
                if Y < y_threshold:
                    sr = sr1
                    sr1_needed = True
                else:
                    sr = sr2
                    sr2_needed = True

                # Create a key based on NUM_PM and the associated SR
                key = (NUM_PM, sr)
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(arcpy.Point(X, Y))

            except (ValueError, IndexError):
                continue  # Ignore incorrect rows

except IOError:
    print("Error: CSV file not found or unreadable!")
    arcpy.AddMessage("Error: CSV file not found or unreadable!")
    exit()

# -----------------------------------------------------------
# STEP 2: CREATING FEATURE CLASSES
# -----------------------------------------------------------
fcs_created = []  # List of created Feature Classes

# Remove old Feature Classes if they exist
for suffix in ["_SR1", "_SR2"]:
    fc = fc_base_name + suffix
    if arcpy.Exists(fc):
        arcpy.Delete_management(fc)

# Create new Feature Classes based on the required spatial references
if sr1_needed:
    fc_sr1 = fc_base_name + "_SR1"
    arcpy.CreateFeatureclass_management(
        arcpy.env.workspace,
        fc_sr1,
        "POLYGON",  # Geometry type
        spatial_reference=sr1
    )
    arcpy.AddField_management(fc_sr1, "NUM_PM", "DOUBLE")  # Add a field to store NUM_PM
    fcs_created.append(fc_sr1)

if sr2_needed:
    fc_sr2 = fc_base_name + "_SR2"
    arcpy.CreateFeatureclass_management(
        arcpy.env.workspace,
        fc_sr2,
        "POLYGON",
        spatial_reference=sr2
    )
    arcpy.AddField_management(fc_sr2, "NUM_PM", "DOUBLE")
    fcs_created.append(fc_sr2)

# -----------------------------------------------------------
# STEP 3: INSERTING POLYGONS
# -----------------------------------------------------------
for (NUM_PM, sr), points in grouped_data.items():
    if len(points) < 3:
        continue  # Ignore groups with fewer than 3 points since a polygon requires at least three vertices

    fc_name = fc_base_name + ("_SR1" if sr == sr1 else "_SR2")

    with arcpy.da.InsertCursor(fc_name, ["SHAPE@", "NUM_PM"]) as cursor:
        polygon = arcpy.Polygon(arcpy.Array(points), sr)
        cursor.insertRow([polygon, NUM_PM])

print("Polygon creation completed in: " + ", ".join(fcs_created))
arcpy.AddMessage("Polygon creation completed in: " + ", ".join(fcs_created))

# -----------------------------------------------------------
# STEP 4: SPATIAL SELECTION
# -----------------------------------------------------------
try:
    # Create a temporary layer from the reference Feature Class
    arcpy.MakeFeatureLayer_management(fc_AUT_path, "temp_layer")

    # Merge Feature Classes if multiple spatial references are used
    if len(fcs_created) > 1:
        merged_fc = os.path.join(arcpy.env.workspace, "Merged_Permits")
        arcpy.Merge_management(fcs_created, merged_fc)
        input_features = merged_fc
    else:
        input_features = fcs_created[0]

    # Select entities that intersect the created polygons
    arcpy.SelectLayerByLocation_management(
        "temp_layer",
        "INTERSECT",
        input_features,
        selection_type="NEW_SELECTION"
    )

    # Count the number of selected points
    count = arcpy.GetCount_management("temp_layer").getOutput(0)
    print("Selected points: " + count)
    arcpy.AddMessage("Selected points: " + count)

except arcpy.ExecuteError as e:
    print("ArcGIS Error: " + str(e))
    arcpy.AddMessage("ArcGIS Error: " + str(e))

# Perform spatial intersection
try:
    arcpy.analysis.Intersect(["temp_layer", input_features],
                             intersectSSMPermit,
                             join_attributes="ALL",
                             output_type="POINT")
    print("✔️ Intersection successful")
    arcpy.AddMessage("✔️ Intersection successful")

except arcpy.ExecuteError as e:
    print("Error during intersection: {0}".format(e))
    arcpy.AddMessage("Error during intersection: {0}".format(e))

print("Intersection successful")
arcpy.AddMessage("Intersection successful")

