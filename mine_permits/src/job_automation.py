# -*- coding: utf-8 -*-
import arcpy
import csv
import os

arcpy.env.workspace = r"C:\Users\hp\Desktop\MA FORMATION ARCPY\Projet permis miniers\mine_permits\PM.mdb"
arcpy.env.overwriteOutput = True

in_dir = r"C:\Users\hp\Desktop\MA FORMATION ARCPY\Projet permis miniers"
csvFile = "permi.csv"
fc = "minepermit"
in_csv = os.path.join(in_dir, csvFile)
fc_AUT_path = r"C:\Users\hp\Desktop\MA FORMATION ARCPY\Projet permis miniers\mine_permits\PM.mdb\SSM_AUTORISATIONS"
fc_AUT_layer = "SSM_AUTORISATIONS_lyr"
sr = arcpy.SpatialReference(102192)
intersectSSMPermit = os.path.join(arcpy.env.workspace, "SSM_INT_PERMIT")

if arcpy.Exists(fc):
    arcpy.Delete_management(fc)

if arcpy.Exists(intersectSSMPermit):
    arcpy.Delete_management(intersectSSMPermit)

arcpy.management.CreateFeatureclass(
    arcpy.env.workspace, fc, geometry_type="POLYGON", spatial_reference=sr
)

arcpy.management.AddField(fc, "ID", "DOUBLE")
arcpy.management.AddField(fc, "NUM_PM", "DOUBLE")


with arcpy.da.InsertCursor(fc, ["SHAPE@", "NUM_PM"]) as cursor:
    point_list = []
    NUM_PM_VALUE = None
    is_first_pass = True

    if not os.path.exists(in_csv):
        print("Fichier CSV introuvable !")
        exit()

    with open(in_csv, mode="r") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        header = next(csv_reader) # Ignore la première ligne (les noms des colonnes)
        for row in csv_reader:
            # Convertir correctement les valeurs X et Y
            try:
                X = float(row[1])
                Y = float(row[2])
                current_NUM_PM = float(row[3])
            except ValueError:
                continue


            if is_first_pass:
                NUM_PM_VALUE = current_NUM_PM
                is_first_pass = False
            elif current_NUM_PM != NUM_PM_VALUE:
                if point_list: # Vérifier si la liste de points n'est pas vide
                    polygon = arcpy.Polygon(arcpy.Array(point_list), sr)
                    cursor.insertRow([polygon, NUM_PM_VALUE])
                NUM_PM_VALUE = current_NUM_PM
                point_list = [] # Réinitialiser la liste des points

            point_list.append(arcpy.Point(X, Y))

        if point_list:
            polygon = arcpy.Polygon(arcpy.Array(point_list), sr)
            cursor.insertRow([polygon, NUM_PM_VALUE])

    print("✔️ Traitement terminé avec succès !")


    arcpy.MakeFeatureLayer_management(fc_AUT_path, fc_AUT_layer)

    try:
        arcpy.management.SelectLayerByLocation(fc_AUT_layer,
                                               overlap_type = "INTERSECT" ,
                                               select_features = fc,
                                               selection_type="NEW_SELECTION")
    except arcpy.ExecuteError as e:
        print("Erreur ArcPy : {0}".format(e))


    print("{0} points sélectionnés.".format(arcpy.GetCount_management(fc_AUT_layer).getOutput(0)))

    try:
        arcpy.analysis.Intersect([fc_AUT_layer, fc],
                                 intersectSSMPermit,
                                 join_attributes = "ALL",
                                 output_type = "POINT")
        print("✔️ Intersection réussie")

    except arcpy.ExecuteError as e:
        print("Erreur lors de l'intersection : {0}".format(e))

    print(" Intersection réussie")