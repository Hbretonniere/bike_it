import geopandas as gpd
from scipy.spatial import KDTree
import gpxpy
import glob
# from shapely.geometry import LineString
import matplotlib.pyplot as plt
# from shapely.geometry import Point
import contextily as ctx
# import matplotlib.animation as animation
import numpy as np


colors = {'hubert': 'cornflowerblue',
          'pa': 'tomato'}


def load_long_lat(user, n_segments=None):

    # Parsing an existing file:
    # -------------------------
    file = glob.glob(f'segments/{user}/*.gpx')[0]
    gpx_file = open(file, 'r')

    gpx = gpxpy.parse(gpx_file)
    track = []
    lats_tot = []
    longs_tot = []
    # xs_nc = []
    # ys_nc = []
    # cuts = []
    pts = 0
    for track_i in gpx.tracks:
        for s, segment in enumerate(track_i.segments):
            if (user == 'hubert') & (s in [1, 6]):
                continue
            if n_segments:
                if s >= n_segments:
                    return track, longs_tot, lats_tot
            longs = []
            lats = []
            for point in segment.points:
                lats.append(point.latitude)
                longs.append(point.longitude)
                pts += 1
            gdf_points = gpd.GeoDataFrame(
                geometry=gpd.points_from_xy(longs, lats),
                crs="EPSG:4326")
            gdf_points = gdf_points.to_crs(epsg=3857)
            xs_merc, ys_merc = zip(*[(p.x, p.y) for p in gdf_points.geometry])
            xs_merc = np.array(xs_merc)
            ys_merc = np.array(ys_merc)
            track.append({'lats': ys_merc,
                          'longs': xs_merc})
            longs_tot.extend(xs_merc)
            lats_tot.extend(ys_merc)
    return track, longs_tot, lats_tot


def static_plot(track, longs_tot, lats_tot, user, fig, ax,
                x_min_global, x_max_global, y_min_global, y_max_global,
                step, round,
                with_map,
                map_style,
                colors,
                lws={'hubert': 5,
                     'pa': 5}):
    lw = 0.8
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

    for segment in track:
        # xs = np.round(np.array(longs_tot['longs'][::step])/100, round)*100
        # ys = np.round(np.array(segment['lats'][::step])/0.1, round)*10
        # xs = np.round(np.array(segment['longs'][::step]), round)
        lats_tot = np.array(segment['lats'][::step])
        longs_tot = np.array(segment['longs'][::step])
        ax.plot(longs_tot, lats_tot, color=colors[user], lw=lws[user]/10, alpha=0.7)

    return fig, ax, x_min_global, x_max_global, y_min_global, y_max_global,


def compute_and_plot_track(users, step=2, round=10, with_map=True,
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
        track, longs_tot, lats_tot = load_long_lat(user, n_segments=None)
        if not map_style:
            with_map = False
        else:
            with_map = with_map

        fig, ax, x_min_global, x_max_global, y_min_global, y_max_global, = \
            static_plot(track, longs_tot, lats_tot,
                        user, fig, ax,
                        x_min_global, x_max_global,
                        y_min_global, y_max_global,
                        step, round,
                        with_map,
                        map_style)
        if savefig:
            plt.savefig(f'new_track_{user}{suffix}.png', dpi=dpi)
    return longs_tot, lats_tot


def plot_track(users,
               gpx_infos,
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

        track = gpx_infos[user]['track']
        longs_tot = gpx_infos[user]['longs']
        lats_tot = gpx_infos[user]['lats']
        fig, ax, x_min_global, x_max_global, y_min_global, y_max_global, = \
            static_plot(track, longs_tot, lats_tot,
                        user, fig, ax,
                        x_min_global, x_max_global,
                        y_min_global, y_max_global,
                        step, round,
                        with_map,
                        map_style,
                        colors,
                        lws)
        if savefig:
            plt.savefig(f'new_track_{user}{suffix}.png', dpi=dpi)


def calculate_track_density_no_mask(easting, northing,
                                    radius_meters=50.0, time_excl_window=50):
    """
    Calculates the passage density for each point,
    assuming coordinates are in a
    meter-based Projected Coordinate Syste
    (e.g., UTM Easting/Northing).

    :param easting: List or array of Easting coordinates (X).
    :param northing: List or array of Northing coordinates (Y).
    :param radius_meters: The spatial distance (in meters)
                         for considering points as "same road".
    :param time_excl_window: The number of indices (points) before and after
                             to exclude from the count.
    :return: A numpy array of pass counts for each point.
    """
    if len(easting) != len(northing) or len(easting) == 0:
        return np.array([])

    # Combine X and Y coordinates (Easting, Northing)
    points = np.column_stack((easting, northing))

    # --- 1. Build KD-Tree ---
    tree = KDTree(points)

    # The search radius 'r' is simply the required distance in meters.
    # The KD-Tree's Euclidean distance calculation is accurate here.
    search_radius = radius_meters

    # --- 2. Iterate, Query, and Filter ---
    n_points = len(points)
    pass_counts = np.zeros(n_points, dtype=int)

    for i in range(n_points):
        # Spatial Query: Find all point indices
        # within the search_radius (5.0 meters)
        neighbor_indices = tree.query_ball_point(points[i], r=search_radius)

        # Time-based Exclusion: Define the window of indices to ignore
        min_idx = max(0, i - time_excl_window)
        max_idx = min(n_points - 1, i + time_excl_window)

        # We pre-calculate the exclusion set for fast lookups
        exclusion_set = set(range(min_idx, max_idx + 1))

        final_count = 0
        for neighbor_idx in neighbor_indices:
            # Only count the neighbor if it's NOT within
            # the temporal exclusion window
            if neighbor_idx not in exclusion_set:
                final_count += 1

        # Add 1 to include the point itself as a "pass"
        pass_counts[i] = final_count + 1

    return pass_counts


def static_plot_density_no_mask(
        track, longs_tot, lats_tot, counts, user, fig, ax,
        x_min_global, x_max_global, y_min_global, y_max_global,
        step, round):

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

    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Voyager)
    ax.set_axis_off()
    seg_start = 0
    for segment in track:
        lats_tot = np.array(segment['lats'][::step])
        longs_tot = np.array(segment['longs'][::step])
        seg_end = seg_start + len(lats_tot)
        ax.scatter(longs_tot, lats_tot,
                   c=counts[seg_start:seg_end], s=1,
                   cmap='Blues', vmin=0, vmax=3)
        seg_start = seg_end
    fig.savefig(
        f'{user}_density_mo_mask_step-{step}_round-{round}.png', dpi=700)
    return fig, ax, x_min_global, x_max_global, y_min_global, y_max_global


def plot_track_density_no_mask(users):
    fig, ax = plt.subplots(figsize=(8, 8))
    x_min_global, x_max_global, y_min_global, y_max_global = \
        np.inf, -np.inf, np.inf, -np.inf
    for user in users:
        track, xs_tot, ys_tot = load_long_lat(user, n_segments=None)
        pass_counts = calculate_track_density_no_mask(
            ys_tot, xs_tot, radius_meters=10, time_excl_window=1,)
        fig, ax, x_min_global, x_max_global, y_min_global, y_max_global = \
            static_plot_density_no_mask(
                track, xs_tot, ys_tot, pass_counts, user, fig, ax,
                x_min_global, x_max_global, y_min_global, y_max_global,
                step=1, round=5)
    plt.show()
    return xs_tot, ys_tot


def calculate_track_density_and_mask(easting, northing, radius_meters,
                                     time_excl_window=10):
    """
    Calculates the passage density and a visibility mask for each point,
    ensuring counts are aggregated onto the *first* point of a segment,
    and subsequent passages are masked.

    :param easting: List or array of Easting coordinates (X).
    :param northing: List or array of Northing coordinates (Y).
    :param radius_meters: The spatial distance (in meters)
    for considering points as "same road".
    :param time_excl_window: The number of indices (points) before and after
                             to exclude from the count.
    :return: A tuple (final_pass_counts, visibility_mask).
    """
    if len(easting) != len(northing) or len(easting) == 0:
        return np.array([]), np.array([])

    points = np.column_stack((easting, northing))
    n_points = len(points)

    # --- 1. Build KD-Tree ---
    tree = KDTree(points)
    search_radius = radius_meters

    # --- 2. Initialize Outputs ---
    # We only need the final outputs, initialized to zero/True
    final_pass_counts = np.zeros(n_points, dtype=int)
    visibility_mask = np.ones(n_points, dtype=bool)

    # --- 3. Single Pass Aggregation (Combines original Steps 3 & 4 logic) ---
    for i in range(n_points):
        # Only proceed if this point hasn't been masked by an earlier neighbor
        if not visibility_mask[i]:
            continue

        # If we reach here, point 'i' is the first point of its segment
        # (or the first point of a new passage). It is VISIBLE.

        # Spatial Query: Find all point indices within the search_radius
        # Note: Includes point i itself.
        neighbor_indices = tree.query_ball_point(points[i], r=search_radius)

        # Initialize count with point 'i' itself (1 pass)
        count = 1

        # Check all subsequent neighbors (k > i)
        for k in neighbor_indices:

            # --- Condition for Re-Passage ---
            # 1. k must be later than i (k > i)
            # 2. k must be temporally distant from i (k - i > time_excl_window)

            if k > i and k - i > time_excl_window:
                # Point k is a subsequent,
                # distant passage to the same location.

                # Check if point k was *already* claimed
                #  and masked by an earlier point j < i.
                # If visibility_mask[k] is already False,
                #  it means a point j (i < j < k)
                # already took the credit. We skip it to avoid double-counting.
                if visibility_mask[k]:
                    # This point 'k' is a valid re-visit
                    #  that hasn't been claimed yet.
                    count += 1

                    # MASK IT: Ensure this subsequent
                    #  passage point 'k' is hidden.
                    visibility_mask[k] = False

        # Assign the total aggregated count to
        # the *visible* representative point 'i'
        final_pass_counts[i] = count

    return final_pass_counts, visibility_mask


def static_plot_density_mask(
        track, longs_tot, lats_tot, counts, mask, user, fig, ax,
        x_min_global, x_max_global, y_min_global, y_max_global,
        step, round):

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

    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Voyager)
    ax.set_axis_off()
    seg_start = 0
    # print(np.shape(mask))
    # print(np.shape(longs_tot))
    # print(np.shape(counts))
    for segment in track:
        lats_tot = np.array(segment['lats'][::step])
        longs_tot = np.array(segment['longs'][::step])
        seg_end = seg_start + len(lats_tot)
        # print(np.shape(lats_tot))
        # print(np.shape(mask[seg_start:seg_end]))
        lats_tot *= mask[seg_start:seg_end]
        longs_tot *= mask[seg_start:seg_end]
        ax.scatter(longs_tot, lats_tot,
                   c=counts[seg_start:seg_end], s=0.5, alpha=1,
                   cmap='Reds',
                   vmin=0, vmax=5,
                   marker='o')

        seg_start = seg_end
    fig.savefig(
        f'{user}_density_mask_step-{step}_round-{round}.png', dpi=500)
    return fig, ax, x_min_global, x_max_global, y_min_global, y_max_global


def plot_track_density_mask(users, step, radius_meters, time_excl_window):
    fig, ax = plt.subplots(figsize=(8, 8))
    x_min_global, x_max_global, y_min_global, y_max_global = \
        np.inf, -np.inf, np.inf, -np.inf
    for user in users:
        track, xs_tot, ys_tot = load_long_lat(user, n_segments=None)
        pass_counts, visibility_mask = calculate_track_density_and_mask(
            ys_tot[::step], xs_tot[::step], radius_meters, time_excl_window)
        fig, ax, x_min_global, x_max_global, y_min_global, y_max_global = \
            static_plot_density_mask(
                track, xs_tot, ys_tot, pass_counts, visibility_mask,
                user, fig, ax,
                x_min_global, x_max_global, y_min_global, y_max_global,
                step=step, round=5)
    plt.show()
    return xs_tot, ys_tot
