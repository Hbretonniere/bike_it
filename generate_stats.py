import geopandas as gpd
import pandas as pd
import gpxpy
import glob
import gpxpy.gpx
from shapely.geometry import LineString
import matplotlib.pyplot as plt
from shapely.geometry import Point
import contextily as ctx
import matplotlib.animation as animation
import numpy as np
from utils import *
import osmnx as ox
import os
import ast
import argparse 

#%matplotlib widget

parser = argparse.ArgumentParser()

parser.add_argument(
        "--users", 
        nargs='+', 
        default=['hubert', 'pa'], 
        help="User from which to generate the stats. Default is all (pa, hubert). Looks for data in segments/user."
    )

parser.add_argument(
        "--districts", 
        nargs='+', 
        default=["Barcelona", "Ciutat_Vella", "Eixample", "Sants_Montjuic", "Les_Corts", "Sarria_Sant_Gervasi", "Gracia", "Horta_Guinardo", "Nou_Barris", "Sant_Andreu", "Sant_Marti"], 
        help="Specific district name or 'all' to process everything. Default is 'all' ([Barcelona, Ciutat_Vella, Eixample, Sants_Montjuic, Les_Corts, Sarria_Sant_Gervasi, Gracia, Horta_Guinardo, Nou_Barris, Sant_Andreu, Sant_Marti])."
    )

parser.add_argument(
        "--color", 
        type=str, 
        default="red", 
        help="The highlight color for the mapped streets. Default is 'red'."
    )

args = parser.parse_args()

users = args.users
districts = args.districts
color = args.color

print(districts)
if districts == ["all"]:
   print("from all to list")
   list_districts = ["Barcelona", "Ciutat_Vella", "Eixample", "Sants_Montjuic", "Les_Corts", "Sarria_Sant_Gervasi", "Gracia", "Horta_Guinardo", "Nou_Barris", "Sant_Andreu", "Sant_Marti"]
else:
   list_districts = districts    
if users == "all":
   list_users = ["pa", "hubert"]

graph_dict={}
graph_type = "bike" #walk or bike
print("graph_type:",graph_type)
os.makedirs("graphs",exist_ok=True)
for district in list_districts:
    filepath = "graphs/"+district+"-"+graph_type+".graphml"
    if not os.path.isfile(filepath):
        print("Downloading ",district,"from Internet")
        graph = ox.graph.graph_from_place(district + " ,Barcelona, Spain", network_type=graph_type)
        ox.save_graphml(G=graph,filepath=filepath)
    else:
        print("Loading",district," from file")
        graph = ox.load_graphml(filepath)
    graph_dict[district] = graph
print("All graphs loaded")

stats={}
for district in list_districts:
    print("Computing stats for", district)
    stats[district]=get_graph_stats(graph_dict[district])
    
list_edges = {}
edge_colors={}

for user in users:
    coords_date_gpx_pa,date_date_last_pa = get_coords_date_gpx(user)
    date=get_coords_date_gpx(user)[1].strftime("%Y-%m-%d")
    edge_colors[user]={}
    list_edges[user] = generate_list_edges(graph_dict,user,list_districts)
    for district in list_districts:
        edge_colors[user][district]= highlight_edges(graph_dict[district],list_edges,user,color,district)
    for district in list_districts:
        plot_mapped(
            graph_dict[district],
            list_edges,
            user,
            district,
            edge_colors,
            color
        )
    final_table,previous_table = get_final_stats(user,list_edges,graph_dict,list_districts,stats)
    styled_table = plot_stats(final_table, previous_table, list_districts)
   # print(styled_table.data.to_string())