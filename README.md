# GIS Buffer Automation (ArcPy)

This project automates buffer analysis workflows in ArcGIS Pro using Python (ArcPy).

## Overview
The script processes point data and generates 100 meter buffers for each year from 2017 to 2025.

## Features
- Year based filtering of spatial data
- Automated 100 meter buffer creation
- Dissolve operation to merge overlapping buffers
- Batch processing across multiple years

## Tools & Technologies
- ArcGIS Pro
- Python (ArcPy)

## Workflow
1. Load input dataset (CSV or table with coordinates)
2. Convert to point feature class
3. Filter data by year (2017-2025)
4. Generate 100m buffers for each year
5. Dissolve buffers for spatial analysis

## Use Case
This script improves efficiency in GIS workflows by automating repetitive spatial operations.

## Author
Enran Zu
