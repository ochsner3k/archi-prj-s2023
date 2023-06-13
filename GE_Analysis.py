# Imports
import tkinter as tk
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import sys
from math import asin, cos, radians, sin, sqrt
from shapely.geometry import Point, Polygon
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

max_speed = 4.6  # Global Fishing Watch states maximum trawling speed for boats is 4.6 Knots
current_graph = None

# Function allows users to upload a CSV
def upload_csv():
    global df  
    file_path = file_entry.get()
    try:
        df = pd.read_csv(file_path)
        df_display = df.iloc[:, :6] 
        csv_display.delete("1.0", tk.END) 
        csv_display.insert(tk.END, df_display.to_string()) 
        global current_entry, num_entries
        current_entry = 0
        num_entries = len(df)  
        highlight_row(current_entry) 

    except FileNotFoundError:
        csv_display.delete("1.0", tk.END)
        csv_display.insert(tk.END, "File not found!")
    except pd.errors.ParserError:
        csv_display.delete("1.0", tk.END)
        csv_display.insert(tk.END, "Invalid CSV file!")

# Fuction allows users to query the CSV using (), |, &, <, >, <=, >=, == 
# EX. ( mmsi == 237302000 & gap_hours <= 10 ) | ( mmsi == 237371000 & gap_hours > 11 )
def execute_query():
    query = query_entry.get()
    try:
        result = df.query(query)
        csv_display.delete("1.0", tk.END)
        df_display = result.iloc[:, :6] 
        csv_display.insert(tk.END, df_display.to_string()) 

        row_details.delete("1.0", tk.END)
        highlight_row(current_entry) 

        if current_graph:
            current_graph.get_tk_widget().destroy()
    except pd.errors.ParserError:
        csv_display.delete("1.0", tk.END)
        csv_display.insert(tk.END, "Invalid query!")
    except ValueError:
        csv_display.delete("1.0", tk.END)
        csv_display.insert(tk.END, "Invalid query!")
    except pd.errors.UndefinedVariableError:
        csv_display.delete("1.0", tk.END)
        csv_display.insert(tk.END, "Invalid query!")

# Function highlights the current entry
def highlight_row(index):   
    current_entry = index
    csv_display.tag_remove("highlight", "1.0", tk.END)
    csv_display.tag_add("highlight", f"{index + 2}.0", f"{index + 2}.end")
    csv_display.tag_config("highlight", background="pink")
    csv_display.tag_add("row", f"{index + 2}.0", f"{index + 2}.end")

    csv_display.see(f"{index + 2}.0")  
    row_details_text = plot_frame.winfo_children()[0]

    row_details.delete("1.0", tk.END)
    row_details.insert(tk.END, df.iloc[index].to_string())
    index = current_entry

# Function allows rows to be navigated
def navigate_row(event):
    global current_entry
    if event.keysym == "Up":
        current_entry = (current_entry - 1) % num_entries  
    elif event.keysym == "Down":
        current_entry = (current_entry + 1) % num_entries  
    highlight_row(current_entry) 

# Function minimizes the program window
def minimize_program():
    root.iconify()

# Function closes the window and terminates the program
def terminate_program():
    sys.exit()

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

# Function reads variables from the selected row and calls the visualization function if requirements are met
def plot_graph():
    if current_entry is None:
        return
    else:
        selected_row = df.iloc[current_entry]
        start = (selected_row['gap_start_lon'], selected_row['gap_start_lat'])
        end = (selected_row['gap_end_lon'], selected_row['gap_end_lat'])
        time_of_travel = selected_row['gap_hours']
        start_heading = selected_row['gap_start_course']
        end_heading = selected_row['gap_end_course']
        sea_shapefile = './Data/Geo Data/Aegean/iho.shp'
        protected_areas = './Data/Geo Data/ProtectedAreas_Aegean/ProtectedAreas_Aegean.shp'

        md = time_of_travel * max_speed
        d = calculate_distance(start, end)

        if md <= d:
            csv_display.delete("1.0", tk.END)
            csv_display.insert(tk.END, "Error: Ship had to have been moving faster than MAX trawling speed at some point.")
            return
        else:
            viz(start, end, max_speed, time_of_travel, sea_shapefile, protected_areas, start_heading, end_heading)

# This function visualizes the map with the given inputs
def viz(start, end, max_speed, time_of_travel, sea_shapefile, protectedAreas, sCourse, eCourse, gapID):
    # Based graph with protected areas
    aegean = gpd.read_file(sea_shapefile)
    fig, ax = plt.subplots(figsize=(10, 10), dpi=100, tight_layout=True)  
    aegean.plot(ax=ax, color='midnightblue')
    aegean = aegean.to_crs("EPSG:4326")
    pA = gpd.read_file(protectedAreas)
    pA.crs = aegean.crs
    pA = gpd.clip(pA, aegean)
    pA.plot(ax=ax, color='white', alpha=0.3,aspect=1)
    ax.set_facecolor('xkcd:black')

    # Draws max area of travel
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
    gpd.GeoSeries([intersection]).plot(ax=ax, color='green', alpha=0.4, linewidth=0)

    # Plots the start and end locations of the gap event with the vessel's direction of course
    triangle_size = 0.025  
    triangle_points = [
        (start[0] - triangle_size * np.cos(sCourse + np.pi/2), start[1] - triangle_size * np.sin(sCourse + np.pi/2)),
        (start[0] + 2.5 * triangle_size * np.cos(sCourse), start[1] + 2.5 * triangle_size * np.sin(sCourse)),
        (start[0] - triangle_size * np.cos(sCourse - np.pi/2), start[1] - triangle_size * np.sin(sCourse - np.pi/2))
    ]

    ax.plot(*zip(*triangle_points, triangle_points[0]), color='firebrick', label='start')
    triangle_points = [
        (end[0] - triangle_size * np.cos(eCourse + np.pi/2), end[1] - triangle_size * np.sin(eCourse + np.pi/2)),
        (end[0] + 2.5 * triangle_size * np.cos(eCourse), end[1] + 2.5 * triangle_size * np.sin(eCourse)),
        (end[0] - triangle_size * np.cos(eCourse - np.pi/2), end[1] - triangle_size * np.sin(eCourse - np.pi/2))
    ]
    ax.plot(*zip(*triangle_points, triangle_points[0]), color='limegreen', label= 'end')
    ax.set_xlim(aegean.total_bounds[0], aegean.total_bounds[2])
    ax.set_ylim(aegean.total_bounds[1], aegean.total_bounds[3])

    # Supplements the legend, the gap event ID labeled at the bottom of the map, the nav toolbar
    ax.legend()
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
    gap_id_label = ax.text(0.02, 0.02, f"ID: {gapID}", transform=ax.transAxes, color='white')
    ax.plot()
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, plot_frame)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, plot_frame)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    current_graph = canvas

# GUI view, self explanatory
root = tk.Tk()
root.title("GE Analysis")
root.attributes('-fullscreen', True)

file_frame = tk.Frame(root)
file_frame.pack(side=tk.TOP, fill=tk.X)

file_label = tk.Label(file_frame, text="CSV Path:")
file_label.pack(side=tk.LEFT)
file_entry = tk.Entry(file_frame)
file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

upload_button = tk.Button(file_frame, text=" Upload ", fg="black", command=upload_csv)
upload_button.pack(side=tk.LEFT)
minimize_button = tk.Button(file_frame, text=" - ", command=minimize_program)
minimize_button.pack(side=tk.LEFT)
exit_button = tk.Button(file_frame, text=" X ", fg="red", command=terminate_program)
exit_button.pack(side=tk.LEFT)

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)
root.iconbitmap("./Data/ic.ico")

csv_display = tk.Text(frame, height=10, width=75)
csv_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
csv_display_height = 4
csv_display.config(height=csv_display_height)

plot_frame = tk.Frame(frame)
plot_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

query_frame = tk.Frame(frame)
query_frame.pack(side=tk.TOP, fill=tk.X)

query_label = tk.Label(query_frame, text="Query: ")
query_label.pack(side=tk.LEFT)
query_entry = tk.Entry(query_frame)
query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

query_button = tk.Button(query_frame, text="     Execute      ", command=execute_query)
query_button.pack(side=tk.LEFT)

row_details = tk.Text(plot_frame, height=10, width=75)
row_details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

plot_button = tk.Button(plot_frame, text="Generate Map", command=plot_graph)
plot_button.pack(side=tk.RIGHT)

root.bind("<Up>", navigate_row)  
root.bind("<Down>", navigate_row)

frame.rowconfigure(0, weight=1)
frame.columnconfigure(0, weight=1)

root.mainloop()