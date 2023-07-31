import base64
from datetime import datetime
import json
import os
import random
import schedule
import string
import tkinter.font as tkFont
import threading
import PySimpleGUI as sg
import webbrowser

from images import cc_image, github_image, donate_image, logo_image
from ip_manager import IPManager
from logger import Logger



#
#
# FUNCTIONS' DEFINITIONS
#
#

def load_config(CONFIG_FILE_PATH) -> str:
    if os.path.exists(CONFIG_FILE_PATH):
        LOGGER.log('Config file exists.')
    else:
        LOGGER.log('Config file does not exists. Loading default config')
        CONFIG = {
            "GAS_SCRIPT_URL": "",
            "GAS_AUTHCODE": "",
            "IP_UPDATE_INTERVAL": 15,
            "MACHINE_NAME": "NetAnchored Device",
            "IP_SERVICE": "https://api.ipify.org",
            "USE_ENCRYPTED_DATABASE": False,
            "IP_ENCRYPTION_KEY": "",
            "MAX_UI_LOGS": 10
        }
        return CONFIG
        # raise Exception('Config file not found. Unable to run program.')


    LOGGER.log('Loading config...')
    with open(CONFIG_FILE_PATH, "r") as file:
        CONFIG = json.load(file)
    LOGGER.log('Config loaded.')
    return CONFIG

def save_config(config, CONFIG_FILE_PATH):
    LOGGER.log('Saving config...')
    with open(CONFIG_FILE_PATH, "w") as file:
        json.dump(config, file, indent=4)
    LOGGER.log('Config saved.')

def create_main_window_layout():
    # Text version    
    # Create a font with the same family and size but bold style
    default_font = sg.DEFAULT_FONT[0]
    default_size = sg.DEFAULT_FONT[1]
    bold_font = tkFont.Font(family=default_font, size=default_size, weight="bold", slant="italic")

    # Create network list, bold our current IP and LABEL
    network_frame_rows = []
    for i, entry in enumerate(IP_MANAGER.get_network()):
        network_frame_rows.append([sg.Text(entry[0], key=f'-CLIENT_{i}_LABEL-', expand_x=True, font=(bold_font if entry[1] == IP_MANAGER.get_current_ip() else None)), sg.Text(
            entry[1], key=f'-CLIENT_{i}_IP-', font=(bold_font if entry[1] == IP_MANAGER.get_current_ip() else None)), sg.Button("Copy", key=f'-BUTTON_COPY_IP_{i}-')])

    # ListBox version
    # network_frame_rows = [[sg.Listbox([f'{entry[0]}: {entry[1]}' for entry in network], key='-CLIENTS-', enable_events=True, size=(50, 10))]]

    network_frame = sg.Frame(
        'Network', network_frame_rows if len(network_frame_rows) > 0 else [[sg.Text('No data')]], key='-NETWORK_FRAME-', expand_x=True)

    upper_row_left_column = sg.Column([
        [network_frame],
        [sg.VPush()]
    ], expand_y=True, expand_x=True)

    log_rows = [row for row in LOGGER.get_logs_as_strings()]
    log_frame_rows = [[sg.Listbox(log_rows, size=(100, CONFIG['MAX_UI_LOGS']), key='-LOGS_LISTBOX-',
                                  disabled=False, no_scrollbar=True, expand_x=True)]]
    log_frame = sg.Frame('Log', log_frame_rows, expand_x=True)


    upper_row_right_column = sg.Column([
        [sg.Button('Update now', key='-BUTTON_FORCE_NETWORK_UPDATE-')],
        [sg.Button('Open config', key='-BUTTON_OPEN_CONFIG-')],
        # [sg.Button('Reload window', key='-BUTTON_RELOAD_WINDOW-')],
        # [sg.Text("Download TightVNC")],
        # [sg.Text("Open sheet in Google Drive")],
        [sg.VPush()],
        [sg.Image(data=cc_image, key='-CC_IMAGE-', enable_events=True)],
        [sg.Image(data=donate_image, key='-DONATE_IMAGE-', enable_events=True)],
        [sg.Image(data=github_image, key='-GITHUB_IMAGE-', enable_events=True)],
    ], element_justification='r', expand_x=True, expand_y=True)

    upper_row = [upper_row_left_column, upper_row_right_column]
    lower_row = [log_frame]

    status_bar = [sg.Text(f"{CONFIG['MACHINE_NAME']}: {IP_MANAGER.get_current_ip()}", key='-CURRENT_IP-'), sg.Push(), sg.Text(f"Time to next update: Unknown", key='-TIMER-')]

    layout = [
        upper_row,
        lower_row,
        [sg.HorizontalSeparator()],
        status_bar,
    ]

    return layout

def get_main_window():
    global PROGRAM_TITLE
    print('getting main window')

    window = sg.Window(f"{PROGRAM_TITLE}", create_main_window_layout(), icon=logo_image, resizable=False)
    return window

def splash_window():
    layout = [
        [sg.VPush()],
        [sg.Push(), sg.Text(PROGRAM_TITLE), sg.Push()],
        [sg.VPush()],
        [sg.Text("Fetching network, please wait a few seconds...")]
    ]
    window = sg.Window(f"{PROGRAM_TITLE} - Splash Screen", layout) # ! this is a blocking function until an event is triggered. Set a timeout (ms)
    window.read(timeout=0)
    return window

def open_config_window() -> bool:
    global IP_MANAGER

    layout = [
        [sg.Push(), sg.Text("Config", pad=(0, 50)), sg.Push()],
        [sg.Text('GAS script url:'), sg.Push(), sg.Input(CONFIG['GAS_SCRIPT_URL'], size=45, key='-GAS_SCRIPT_URL-')],
        [sg.Text('GAS AuthCode:'), sg.Push(), sg.Input(CONFIG['GAS_AUTHCODE'], size=45, key='-GAS_AUTHCODE-')],
        [sg.Text('Network update interval (mins):'), sg.Push(), sg.Input(str(CONFIG['IP_UPDATE_INTERVAL']), size=45, key='-IP_UPDATE_INTERVAL-')],
        [sg.Text('Machine label:'), sg.Push(), sg.Input(CONFIG['MACHINE_NAME'], size=45, key='-MACHINE_LABEL-')],
        [sg.Text('IP retrieval service:'), sg.Push(), sg.Input(CONFIG['IP_SERVICE'], size=45, key='-IP_SERVICE-')],
        [sg.Text('Use encrypted database:'), sg.Push(), sg.Checkbox('', default=bool(CONFIG['USE_ENCRYPTED_DATABASE']), key='-USE_ENCRYPTED_DATABASE-')],
        [sg.Text('Encryption key:'), sg.Push(), sg.Input(CONFIG['IP_ENCRYPTION_KEY'], size=45, key='-IP_ENCRYPTION_KEY-')],
        [sg.Text('Max logs to show:'), sg.Push(), sg.Input(str(CONFIG['MAX_UI_LOGS']), size=45, key='-MAX_UI_LOGS-')],
        [sg.Push(), sg.Text('Some settings require to restart for changes to take effect.', pad=(0, 50)), sg.Push()],
        [sg.Button('Discard changes'), sg.Button(
            'Save changes', key='-SAVE-', expand_x=True)],
    ]
    window = sg.Window(f'{PROGRAM_TITLE} - Config', layout) # ! this is a blocking function until an event is triggered.
    event, values = window.read()

    if event == '-SAVE-':
        CONFIG['GAS_SCRIPT_URL'] = values['-GAS_SCRIPT_URL-']
        CONFIG['GAS_AUTHCODE'] = values['-GAS_AUTHCODE-']
        CONFIG['IP_UPDATE_INTERVAL'] = int(values['-IP_UPDATE_INTERVAL-']) if int(values['-IP_UPDATE_INTERVAL-']) > 0 and int(values['-IP_UPDATE_INTERVAL-']) <= 60 else 15
        CONFIG['MACHINE_NAME'] = values['-MACHINE_LABEL-']
        CONFIG['IP_SERVICE'] = values['-IP_SERVICE-']
        CONFIG['USE_ENCRYPTED_DATABASE'] = values['-USE_ENCRYPTED_DATABASE-']
        CONFIG['IP_ENCRYPTION_KEY'] = values['-IP_ENCRYPTION_KEY-']
        CONFIG['MAX_UI_LOGS'] = int(values['-MAX_UI_LOGS-'])

        save_config(CONFIG, CONFIG_FILE_PATH)
        IP_MANAGER = IPManager(CONFIG, LOGGER, IP_MANAGER.get_network(), IP_MANAGER.get_current_ip())
        window.close()
        return True
    else:
        window.close()
        return False

def generate_random_authcode() -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(20))

def update_ip_manager():
    '''
        This is to allow the scheduled task to always call the current instance of IP_MANAGER
    '''
    global MAIN_WINDOW
    global IP_MANAGER

    IP_MANAGER.update()
    MAIN_WINDOW.close()
    MAIN_WINDOW = get_main_window()

def mt_ip_manager_update(IP_MANAGER):
    IP_MANAGER.update()

def main():
    global MAIN_WINDOW

    # if a new key is generated, we write it to the config.json
    if CONFIG['IP_ENCRYPTION_KEY'] == '':
        CONFIG['IP_ENCRYPTION_KEY'] = IP_MANAGER.encryption_key.decode()
        LOGGER.log(f'Saving new key: ', CONFIG['IP_ENCRYPTION_KEY'])
        with open('config.json', 'w') as config_file:
            json.dump(CONFIG, config_file, indent=4)

    # IP_MANAGER.update()

    sg.theme("DefaultNoMoreNagging")  # Choose a theme for the window

    # Event loop to process events and update the window
    first_loop = True

    while True:
        if first_loop == True:
            splash_w = splash_window()
            # IP_MANAGER.update()
            splash_w.close()
            MAIN_WINDOW = get_main_window()
            thread = threading.Thread(target=mt_ip_manager_update, args=(IP_MANAGER,))
            thread.start()
            first_loop = False

        event, values = MAIN_WINDOW.read(timeout=500) # ! this is a blocking function until an event is triggered. Set a timeout (ms)

        # if event != '__TIMEOUT__':
        #     LOGGER.log('Event: ', event)

        schedule.run_pending()

        # Update timer till next network update
        time_to_next_update = schedule.next_run() - datetime.now()
        m, s = divmod(time_to_next_update.total_seconds(), 60)
        MAIN_WINDOW.finalize()
        MAIN_WINDOW['-TIMER-'].update(value=f"Time to next update: {int(m):02}:{int(s):02}")

        # Exit the program when the window is closed
        if event == sg.WIN_CLOSED or event == None:
            break
        elif event == '-CC_IMAGE-':
            webbrowser.open('https://creativecommons.org/licenses/by-nc-sa/4.0/')
        elif event == '-GITHUB_IMAGE-':
            webbrowser.open('https://github.com/Rahjael/NetAnchor')
        elif event == '-DONATE_IMAGE-':
            # TODO implement this
            LOGGER.log('Donations are not yet implemented. Thank you anyways!')
        elif event == '-BUTTON_OPEN_CONFIG-':
            if open_config_window():  # opens config window and returns True if config is saved
                MAIN_WINDOW.close()
                MAIN_WINDOW = get_main_window()
        elif event == '-BUTTON_RELOAD_WINDOW-':
            MAIN_WINDOW.close()
            MAIN_WINDOW = get_main_window()
        elif event == '-BUTTON_FORCE_NETWORK_UPDATE-':
            MAIN_WINDOW['-BUTTON_FORCE_NETWORK_UPDATE-'].update('Updating...', disabled=True)
            thread = threading.Thread(target=mt_ip_manager_update, args=(IP_MANAGER,))
            thread.start()
            # Optionally, you can wait for the thread to complete using join()
            # thread.join()
        elif type(event) == str and event.startswith("-BUTTON_COPY_IP_"):
            index = int(event.split("_")[3].replace('-', ''))
            client_ip = MAIN_WINDOW[f'-CLIENT_{index}_IP-'].get()
            sg.clipboard_set(client_ip)
            LOGGER.log(f"IP '{client_ip}' copied to clipboard!")

        # Update logs listbox and refresh window no matter the event
        MAIN_WINDOW.finalize()
        log_rows = [row for row in LOGGER.get_logs_as_strings()]
        MAIN_WINDOW['-LOGS_LISTBOX-'].update(values=log_rows)
        MAIN_WINDOW.refresh()

        # See dev_readme.md for an explanation about this # TODO
        if not IP_MANAGER.has_network_been_given():
            MAIN_WINDOW.close()
            MAIN_WINDOW = get_main_window()

    # Close the window and end the program
    MAIN_WINDOW.close()





#
#
# RUNTIME
#
#


UI_VERSION = 'v0.1.0_RC'
GAS_SCRIPT_VERSION = 'vX.Y.Z'

CONFIG_FILE_PATH = os.path.join(os.getcwd(), 'config.json')

LOGGER = Logger()
CONFIG = load_config(CONFIG_FILE_PATH)
IP_MANAGER = IPManager(CONFIG, LOGGER)
MAIN_WINDOW = None # Main window is in the global scope so that it's easier to refresh it when a scheduled task runs

LOGGER.log('Program started')
PROGRAM_TITLE = f"NetAnchor - {UI_VERSION}"

# Schedule the updating task
schedule.every(CONFIG['IP_UPDATE_INTERVAL']).minutes.do(update_ip_manager)


if __name__ == "__main__":
    main()



# ip = '151.96.56.23'
# encrypted = IP_MANAGER.encrypt_str(ip)
# decrypted = IP_MANAGER.decrypt_str(encrypted)
# print('ip: ', ip)
# print('encrypted: ', encrypted, type(encrypted))
# print('decrypted: ', decrypted, type(decrypted))

