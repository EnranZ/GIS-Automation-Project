import arcpy
import os
from datetime import datetime

# -------------------------
# USER SETTINGS
# -------------------------

# Input table: CSV, Excel sheet table, or geodatabase table
input_table = r"" 
# (Use your unique path)

# Workspace / output folder or geodatabase
output_gdb = r"" 
# (Use your unique output)

# Field names
submitted_field = "Submitted"   # use Submitted because Completed has errors
x_field = "x"           # change to your actual X field
y_field = "y"            # change to your actual Y field

# This is basically the XY Table to Point Function

# Years 
start_year = 2017
end_year = 2025

# Buffer distance in meters
buffer_distance = "100 Meters"

# Dissolve option: "NONE" or "ALL" (depends on what you want)
dissolve_option = "ALL"

# -------------------------
# ENVIRONMENT
# -------------------------

arcpy.env.overwriteOutput = True
arcpy.env.workspace = output_gdb

# Spatial references
sr_wgs84 = arcpy.SpatialReference(4326)   # GCS_WGS_1984
sr_utm17 = arcpy.SpatialReference(26917)  # NAD 1983 UTM Zone 17N

# Geographic transformation from WGS84 to NAD83
geo_transform = "WGS_1984_(ITRF00)_To_NAD_1983"
# If this transformation is unavailable on your machine, try:
# geo_transform = "NAD_1983_To_WGS_1984_1"
# or leave it blank: geo_transform = ""

# -------------------------
# HELPER FUNCTIONS
# -------------------------

def make_query(table, field_name, year):
    """
    Build SQL query for one year.
    Adjusts delimiters automatically depending on table type.
    """
    fld = arcpy.AddFieldDelimiters(table, field_name)
    start_date = f"{year}-01-01"
    end_date = f"{year + 1}-01-01"

    # File geodatabase / shapefile style
    # For many ArcGIS table types, this works:
    return f"{fld} >= DATE '{start_date} 00:00:00' AND {fld} < DATE '{end_date} 00:00:00'"


def delete_if_exists(path):
    if arcpy.Exists(path):
        arcpy.management.Delete(path)


# -------------------------
# MAIN WORKFLOW
# -------------------------

try:
    print("Starting workflow...")

    # Convert CSV to geodatabase table so it gets an ObjectID
    converted_table = os.path.join(output_gdb, "size_and_healthy_tbl")

    if arcpy.Exists(converted_table):
        arcpy.management.Delete(converted_table)

    arcpy.conversion.ExportTable(input_table, converted_table)

    input_table = converted_table
    print(f"Converted input table: {input_table}")


    for year in range(start_year, end_year + 1):
        print(f"\nProcessing year {year}...")

        # Names
        year_table_view = f"submitted_view_{year}"
        year_points = os.path.join(output_gdb, f"Submitted_{year}_XY")
        year_projected = os.path.join(output_gdb, f"Submitted_{year}_Project")
        year_buffer = os.path.join(output_gdb, f"Submitted_{year}_Buffer_100m")

        # Clean old temp layers / outputs
        delete_if_exists(year_points)
        delete_if_exists(year_projected)
        delete_if_exists(year_buffer)

        if arcpy.Exists(year_table_view):
            arcpy.management.Delete(year_table_view)

        # 1. Create table view
        arcpy.management.MakeTableView(input_table, year_table_view)

        # 2. Select records for that year using Submitted
        query = make_query(input_table, submitted_field, year)
        print(query)
        arcpy.management.SelectLayerByAttribute(year_table_view, "NEW_SELECTION", query)

        count = int(arcpy.management.GetCount(year_table_view)[0])
        print(f"Selected {count} records for {year}")

        if count == 0:
            print(f"No records found for {year}, skipping.")
            continue

        # 3. XY Table To Point
        arcpy.management.XYTableToPoint(
            in_table=year_table_view,
            out_feature_class=year_points,
            x_field=x_field,
            y_field=y_field,
            coordinate_system=sr_wgs84
        )
        print(f"Created XY points: {year_points}")

        # 4. Project to NAD 1983 UTM Zone 17N
        if geo_transform:
            arcpy.management.Project(
                in_dataset=year_points,
                out_dataset=year_projected,
                out_coor_system=sr_utm17,
                transform_method=geo_transform
            )
        else:
            arcpy.management.Project(
                in_dataset=year_points,
                out_dataset=year_projected,
                out_coor_system=sr_utm17
            )

        print(f"Projected to UTM 17N: {year_projected}")

        # 5. Buffer to 100 meters
        arcpy.analysis.Buffer(
            in_features=year_projected,
            out_feature_class=year_buffer,
            buffer_distance_or_field=buffer_distance,
            line_side="FULL",
            line_end_type="ROUND",
            dissolve_option=dissolve_option,
            method="PLANAR"
        )
        print(f"Created buffer: {year_buffer}")

        # Clear selection
        arcpy.management.SelectLayerByAttribute(year_table_view, "CLEAR_SELECTION")
        arcpy.management.Delete(year_table_view)

    print("\nWorkflow completed successfully.")

except Exception as e:
    print("Workflow failed.")
    print(arcpy.GetMessages())
    print(str(e))