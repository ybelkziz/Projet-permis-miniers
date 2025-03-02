# -*- coding: utf-8 -*-
import arcpy
import csv
import os
import settings

# Configuration
arcpy.env.workspace = arcpy.GetParameterAsText(0)

arcpy.env.overwriteOutput = True

in_dir = arcpy.GetParameterAsText(1)
csvFile = arcpy.GetParameterAsText(2)
fc_AUT_path = arcpy.GetParameterAsText(3)
y_threshold = float(arcpy.GetParameterAsText(4))

fc_base_name = "minepermit"
intersectSSMPermit = os.path.join(arcpy.env.workspace, "SSM_INT_PERMIT")


sr1 = arcpy.SpatialReference(settings.SR1)  # Si Y < 300000
sr2 = arcpy.SpatialReference(settings.SR2)  # Si Y >= 300000

# -----------------------------------------------------------
# ÉTAPE 1 : Lire le CSV et déterminer les SR nécessaires
# -----------------------------------------------------------
in_csv = os.path.join(in_dir, csvFile)
sr1_needed, sr2_needed = False, False
grouped_data = {}  # Format: {(num_pm, sr): [points]}

try:
    with open(in_csv, "r") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        header = next(csv_reader)  # Ignorer l'en-tête

        required_columns = ["BORNE", "X", "Y", "NUM_PM"]
        if header != required_columns:
            print("Erreur : Colonnes manquantes dans le CSV.")
            exit()

        for row in csv_reader:
            try:
                X = float(row[1])
                Y = float(row[2])
                NUM_PM = float(row[3])

                # Déterminer la référence spatiale
                if Y < y_threshold:
                    sr = sr1
                    sr1_needed = True
                else:
                    sr = sr2
                    sr2_needed = True

                key = (NUM_PM, sr)
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(arcpy.Point(X, Y))

            except (ValueError, IndexError):
                continue

except IOError:
    print("Erreur : Fichier CSV introuvable ou illisible !")
    exit()

# -----------------------------------------------------------
# ÉTAPE 2 : Créer les Feature Classes nécessaires
# -----------------------------------------------------------
fcs_created = []

# Supprimer les anciennes FC si elles existent
for suffix in ["_SR1", "_SR2"]:
    fc = fc_base_name + suffix
    if arcpy.Exists(fc):
        arcpy.Delete_management(fc)

# Créer les nouvelles FC
if sr1_needed:
    fc_sr1 = fc_base_name + "_SR1"
    arcpy.CreateFeatureclass_management(
        arcpy.env.workspace,
        fc_sr1,
        "POLYGON",
        spatial_reference=sr1
    )
    arcpy.AddField_management(fc_sr1, "NUM_PM", "DOUBLE")
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
# ÉTAPE 3 : Insérer les polygones
# -----------------------------------------------------------
for (NUM_PM, sr), points in grouped_data.items():
    if len(points) < 3:
        continue  # Ignorer les groupes de moins de 3 points

    fc_name = fc_base_name + ("_SR1" if sr == sr1 else "_SR2")

    with arcpy.da.InsertCursor(fc_name, ["SHAPE@", "NUM_PM"]) as cursor:
        polygon = arcpy.Polygon(arcpy.Array(points), sr)
        cursor.insertRow([polygon, NUM_PM])

print("Creation des polygones terminee dans : " + ", ".join(fcs_created))

# -----------------------------------------------------------
# ÉTAPE 4 : Selection spatiale
# -----------------------------------------------------------
try:
    # Créer une couche temporaire
    arcpy.MakeFeatureLayer_management(fc_AUT_path, "temp_layer")

    # Fusionner les FC si plusieurs SR utilisées
    if len(fcs_created) > 1:
        merged_fc = os.path.join(arcpy.env.workspace, "Merged_Permits")
        arcpy.Merge_management(fcs_created, merged_fc)
        input_features = merged_fc
    else:
        input_features = fcs_created[0]

    # Selection par localisation
    arcpy.SelectLayerByLocation_management(
        "temp_layer",
        "INTERSECT",
        input_features,
        selection_type= "NEW_SELECTION"
    )

    # Afficher le résultat
    count = arcpy.GetCount_management("temp_layer").getOutput(0)
    print("Points selectionnes : " + count)


except arcpy.ExecuteError as e:
    print("Erreur ArcGIS : " + str(e))

try:
    arcpy.analysis.Intersect(["temp_layer", input_features],
                             intersectSSMPermit,
                             join_attributes="ALL",
                             output_type="POINT")
    print("✔️ Intersection réussie")

except arcpy.ExecuteError as e:
    print("Erreur lors de l'intersection : {0}".format(e))

print(" Intersection réussie")

