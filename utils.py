import pandas as pd
import gpxpy
import glob
import numpy as np
import osmnx as ox
import os
import ast
import matplotlib.pyplot as plt
import textwrap
from datetime import datetime


def get_graph_stats(graph):
    G_proj = ox.projection.project_graph(graph)
    nodes_proj = ox.convert.graph_to_gdfs(G_proj, edges=False)
    graph_area_m = nodes_proj.union_all().convex_hull.area
    graph_area_m = nodes_proj.union_all().convex_hull.area
    stats = ox.stats.basic_stats(G_proj, area=graph_area_m, clean_int_tol=15)
    return stats

def get_all_edge_data(graph, coords_list):

    lats = [c[0] for c in coords_list]
    lons = [c[1] for c in coords_list]

    u_ids, v_ids, keys = ox.nearest_edges(graph, X=lons, Y=lats)

    gdf_edges = ox.graph_to_gdfs(graph, nodes=False, fill_edge_geometry=False)

    results = []
    
    for u, v, k in zip(u_ids, v_ids, keys):
        edge_data = gdf_edges.loc[(u, v, k)]
        
        if type(edge_attributes.get('name')) == str:  
            street_name = edge_attributes.get('name') #usually a string
        else:
            try:
                street_name = edge_attributes.get('name')[0] #edge with coords (41.4049091 2.1738864), (41.4052928 2.1755545) has Provenca and Marina
            except:
                street_name = "Unkwown" # edge from point 867 or 868 from PA has no street name
    #print(type(street_name),street_name)
        
        length = edge_data.get('length', 0)
        
        results.append(((u, v, k), street_name, length))
        
    return results

def save_last_read_gps_point(i,district,user):
    os.makedirs("edges/"+user,exist_ok=True)
    file_list_edges = "edges/last_gpx_point_"+district+"-"+user+".txt"
    with open(file_list_edges, "w") as f:
           f.write(str(i))

def get_coords_date_gpx(user):
    file = glob.glob(f'segments/{user}/*.gpx')[0] 
    gpx_file = open(file, 'r') 
    gpx = gpxpy.parse(gpx_file) 
    coords_gpx = []
    for track in gpx.tracks:
        for s, segment in enumerate(track.segments):
            if (user == 'hubert') & (s in [1, 6]):
                continue
            for points in segment.points:
                coords_gpx.append((points.latitude,points.longitude,points.time))
    return coords_gpx, points.time

def get_coords_dates_gpx(user):
    file = glob.glob(f'segments/{user}/*.gpx')[0] 
    gpx_file = open(file, 'r') 
    gpx = gpxpy.parse(gpx_file) 
    coords_gpx = []
    dates_gpx = []
    for track in gpx.tracks:
        for s, segment in enumerate(track.segments):
            if (user == 'hubert') & (s in [1, 6]):
                continue
            for points in segment.points:
                coords_gpx.append((points.latitude,points.longitude))
                dates_gpx.append(points.time.replace(tzinfo=None))
    return coords_gpx, points.time, dates_gpx



def get_list_edges(graph, coords_gpx, dates_gpx, district, user, start=None):
    os.makedirs("edges/"+user,exist_ok=True)
    file_list_edges = "edges/"+user+"/list_edges_"+district+"-"+user+".txt"
    list_edges = []
    
    if start and os.path.isfile(file_list_edges):
        print("Reading from previous list of edges")
        with open(file_list_edges, "r") as f:
            for line in f:
                if line.strip():
                    list_edges.append(ast.literal_eval(line))
    else:
        print("Starting new list of edges")
        with open(file_list_edges, "w") as f:
            pass 

    idx_start = start if start is not None else 0
    to_process = coords_gpx[idx_start:]
    
    if not to_process:
        return list_edges

    lats = [c[0] for c in to_process]
    lons = [c[1] for c in to_process]

    edges = ox.nearest_edges(graph, X=lons, Y=lats)

    gdf_edges = ox.graph_to_gdfs(graph, nodes=False)

    with open(file_list_edges, "a") as f:
#        for u, v, k in edges:
        for (u, v, k), edge_date in zip(edges, dates_gpx[idx_start:]):

            edge_attributes = gdf_edges.loc[(u, v, k)]
            if type(edge_attributes.get('name')) == str:  
                street_name = edge_attributes.get('name')
            else:
                try:
                    street_name = edge_attributes.get('name')[0]
                except:
                    street_name = "Unkwown"
            length_edge = float(edge_attributes.get('length'))
   #         edge_data = ((u, v, k), street_name, length_edge)
            edge_data = ((u, v, k), street_name, length_edge, edge_date)
            if edge_data not in list_edges:
                list_edges.append(edge_data)
                f.write(f"{edge_data}\n")

    save_last_read_gps_point(get_coords_date_gpx(user)[0], district, user)
    
    return list_edges

def load_last_gps_point(district,user):
    try:
        file_list_edges = "edges/"+user+"/last_gpx_point_"+district+"-"+user+".txtt" #bug with reading previous
        with open(file_list_edges, "r") as f:
            return int(f.read())
    except:
        return None
    

def generate_list_edges(graph_dict,user,list_districts):
    list_edges_read={}
    for district in list_districts:
        print(district)
        last_gps_point = load_last_gps_point(district,user)
        print("last_gps_point",last_gps_point)
        coords,_,dates_gpx=get_coords_dates_gpx(user)
        #coords=get_coords_dates_gpx(user)[0]
     #   dates_gpx = get_coords_dates_gpx(user)[2]
        list_edges_read[district] = get_list_edges(graph_dict[district],coords,dates_gpx, district,user,last_gps_point)

    return list_edges_read

def highlight_edges(graph,list_edges,user,color,district,date):
    #highlighted_edges_set={}
    # highlighted_edges_set[user] = {
    #     data[0] 
    #     for data in list_edges[user][district]
    # }
    edge_date_map = {
    data[0]: data[3]   # (u,v,k) → datetime
    for data in list_edges[user][district]
    }
    date_limit = datetime.strptime(date, "%Y-%m-%d")
    edge_colors = []
    for u, v, k in graph.edges(keys=True):
        edge_id = (u, v, k)

        if edge_id in edge_date_map:
         #   print(edge_date_map[edge_id],date_limit)
            if edge_date_map[edge_id] >= date_limit:
                edge_colors.append("green")
            else:
                edge_colors.append(color)
        else:
            edge_colors.append("grey")
    return edge_colors

#generalize this and the function below to have a way to plot by user and district and loop over this

def plot_mapped(graph_dict,list_edges,user,district,edge_colors,color):
    os.makedirs("plots/"+user,exist_ok=True)
    os.makedirs("stats/"+user,exist_ok=True)
    date=get_coords_date_gpx(user)[1].strftime("%Y-%m-%d")
    print(district)
    edge_colors[district]= highlight_edges(graph_dict,list_edges,user,color,district,date)
    fig, ax = ox.plot.plot_graph(
            graph_dict,
            edge_color=edge_colors[user][district],
            edge_linewidth=1.5,
            show=False,
            close=False,
            node_zorder=0,
            bgcolor="w"
        )
    ax.set_title(district+"-"+user)
  #  plt.show()
    fig.savefig("plots/"+user+"/"+district.replace(" ","_")+"-"+user+"."+date+".jpg", dpi=300, bbox_inches='tight')

def get_number_of_mapped_streets(list_edges):
    mapped_street_names = [edge_data for edge_data in list_edges]
    return len(set(mapped_street_names))

def get_number_of_streets(graph):
    
    unique_street_names_from_G = set()

# Iterate over all edges in the graph, retrieving the attribute data for each edge
# We use keys=False because the u, v, k are not strictly needed for this task,
# only the data dictionary is.
    for _, _, data in graph.edges(data=True):
    # The street name is stored under the key 'name'
        name_entry = data.get('name')
    
    # Check if the 'name' attribute exists
        if name_entry is not None:
            
            if isinstance(name_entry, list):
                # If the value is a list (multiple names), add all individual names to the set
                for name in name_entry:
                    unique_street_names_from_G.add(name)
            elif isinstance(name_entry, str):
            # If the value is a single string, add it to the set
                unique_street_names_from_G.add(name_entry)

# The count of unique street names is the length of the final set
    count_unique_names_G = len(unique_street_names_from_G)
    #print("Total number of streets",count_unique_names_G)
    return count_unique_names_G

def get_final_stats(user,list_edges,graph_dict,list_districts,stats):
    date=get_coords_date_gpx(user)[1].strftime("%Y-%m-%d")
    stats_file = "stats/stats-"+user+'_'+date+".csv"
    try:
        if os.path.exists(stats_file):
            prev_stats_file = sorted(glob.glob('stats/stats-'+user+'_*.csv'))[-2]
        else:
            prev_stats_file = sorted(glob.glob('stats/stats-'+user+'_*.csv'))[-1]
        df_prev = pd.read_csv(prev_stats_file)
        print("loading previous stats",prev_stats_file)
    except:
        df_prev = []
    if os.path.exists(stats_file):
        df = pd.read_csv(stats_file)
        print("reading from current file",stats_file)
    else:
        print("creating new stats file")
        number_of_mapped_streets = []
        total_number_of_streets = []
        number_of_mapped_segments = []
        total_number_of_segments = []
        mapped_kms = []
        total_street_length = []

        for district in list_districts:
            number_of_mapped_streets.append(get_number_of_mapped_streets(list_edges[user][district]))
            total_number_of_streets.append(get_number_of_streets(graph_dict[district]))
            number_of_mapped_segments.append(len(list_edges[user][district]))
            total_number_of_segments.append(stats[district]["m"])
            mapped_kms.append(sum(edge[2] for edge in list_edges[user][district])/1000)
            total_street_length.append(stats[district]["edge_length_total"]/1000)

        df = pd.DataFrame({
            "districts": list_districts,
            "number of mapped streets": number_of_mapped_streets,
            "total number of streets": total_number_of_streets,
            "percentage street": np.array(number_of_mapped_streets)/np.array(total_number_of_streets)*100,
            "number of mapped segments ": number_of_mapped_segments,
            "total number of segments" : total_number_of_segments, 
            "percentage segments": np.array(number_of_mapped_segments)/np.array(total_number_of_segments)*100,
            "mapped kms": mapped_kms,
            "total street length": total_street_length,
            "percentage km": np.array(mapped_kms)/np.array(total_street_length)*100
        })
    #    df.set_index('districts')
        df.to_csv(stats_file,index=False)
    return df,df_prev
    
def plot_stats(final_table,previous_table,list_districts):
    if isinstance(previous_table, pd.DataFrame) and not previous_table.empty:
        print("previous")
        diff = final_table.set_index("districts").subtract(previous_table.set_index("districts"), fill_value=0).abs()
        diff = diff.reset_index()
        display_cols = []
        new_data = {}

        for col in final_table.columns:
            if col != "districts":
                new_data[col] = final_table[col]
                display_cols.append(col)
        
                if (diff[col] != 0).any():
                    delta_col_name = "diff "+ col
                    new_data[delta_col_name] = diff[col]
                    display_cols.append(delta_col_name)

                df_display = pd.DataFrame(new_data, index=final_table.index)[display_cols]
    else:
        df_display = final_table
        print("no previous")
    return df_display.style \
        .format(precision=1) \
        .format_index(str.upper, axis=0) \
        .relabel_index(list_districts, axis=0) \
    .apply(lambda x: ['color: green; font-weight: bold' if 'diff' in x.name else '' 
                      for val in x], axis=0)



def wrap_header(text, width=14):
    return "\n".join(textwrap.wrap(text, width=width))

def dataframe_to_png(df, filename, list_districts):
    df_display = df.copy().reset_index(drop=True)
    try:
        df_display.insert(0, "districts", list_districts)
    except:
        pass

    col_labels = [wrap_header(c) for c in df_display.columns]
    cell_text = df_display.round(1).astype(str).values

    n_rows, n_cols = df_display.shape

    fig_width = max(14, n_cols * 1.45)
    fig_height = max(4, n_rows * 0.45)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")

    col_widths = []
    for col in df_display.columns:
        if col == "districts":
            col_widths.append(0.16)
        elif "diff" in col:
            col_widths.append(0.10)
        else:
            col_widths.append(0.085)

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        colWidths=col_widths,
        cellLoc="center",
        loc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    for (row, col), cell in table.get_celld().items():
        # Header row
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_height(cell.get_height() * 1.8)

        # District names
        if col == 0 and row > 0:
            cell.set_text_props(weight="bold")
            cell.get_text().set_ha("left")

        # Diff columns
        if "diff" in df_display.columns[col] and row > 0:
            cell.set_text_props(color="green", weight="bold")

    plt.tight_layout()
    plt.savefig(filename, dpi=200, bbox_inches="tight")
    plt.close()

def filter_df_for_district(df, list_districts, district_name):
    idx = list_districts.index(district_name)
    return df.iloc[[idx]]