from nicegui import ui
from gui_utils import (plot_track,
                       load_long_lat,
                    #    calculate_track_density_and_mask,
                       calculate_density_dbscan)
import contextily as cx


MAPS_OPTIONS = {
    'Light (grey)': 'CartoDB.Positron',
    'OpenStreetMap (Standard)': 'OpenStreetMap.Mapnik',
    'Satellite': 'Esri.WorldImagery',
    # 'Topographic': 'Stamen.Terrain',
    # 'High Contrast B&W': 'Stamen.Toner',
    'Dark Mode': 'CartoDB.DarkMatter',
    # '(Elevation Focused': 'OpenTopoMap',
    'Detailed Streets': 'Esri.WorldStreetMap'  # Detailed street-level map
}
COLORS = ['blue', 'black', 'white', 'darkblue', 'red', 'tomato', 'forestgreen']


def get_map_style_object(map_path: str):
    """
    """
    base = cx.providers

    # Split the path by dots (e.g., ['CartoDB', 'Positron'])
    parts = map_path.split('.')

    # Recursively use getattr to navigate the structure
    map_object = base
    for part in parts:
        try:
            map_object = getattr(map_object, part)
        except AttributeError:
            raise ValueError(f"map not found: {map_path}",
                             f"(part: {part}). Check contextily version.")

    # This returns the actual map object reference
    return map_object


density = False
selected_names = []
gpx_infos = {}
gpx_density_infos = {}
colors = {'hubert': 'cornflowerblue',
          'pa': 'tomato'}
lws = {'hubert': 7,
       'pa': 7}
initial_selection_key = list(MAPS_OPTIONS.keys())[0]
selected_map_path = MAPS_OPTIONS[initial_selection_key]
current_map_object = get_map_style_object(selected_map_path)


def handle_map_change(event):
    global selected_maps_path, current_map_object
    selected_display_name = event.value
    selected_map_path = MAPS_OPTIONS[selected_display_name]
    current_map_object = get_map_style_object(selected_map_path)
    display_map.refresh(density)


def handle_hubert_color_change(event):
    colors['hubert'] = event.value
    display_map.refresh(density)


def handle_pa_color_change(event):
    colors['pa'] = event.value
    display_map.refresh(density)


def handle_hubert_lw_change(event):
    lws['hubert'] = event.value


def handle_density_plot_change(event):
    global density
    density = event.value
    display_map.refresh(density)


def update_gpx(name: str, is_checked: bool):
    """
    Updates the selected_names list based on the checkbox state.
    """
    if is_checked and name not in selected_names:
        selected_names.append(name)
        for name in selected_names:
            if name not in gpx_infos.keys():
                gpx_infos[name] = {}
                track, longs_tot, lats_tot, times_tot = load_long_lat(
                    name,
                    n_segments=None)
                gpx_infos[name]['longs'] = longs_tot
                gpx_infos[name]['lats'] = lats_tot
                gpx_infos[name]['track'] = track

            if name not in gpx_density_infos.keys():
                gpx_density_infos[name] = {}
                track, longs_tot, lats_tot, times_tot = load_long_lat(
                    name,
                    n_segments=None)
                # pass_counts, visibility_mask = \
                #     calculate_track_density_and_mask(
                #         lats_tot, longs_tot, times_tot,
                #         radius_meters=20, time_excl_seconds=60*5)
                centers, pass_counts, labels = calculate_density_dbscan(
                    longs_tot, lats_tot, times_tot,
                    eps_meters=12,
                    time_exclusion_seconds=120,
                )
                gpx_density_infos[name]['longs'] = longs_tot
                gpx_density_infos[name]['lats'] = lats_tot
                gpx_density_infos[name]['times_tot'] = times_tot
                gpx_density_infos[name]['track'] = track
                gpx_density_infos[name]['counts'] = pass_counts
                gpx_density_infos[name]['centers'] = centers
                gpx_density_infos[name]['labels'] = labels

        display_map.refresh(density)

    elif not is_checked and name in selected_names:
        selected_names.remove(name)
        display_map.refresh(density)


@ui.refreshable
def display_map(density):
    map = current_map_object
    if density:
        print('using density infos')
        gpx_to_use = gpx_density_infos
    else:
        print('using raw infos')
        gpx_to_use = gpx_infos
    if len(selected_names) == 0:
        ui.label("Please select at least one run type to display.").classes(
            'text-lg text-gray-500 italic')
    else:
        with ui.row().classes('justify-center w-full p-4').style('margin-top: -80px;'):
            with ui.pyplot(figsize=(10, 10)):
                plot_track(selected_names,
                           gpx_to_use,
                           density,
                           colors,
                           lws=lws,
                           step=2,
                           round=5,
                           with_map=True,
                           savefig=False,
                           nicegui=True,
                           map_style=map)


with ui.column().classes('items-center w-full p-4'):

    # --- Card with user/color selection and map selector in header ---
    with ui.card().classes('p-4 w-full max-w-3xl shadow-lg'):
        with ui.row().classes('justify-between items-center mb-2'):
            ui.label("User Selection & Colors").classes('text-lg font-bold')
            with ui.row().classes('items-center gap-2'):
                ui.label("Map style").classes('text-sm text-gray-600')
                ui.select(
                    options=list(MAPS_OPTIONS.keys()),
                    value=initial_selection_key,
                    on_change=handle_map_change
                ).classes('w-48')

        ui.separator()

        ui.checkbox(
            'Density plot',
            value=False,
            on_change=handle_density_plot_change
            )
        ui.separator()

        # Hubert section
        with ui.grid(columns=4).classes('gap-4 items-center mt-4'):
            ui.checkbox(
                'Hubert',
                value=True,
                on_change=lambda e: update_gpx('hubert', e.value)
            )
            ui.label("Hubert Color").classes('text-sm text-gray-600')
            ui.select(
                options=COLORS,
                on_change=handle_hubert_color_change,
            ).classes('w-full col-span-2')

            # ui.label("Line thickness Level").classes('text-sm text-gray-600 mr-2')
            # ui.slider(
            #     min=0.5,
            #     max=10,
            #     step=1,
            #     value=1,
            #     on_change=handle_hubert_lw_change
            # ).classes('w-full')

        # Pierre-Antoine section (new grid → new row)
        with ui.grid(columns=4).classes('gap-4 items-center mt-2'):
            ui.checkbox(
                'Pierre-Antoine',
                value=False,
                on_change=lambda e: update_gpx('pa', e.value)
            )
            ui.label("PA Color").classes('text-sm text-gray-600')
            ui.select(
                options=COLORS,
                on_change=handle_pa_color_change,
            ).classes('w-full col-span-2')

update_gpx('hubert', True)
display_map(density)

ui.page.title = "Bike it"
ui.run()
