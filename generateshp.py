# Imports
from math import asin, cos, radians, sin, sqrt
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Point, Polygon 

max_speed = 4.6  # Global Fishing Watch states maximum trawling speed for boats is 4.6 Knots

# Calculates maximum distance
def maxDist(time):
    return max_speed * time

# This function uses the Haversine formula to calculate distance between coordinates then converts the answer (in km) to knots
def calculate_distance(coord1, coord2):
    # https://www.youtube.com/watch?v=ZTRmK6GehUY
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    r = 6371
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = (2*asin(sqrt(a)))*r
    # Convert km to knots
    return (c/1.852)

# Creates maximum area of travel
def sPath(start, end, sea_shapefile, max_speed, time_of_travel):
    aegean = gpd.read_file(sea_shapefile)
    aegean = aegean.to_crs("EPSG:4326")

    tr = 1/60
    radius = time_of_travel*max_speed*tr
    start_point = Point(start[0], start[1])
    end_point = Point(end[0], end[1])
    start_circle = gpd.GeoDataFrame(geometry=[Polygon(start_point.buffer(radius))], crs="EPSG:4326")
    start_circle = start_circle.to_crs(aegean.crs)
    start_circle_clipped = gpd.clip(start_circle, aegean).geometry.iloc[0]

    end_circle = gpd.GeoDataFrame(geometry=[Polygon(end_point.buffer(radius))], crs="EPSG:4326")
    end_circle = end_circle.to_crs(aegean.crs)
    end_circle_clipped = gpd.clip(end_circle, aegean).geometry.iloc[0]

    intersection = start_circle_clipped.intersection(end_circle_clipped)
    intersection = gpd.clip(intersection, aegean)

    return intersection

# Creates a .shp based on all paths
def createPolygon(paths, output_shapefile):
    polygons = [Polygon(route_coordinates) for route_coordinates in paths]
    gdf2 = gpd.GeoDataFrame(geometry=polygons)
    gdf2.to_file(output_shapefile, driver='ESRI Shapefile')
    return gdf2

# Creates & saves the area of travel .shp if requirements are met
def viz(start, end, max_speed, time_of_travel, sea_shapefile, output_shapefile, gapID):
    md = maxDist(time_of_travel) 
    d = calculate_distance(start,end)
    if md <= d:
        raise ValueError(f"Error: {gapID} had to have been moving faster than MAX trawling speed at some point.")
    else:
        p = sPath(start, end, sea_shapefile, max_speed, time_of_travel)
        createPolygon(p, output_shapefile)

# 
# Reads CSV, iterates through each row and saves the created SHP to the output folder
#
df = pd.read_csv('./Data/{}.csv') # Update this line with the CSV you want to use to get the shapefiles off of
for _, row in df.iterrows():
    start = (row['gap_start_lat'], row['gap_start_lon'])  
    end = (row['gap_end_lat'], row['gap_end_lon'])  
    max_speed = 4.6  
    time_of_travel = row['gap_hours']  
    id = row['gap_id']

    # Assign shapefiles, run
    sea_shapefile = './Data/Geo Data/Aegean/iho.shp' 
    output_shapefile = './Output/maximum_travel_area_{}.shp'.format(id)  
    viz(start, end, max_speed, time_of_travel, sea_shapefile, output_shapefile, id)