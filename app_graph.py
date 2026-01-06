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
    pattern = os.path.join("stats",f'stats-{user}_*.csv')

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
    pattern = os.path.join(user_dir, f'{district}-{user}.*.jpg')
    candidates = glob.glob(pattern)

    if not candidates:
        return None

    def extract_date(path):
        filename = os.path.basename(path)
        date_str = filename.split('.')[-2]
        return datetime.strptime(date_str, '%Y-%m-%d')

    return max(candidates, key=extract_date)

def latest_stats_image(base_dir: str, user: str, district: str) -> str | None:
    if district == 'Barcelona':
        pattern = os.path.join(base_dir,f'stats-{user}-*.png')
    else:
        pattern = os.path.join(base_dir,f'stats-{district}-{user}-*.png')

    candidates = glob.glob(pattern)
    if not candidates:
        print(pattern)
        return None

    def extract_date(path):
        filename = os.path.basename(path)
        date_str = filename.replace('.png', '').split('-')[-3:]
        return datetime.strptime('-'.join(date_str), '%Y-%m-%d')

    return max(candidates, key=extract_date)


def get_user_districts(user: str):
    user_dir = os.path.join(BASE_DIR, user)
    image_list = glob.glob(f'{user_dir}/*.jpg')

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
    def get_ratio(d):
        if stats_df is None:
            return 0.0
        row = stats_df[stats_df['districts'] == d]
        if row.empty:
            return 0.0
        percentage_street = row['percentage street'].iloc[0]
        return percentage_street if percentage_street else 0.0

    def set_main(d):
        path = image_path(d)
        if path:
            state['districts'] = d
            main_image.set_source(path)

            # Update bar height
            ratio = get_ratio(d)
            bar.style(f'height: {ratio}%')
            percent_label.set_text(f'{int(ratio)}%')

            # Print stats in terminal
            # print(f'[{user}] {d}: ratio={ratio:.2f}')
            stats_path = latest_stats_image('stats', user, d)
            if stats_image and stats_path:
                stats_image.set_source(stats_path)
            else:
                print("no stats image")
 

    ui.label(user.upper()).classes('text-xl font-bold mb-4')

    # ─────────────────────────────────────────
    # MAIN IMAGE (constrained width)
    # ─────────────────────────────────────────
    with ui.element('div').classes('mx-auto w-[800px] max-w-full'):

        # Grid: 2 columns (bar + image)
        with ui.element('div').classes('grid grid-cols-[40px_1fr] items-end gap-4'):

            # ---- BAR COLUMN ----
            with ui.element('div').classes('flex flex-col justify-end items-center h-full'):

                ui.label('Mapped').classes('text-xs mb-1 text-center')

                bar = ui.element('div').classes('bg-blue-500 w-full rounded')
                bar.style(f'height: {get_ratio(state["districts"])}%')

                percent_label = ui.label(
                    f'{int(get_ratio(state["districts"]))}%'
                ).classes('text-xs mt-1 text-center')

            # ---- MAIN IMAGE ----
            main_image = ui.image(first_path).classes(
                'w-full rounded-lg shadow'
            )

    # ─────────────────────────────────────────
    # STATS IMAGE (FULL WIDTH, CENTERED)
    # ─────────────────────────────────────────
    stats_path = latest_stats_image('stats', user, state['districts'])
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
    with ui.row().classes('gap-4 justify-center'):
        for d in district_names:
            thumb = image_path(d)
            if thumb:
                ui.image(thumb).classes(
                    'w-48 cursor-pointer rounded hover:scale-105 transition'
                ).on('click', lambda d=d: set_main(d))

#---------------------------
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

    def set_district(d):
        state['districts'] = d
        for user, img in main_images.items():
            path = latest_image_path(BASE_DIR, user, d)
            if path:
                img.set_source(path)

    ui.label('Comparison').classes('text-xl font-bold text-center')

    # ---- ROW: force side by side ----
    with ui.row().classes('w-full justify-center items-start gap-4'):

        for user in users:
            # each column contains the user label and image
            with ui.column().classes('items-center'):

                ui.label(user.upper()).classes('text-lg font-bold mb-2')

                path = latest_image_path(BASE_DIR, user, state['districts'])
                if not path:
                    ui.label('No image')
                    continue

                # ✅ Force image width < 50% of window width (adaptive)
                main_images[user] = ui.image(path).classes(
                    'w-[45vw] max-w-[45vw]'
                )

    ui.separator()

    # district selector (shared)
    ui.label('Select district').classes('text-center')

    with ui.row().classes('gap-4 justify-center'):
        for d in common_districts:
            ui.button(d).on('click', lambda d=d: set_district(d))

# --------------------------------------------------
# Main page (tabs)
# --------------------------------------------------

@ui.page('/')
def main_page():

    with ui.tabs().classes('w-full') as tabs:
        hubert_tab = ui.tab('Hubert')
        pa_tab = ui.tab('PA')
        compare_tab = ui.tab('Comparison')

    with ui.tab_panels(tabs, value=hubert_tab).classes('w-full'):
        with ui.tab_panel(hubert_tab):
            user_view('hubert')

        with ui.tab_panel(pa_tab):
            user_view('pa')

        with ui.tab_panel(compare_tab):
            comparison_view(('hubert', 'pa'))


ui.run()
