from nicegui import ui
import os
import glob
from datetime import datetime

BASE_DIR = 'plots'
USERS = ['hubert', 'pa']


# --------------------------------------------------
# Utilities
# --------------------------------------------------

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


def get_user_districts(user: str):
    user_dir = os.path.join(BASE_DIR, user)
    image_list = glob.glob(f'{user_dir}/*.jpg')

    districts = []
    for p in image_list:
        filename = os.path.basename(p)
        districts.append(filename.split('-')[0])

    return sorted(set(districts))


# --------------------------------------------------
# User view (single user tab)
# --------------------------------------------------

def user_view(user: str):
    district_names = get_user_districts(user)

    if not district_names:
        ui.label(f'No images for {user}')
        return

    state = {'district': district_names[0]}

    def image_path(d):
        return latest_image_path(BASE_DIR, user, d)

    def set_main(d):
        path = image_path(d)
        if path:
            state['district'] = d
            main_image.set_source(path)

    ui.label(user.upper()).classes('text-xl font-bold')

    with ui.column().classes('items-center'):
        main_image = ui.image(
            image_path(state['district'])
        ).classes('max-w-3xl w-full rounded-lg shadow')

        ui.separator()

        with ui.row().classes('gap-4 justify-center'):
            for d in district_names:
                thumb = image_path(d)
                if thumb:
                    ui.image(thumb).classes(
                        'w-48 cursor-pointer rounded hover:scale-105 transition'
                    ).on('click', lambda d=d: set_main(d))


# --------------------------------------------------
# Comparison view (synchronized)
# --------------------------------------------------

def comparison_view(users=('hubert', 'pa')):

    # find common districts
    districts = [set(get_user_districts(u)) for u in users]
    common_districts = sorted(set.intersection(*districts))

    if not common_districts:
        ui.label('No common districts')
        return

    state = {'district': common_districts[0]}
    main_images = {}

    def set_district(d):
        state['district'] = d
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

                path = latest_image_path(BASE_DIR, user, state['district'])
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
