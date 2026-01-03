from sklearn.cluster import DBSCAN
import geopandas as gpd
from scipy.spatial import KDTree
import gpxpy
import glob
import matplotlib.pyplot as plt
import contextily as ctx
import numpy as np


def load_long_lat(user, n_segments=None):

    # Parsing an existing file:
    # -------------------------
    file = glob.glob(f'segments/{user}/*.gpx')[0]
    gpx_file = open(file, 'r')

    gpx = gpxpy.parse(gpx_file)
    track = []
    lats_tot = []
    longs_tot = []
    times_tot = []
    # xs_nc = []
    # ys_nc = []
    # cuts = []
    pts = 0
    for track_i in gpx.tracks:
        for s, segment in enumerate(track_i.segments):

            if (user == 'hubert') & (s in [1, 6, 30]):
                continue
            if (user == 'pa') & (s == 37):
                continue
            if n_segments:
                if s >= n_segments:
                    return track, longs_tot, lats_tot
            longs = []
            lats = []
            times = []
            for point in segment.points:
                lats.append(point.latitude)
                longs.append(point.longitude)
                times.append(point.time)
                pts += 1
            gdf_points = gpd.GeoDataFrame(
                geometry=gpd.points_from_xy(longs, lats),
                crs="EPSG:4326")
            gdf_points = gdf_points.to_crs(epsg=3857)
            xs_merc, ys_merc = zip(*[(p.x, p.y) for p in gdf_points.geometry])
            xs_merc = np.array(xs_merc)
            ys_merc = np.array(ys_merc)
            track.append({'lats': ys_merc,
                          'longs': xs_merc,
                          'times': times})
            longs_tot.extend(xs_merc)
            lats_tot.extend(ys_merc)
            times_tot.extend(times)
    return track, longs_tot, lats_tot, times_tot


def static_plot(gpx_infos, user, fig, ax,
                x_min_global, x_max_global, y_min_global, y_max_global,
                step, round,
                with_map,
                map_style,
                colors,
                density,
                lws={'hubert': 5,
                     'pa': 5}):

    track = gpx_infos[user]['track']
    longs_tot = gpx_infos[user]['longs']
    lats_tot = gpx_infos[user]['lats']
    if density:
        centers = gpx_infos[user]['centers']
        pass_counts = gpx_infos[user]['counts']
        # mask = gpx_infos[user]['mask']
        # counts = gpx_infos[user]['counts']
    # lw = 0.8
    x_min = min(longs_tot) - 500
    x_max = max(longs_tot) + 500
    y_min = min(lats_tot) - 500
    y_max = max(lats_tot) + 500

    if x_min_global > x_min:
        x_min_global = x_min
    if x_max_global < x_min:
        x_max_global = x_max
    if y_min_global > y_min:
        y_min_global = y_min
    if y_max_global < y_min:
        y_max_global = y_max

    ax.set_xlim(x_min_global, x_max_global)
    ax.set_ylim(y_min_global, y_max_global)
    if with_map:
        if map_style:
            ctx.add_basemap(ax, source=map_style)
        else:
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
    ax.set_axis_off()
    # seg_start = 0
    if not density:
        for segment in track:
            # xs = np.round(np.array(longs_tot['longs'][::step])/100, round)*100
            # ys = np.round(np.array(segment['lats'][::step])/0.1, round)*10
            # xs = np.round(np.array(segment['longs'][::step]), round)
            lats_tot = np.array(segment['lats'][::step])
            longs_tot = np.array(segment['longs'][::step])
            # seg_end = seg_start + len(lats_tot)
            ax.plot(longs_tot, lats_tot, color=colors[user],
                    lw=lws[user]/10,
                    alpha=0.7)
    else:
        for (x, y), v in zip(centers, pass_counts):
            # use your existing plotting logic
            # color/size based on v
            ax.scatter(x, y, s=20 + 10*v, c=v, alpha=0.8)
    return fig, ax, x_min_global, x_max_global, y_min_global, y_max_global,


def plot_track(users,
               gpx_infos,
               density,
               colors,
               lws,
               step=2, round=10, with_map=True,
               dpi=500, savefig=True,
               nicegui=False,
               map_style=False):

    if nicegui:
        fig = plt.gcf()
        fig.clf()  # Clear any previous plots from the figure
        ax = fig.subplots()
    else:
        fig, ax = plt.subplots(figsize=(8, 8))
    if not with_map:
        suffix = '_blankmap'
    else:
        suffix = ''
    x_min_global, x_max_global, y_min_global, y_max_global = \
        np.inf, -np.inf, np.inf, -np.inf

    for user in users:
        if not map_style:
            with_map = False
        else:
            with_map = with_map

        fig, ax, x_min_global, x_max_global, y_min_global, y_max_global, = \
            static_plot(gpx_infos,
                        user, fig, ax,
                        x_min_global, x_max_global,
                        y_min_global, y_max_global,
                        step, round,
                        with_map,
                        map_style,
                        colors,
                        density,
                        lws)
        if savefig:
            plt.savefig(f'new_track_{user}{suffix}.png', dpi=dpi)


def calculate_track_density_and_mask(easting, northing, timestamps,
                                     radius_meters, time_excl_seconds=60):
    """
    Spatial aggregation + temporal exclusion.
    """
    if len(easting) != len(northing) or len(easting) != len(timestamps):
        return np.array([]), np.array([])

    points = np.column_stack((easting, northing))
    times = np.array(timestamps)
    n = len(points)

    tree = KDTree(points)
    final_pass_counts = np.zeros(n, dtype=int)
    visibility_mask = np.ones(n, dtype=bool)

    for i in range(n):
        if not visibility_mask[i]:
            continue

        neighbor_indices = tree.query_ball_point(points[i], r=radius_meters)

        count = 1  # this visit
        t_i = times[i]

        for k in neighbor_indices:
            if k <= i:
                continue

            # REAL temporal exclusion:
            dt_seconds = abs((times[k] - t_i).total_seconds())
            if dt_seconds <= time_excl_seconds:
                continue

            if visibility_mask[k]:
                count += 1
                visibility_mask[k] = False

        final_pass_counts[i] = count

    return final_pass_counts, visibility_mask


def calculate_density_dbscan(x, y, timestamps, 
                             eps_meters=12,
                             time_exclusion_seconds=120):
    """
    DBSCAN spatial clustering + temporal revisit counting.

    x, y: coordinates in meters (WebMercator)
    timestamps: list of datetime objects

    returns:
      cluster_centers: (N_clusters, 2)
      cluster_pass_counts: length N_clusters
      labels: cluster ID for each point
    """

    points = np.column_stack((x, y))

    # --- 1. Spatial clustering ---
    db = DBSCAN(eps=eps_meters, min_samples=1).fit(points)
    labels = db.labels_
    n_clusters = labels.max() + 1

    cluster_pass_counts = np.zeros(n_clusters, dtype=int)
    cluster_centers = np.zeros((n_clusters, 2))

    # --- 2. For each cluster: count temporal revisits ---
    for c in range(n_clusters):
        idx = np.where(labels == c)[0]

        # sort by time
        idx_sorted = idx[np.argsort([timestamps[i] for i in idx])]

        count = 1  # at least one visit
        last_time = timestamps[idx_sorted[0]]

        for i in idx_sorted[1:]:
            dt = abs((timestamps[i] - last_time).total_seconds())

            if dt > time_exclusion_seconds:
                # this is a new visit
                count += 1
                last_time = timestamps[i]

        cluster_pass_counts[c] = count

        # representative center of cluster
        cluster_centers[c] = points[idx].mean(axis=0)

    return cluster_centers, cluster_pass_counts, labels
