# Archipelagos Summer Intern Project 2023

# Summary
Hi guys!! (: The two main functions of this repository are the GE_Analysis.py and generateshp.py scripts. GE_Analysis is a GUI tool that allows users to upload a CSV, query it, and generate a map using matplotlib. The other main functionality is generateshp, in the code enter the CSV and run the program. The program will output a shapefile for each row of the CSV listed by gap event ID. 

# Instructions for future interns:
1. Move any gap event data (from supervisor) into the data folder
2. If you are not so keen on working with code for the GE Analysis, you can create an executable file by installing pyInstaller and running "python -m PyInstaller GE_Analysis" in the terminal

Please make sure you read and understand the README.md and LICENSE throughly before moving forward with the project and code.

# Currents FIXES
- TODO Update graph every time generate map is clicked
- TODO Update tst.py to download polygons of possible range
- TODO Add basic toolbar
        - Add draw feature
        - Add drag bar to change speed
        - Add option to highlight most popular trawling areas
- TODO Add overlaying and comparing maps
- TODO Add ML model for most plausible route based off MMSI
