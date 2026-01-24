import geopandas as gpd
import pandas as pd
import gpxpy
import glob
import gpxpy.gpx
from shapely.geometry import LineString
import matplotlib
matplotlib.use('Agg')
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
        help="Specific district name or 'all' to process everything."
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

if districts == ["all"]:
   list_districts = ["Barcelona", "Ciutat_Vella", "Eixample", "Sants_Montjuic", "Les_Corts", "Sarria_Sant_Gervasi", "Gracia", "Horta_Guinardo", "Nou_Barris", "Sant_Andreu", "Sant_Marti"]
else:
   list_districts = districts    

graph_dict={}
graph_type = "bike" 
os.makedirs("graphs", exist_ok=True)

for district in list_districts:
    filepath = "graphs/"+district+"-"+graph_type+".graphml"
    if not os.path.isfile(filepath):
        graph = ox.convert.to_undirected(ox.graph.graph_from_place(district + " ,Barcelona, Spain", network_type=graph_type))
        ox.save_graphml(G=graph, filepath=filepath)
    else:
        graph = ox.load_graphml(filepath)
    graph_dict[district] = graph

stats={}
for district in list_districts:
    stats[district] = get_graph_stats(graph_dict[district], district)

edge_colors = {user: {} for user in users}
edge_widths = {user: {} for user in users}

for user in users:
    coords, _, dates_gpx = get_coords_dates_gpx(user)
    unique_days = sorted(list(set(d.strftime("%Y-%m-%d") for d in dates_gpx)))
    full_history_edges = generate_list_edges(graph_dict, user, list_districts)
    
    last_day = unique_days[-1]
    for current_date in unique_days:
        print(f"Processing {user} for {current_date}")
        
        list_edges_snapshot = {}
        for district in list_districts:
            list_edges_snapshot[district] = [
                e for e in full_history_edges[district] 
                if e[3].split('T')[0] <= current_date
            ]

            colors, widths = highlight_edges(
                graph_dict[district], {user: list_edges_snapshot}, user, color, district, current_date
            )
            edge_colors[user][district] = colors
            edge_widths[user][district] = widths

        stats_check_file = f"stats/{user}/stats-{user}-{current_date}.png"
        if not os.path.exists(stats_check_file):
            for district in list_districts:
                plot_mapped(
                    graph_dict[district],
                    user,
                    district,
                    edge_colors[user][district],
                    edge_widths[user][district],
                    color,
                    current_date
                )

            if current_date == last_day:
                final_table, previous_table = get_final_stats(
                    user, {user: list_edges_snapshot}, graph_dict, list_districts, stats, current_date
                )
            
                styled_stats = plot_stats(final_table, previous_table, list_districts)
                dataframe_to_png(styled_stats.data, stats_check_file, list_districts)
            
                for district in list_districts:
                    table_stats_district = filter_df_for_district(styled_stats.data, list_districts, district)
                    dataframe_to_png(
                        table_stats_district,
                        f"stats/{user}/stats-{district}-{user}-{current_date}.png",
                        [district]
                    )
                    create_gif(district, user)

for district in list_districts:
    merged_colors = merge_edges(edge_colors["pa"][district], edge_colors["hubert"][district])
    plot_mapped(
        graph_dict[district],
        "comparison",
        district,
        merged_colors,
        0.5,
        color,
        current_date
    )