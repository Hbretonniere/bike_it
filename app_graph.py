from nicegui import ui
import os
import glob
from datetime import datetime
import pandas as pd


BASE_DIR = 'plots'
USERS = ['hubert', 'pa']


# --------------------------------------------------
# Utilities
# --------------------------------------------------


def latest_stats_df(base_dir: str, user: str) -> pd.DataFrame | None:
    pattern = os.path.join("stats",user,f'stats-{user}_*.csv')

    candidates = glob.glob(pattern)
    # print(candidates)
    if not candidates:
        return None

    def extract_date(path):
        filename = os.path.basename(path)
        date_str = filename.split('_')[-1].replace('.csv', '')
        return datetime.strptime(date_str, '%Y-%m-%d')

    latest_file = max(candidates, key=extract_date)
    return pd.read_csv(latest_file)


def latest_image_path(base_dir: str, user: str, district: str) -> str | None:
    user_dir = os.path.join(base_dir, user)
    pattern = os.path.join(user_dir, f'{district}-{user}*.png')
    candidates = glob.glob(pattern)
    
    def extract_date(path):
        filename = os.path.basename(path)
        date_str = filename.split('.')[-2]
        return datetime.strptime(date_str, '%Y-%m-%d')
    
    if not candidates:
        return None
    else:
        if len(candidates) == 1:
            latest_picture = candidates[0]
        else:
            latest_picture = max(candidates, key=extract_date)

    return latest_picture

def latest_stats_image(base_dir: str, user: str, district: str) -> str | None:
    if district == 'Barcelona':
        pattern = os.path.join(base_dir,user,f'stats-{user}.png')
    else:
        pattern = os.path.join(base_dir,user,f'stats-{district}-{user}.png')
  #  print("pattern",pattern)
    candidates = glob.glob(pattern)
    if not candidates:
        return None

    return candidates[0]


def get_user_districts(user: str):
    user_dir = os.path.join(BASE_DIR, user)
    image_list = glob.glob(f'{user_dir}/*.png')

    districts = []
    for p in image_list:
        filename = os.path.basename(p)
        districts.append(filename.split('-')[0])

    return sorted(set(districts))


def mapped_ratio(df: pd.DataFrame, district: str) -> float | None:
    row = df[df['district'] == district]
    if row.empty:
        return None

    mapped = row['number of mapped streets'].iloc[0]
    total = row['total number of streets'].iloc[0]

    if total == 0:
        return 0.0

    return mapped / total

# --------------------------------------------------
# User view (single user tab)
# --------------------------------------------------
def user_view(user: str):
    district_names = get_user_districts(user)

    if not district_names:
        ui.label(f'No images for {user}')
        return

    # Load stats ONCE
    stats_df = latest_stats_df('.', user)

    state = {'districts': district_names[0]}

    def image_path(d):
        return latest_image_path(BASE_DIR, user, d)

    first_path = image_path(state['districts'])
    if first_path is None:
        ui.label('No image found')
        return

    # Safe ratio getter
    def get_street_ratio(d):
        if stats_df is None:
            return 0.0
        row = stats_df[stats_df['districts'] == d]
        if row.empty:
            return 0.0
        percentage_street = row['percentage street'].iloc[0]
        return percentage_street if percentage_street else 0.0
    
        # Safe ratio getter
    def get_segments_ratio(d):
        if stats_df is None:
            return 0.0
        row = stats_df[stats_df['districts'] == d]
        if row.empty:
            return 0.0
        percentage_street = row['percentage segments'].iloc[0]
        return percentage_street if percentage_street else 0.0

    def set_main(d):
        path = image_path(d)
        if path:
            state['districts'] = d
            main_image.set_source(path)

            # Update bar height
            ratio_streets = get_street_ratio(d)
            bar1.style(f'height: {ratio_streets}%')
            percent_label1.set_text(f'{int(ratio_streets)}%')

            ratio_segments = get_segments_ratio(d)
            bar2.style(f'height: {ratio_segments}%')
            percent_label2.set_text(f'{int(ratio_segments)}%')

            stats_path = latest_stats_image('stats/', user, d)
            if stats_image and stats_path:
                stats_image.set_source(stats_path)
            else:
                print("no stats image",stats_path,stats_image)
 

    ui.label(user.upper()).classes('text-xl font-bold mb-4')

    # ─────────────────────────────────────────
    # MAIN IMAGE (constrained width)
    # ─────────────────────────────────────────
    with ui.element('div').classes('mx-auto w-[600px] max-w-full'):

        # Grid: bars + image
        with ui.element('div').classes(
            'grid grid-cols-[90px_1fr] items-end gap-4'
        ):

            # ── BAR GROUP (2 bars side by side) ──
            with ui.element('div').classes(
                'grid grid-cols-2 gap-3 items-end h-full mr-4'
            ):

                # ===== BAR 1 =====
                with ui.element('div').classes(
                    'flex flex-col items-center justify-end h-full'
                ):
                    bar1 = ui.element('div').classes('bg-blue-400 w-full rounded')
                    bar1.style(f'height: {get_street_ratio(state["districts"])}%')

                    percent_label1 = ui.label(
                        f'{int(get_street_ratio(state["districts"]))}%'
                    ).classes('text-xs mt-1')

                    ui.label('Streets').classes('text-xs mt-1 text-center font-semibold')

                # ===== BAR 2 =====
                with ui.element('div').classes(
                    'flex flex-col items-center justify-end h-full'
                ):
                    bar2 = ui.element('div').classes(
                        'bg-red-300 w-full rounded'
                    )
                    bar2.style(f'height: {get_segments_ratio(state["districts"])}%')

                    percent_label2 = ui.label(
                        f'{int(get_segments_ratio(state["districts"]))}%'
                    ).classes('text-xs mt-1')

                    ui.label('Segments').classes(
                        'text-xs mt-1 text-center font-semibold'
                    )

            # ── MAIN IMAGE ──
            main_image = ui.image(first_path).classes(
                'w-full rounded-lg shadow'
            )

    # ─────────────────────────────────────────
    # STATS IMAGE (FULL WIDTH, CENTERED)
    # ─────────────────────────────────────────
    stats_path = latest_stats_image('stats', user, state['districts'])
 #   print("stats_path",stats_path)
    stats_image = None

    if stats_path:
        with ui.element('div').classes('w-full flex justify-center'):
            stats_image = ui.image(stats_path).classes(
                'w-full max-w-[1400px] mt-6 rounded shadow'
            )

    ui.separator()

    # ─────────────────────────────────────────
    # THUMBNAILS
    # ─────────────────────────────────────────
    with ui.row().classes('gap-6 justify-center'):
        for d in district_names:
            thumb = image_path(d)
            if thumb:
                with ui.column().classes('items-center cursor-pointer').on('click', lambda d=d: select_thumbnail(d)):
                    ui.label(d.replace('_', ' ')).classes('text-2xl font-bold text-center text-blue-500')
                    ui.image(thumb).classes(
                        'w-80 object-cover rounded hover:scale-105 transition'
                    ).style(
                        'object-position: center 10%;'
                    )

                # callback
                def select_thumbnail(d):
                    set_main(d)  # update main image and bars
                    ui.run_javascript("window.scrollTo({top: 0, behavior: 'smooth'});")


# ---------------------------
# Comparison view (synchronized)
# --------------------------------------------------

def comparison_view(users=('hubert', 'pa')):
    # find common districts
    districts = [set(get_user_districts(u)) for u in users]
    common_districts = sorted(set.intersection(*districts))

    if not common_districts:
        ui.label('No common districts')
        return

    state = {'districts': common_districts[0]}
    main_images = {}

    stats = {u: latest_stats_df('.', u) for u in users}

    def get_ratio(user, district):
        """Return percentage street mapped for user/district (0-100)."""
        df = stats.get(user)
        if df is None:
            return 0.0
        row = df[df['districts'] == district]
        if row.empty:
            return 0.0
        return row['percentage street'].iloc[0] or 0.0


    with ui.row().classes('w-full justify-center mb-8'):
        path_comp = latest_image_path(BASE_DIR, 'comparison', state['districts'])
        main_images['comparison'] = ui.image(path_comp).classes(
            'w-[50vw] max-w-[800px] '
        )

    # ── GRID: Left Image | Bars | Right Image ──
    with ui.element('div').classes(
        'grid grid-cols-[1fr_80px_1fr] items-end gap-6 w-full justify-center'
    ):

        # ── LEFT IMAGE (User 1) ──
        with ui.column().classes('items-center'):
            user = users[0]
            ui.label(user.upper()).classes('text-lg font-bold mb-2')
            path = latest_image_path(BASE_DIR, user, state['districts'])
            main_images[user] = ui.image(path).classes('w-[30vw] max-w-[30vw]')

        # ── BARS (CENTER) ──
        with ui.element('div').classes('grid grid-cols-2 gap-4 items-end h-full'):
            bars = {}
            for user, color in zip(users, ['bg-blue-400', 'bg-red-400']):
                with ui.column().classes('items-center justify-end h-full'):
                    bar = ui.element('div').classes(f'{color} w-full rounded transition-all duration-300')
                    bar.style(f'height: {get_ratio(user, state["districts"])}%')
                    percent_label = ui.label(f'{int(get_ratio(user, state["districts"]))}%').classes('text-xs mt-1')
                    ui.label(user.upper()).classes('text-xs font-semibold mt-1')
                    bars[user] = {'bar': bar, 'label': percent_label}

        # ── RIGHT IMAGE (User 2) ──
        with ui.column().classes('items-center'):
            user = users[1]
            ui.label(user.upper()).classes('text-lg font-bold mb-2')
            path = latest_image_path(BASE_DIR, user, state['districts'])
            main_images[user] = ui.image(path).classes('w-[30vw] max-w-[30vw]')

    ui.separator().classes('my-4')

    # ── DISTRICT SELECTOR ──
    ui.label('Select district').classes('text-center mb-2 font-semibold')
    with ui.row().classes('gap-4 justify-center'):
        for d in common_districts:
            ui.button(d.replace('_', ' '), on_click=lambda d=d: set_district(d)).classes('px-4')

    # ── UPDATE FUNCTION ──
    def set_district(d):
        state['districts'] = d
        for user, img in main_images.items():
            path = latest_image_path(BASE_DIR, user, d)
            if path:
                img.set_source(path)

        # update bars and percentage labels
        for user in users:
            ratio = get_ratio(user, d)
            bars[user]['bar'].style(f'height: {ratio}%')
            bars[user]['label'].set_text(f'{int(ratio)}%')
# --------------------------------------------------
# Main page (tabs)
# --------------------------------------------------

@ui.page('/')
def main_page():

    with ui.tabs().classes('w-full') as tabs:
        hubert_tab = ui.tab('Hubert').classes('text-xxl font-semibold')
        pa_tab = ui.tab('PA').classes('text-xl font-semibold')
        compare_tab = ui.tab('Comparison').classes('text-xl font-semibold')


    with ui.tab_panels(tabs, value=hubert_tab).classes('w-full'):
        with ui.tab_panel(hubert_tab):
            user_view('hubert')

        with ui.tab_panel(pa_tab):
            user_view('pa')

        with ui.tab_panel(compare_tab):
            comparison_view(('hubert', 'pa'))


ui.run()
