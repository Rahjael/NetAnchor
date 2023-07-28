import json
import os
import schedule
import time
from tqdm import tqdm
import PySimpleGUI as sg

from ip_manager import IPManager

config_file_path = os.path.join(os.getcwd(), 'config.json')



def load_config(config_file_path) -> str:
  if os.path.exists(config_file_path):
    print('Config file exists.')
  else:
    raise Exception('Config file not found. Unable to run program.')

  print('Loading config...')
  with open(config_file_path, "r") as file:
    CONFIG = json.load(file)
  print('Config loaded.')
  return CONFIG

def save_config(config, config_file_path):
    """
    Save the CONFIG dictionary to a JSON file.
    """
    print('Saving config...')
    with open(config_file_path, "w") as file:
        json.dump(config, file, indent=4)
    print('Config saved.')


CONFIG = load_config(config_file_path)

print('Program started')


PROGRAM_TITLE = "NetAnchor - v0.1.0"











# MOCK_NETWORK = [
#   ['OFFICE_PC', '151.83.33.126'],
#   ['MAIN_PC', '151.83.58.105'],
#   ['LAPTOP', '93.47.230.0'],
#   ['iOS_LAPTOP', '151.41.127.145'],
#   ['NAS', '151.40.127.63'],
#   ['HOME_DESKTOP', '151.83.20.187'],
#   ['SELF_HOSTED_WEBSERVER', '151.83.42.33']
# ]



MOCK_NETWORK = [
  ['Network', 'empty']
]

MOCK_LOGS = [
   "Connection established.",
   "blablabla info",
   "something went wrong, pc will now explode"
]


def create_main_window_layout(network):
    """
    Create the layout for the GUI window.
    """

    print('Creating layout for network: ', network)

    # Text version
    network_frame_rows = []
    for i, entry in enumerate(network):
      network_frame_rows.append([sg.Text(entry[0], key=f'-CLIENT_{i}_LABEL-', expand_x=True), sg.Text(entry[1], key=f'-CLIENT_{i}_IP-'), sg.Button("Copy", key=f'-BUTTON_COPY_IP_{i}-')])

    # ListBox version
    # network_frame_rows = [[sg.Listbox([f'{entry[0]}: {entry[1]}' for entry in network], key='-CLIENTS-', enable_events=True, size=(50, 10))]]


    network_frame = sg.Frame('Network', network_frame_rows, key='-NETWORK_FRAME-')

    
    log_frame_rows = [[sg.Text(row)] for row in MOCK_LOGS] # TODO need dynamic logs. implement a Logger class? Observer maybe?

    log_frame = sg.Frame('Log', log_frame_rows)


    links_column = sg.Column([
      [sg.Text("Download TightVNC")],
      [sg.Text("Open sheet in Google Drive")],
      [sg.Text("Donate")],
      [sg.Text("Github")],
    ], element_justification='r', expand_x=True)


    upper_row = [network_frame, sg.Push(), sg.Button('Open config', key='-BUTTON_OPEN_CONFIG-'), sg.Button('Update now', key='-BUTTON_FORCE_NETWORK_UPDATE-'), sg.Push()]
    lower_row = [log_frame, links_column]



    progress_bar = [sg.ProgressBar(100)]

    status_bar = [sg.StatusBar("Current IP: 156.562.369.53 | Time to next update: 9m16s")]



    layout = [
       upper_row,
       progress_bar,
       lower_row,
       status_bar,
    ]
    return layout



def splash_window():
  layout = [
    [sg.VPush()],
    [sg.Push(), sg.Text(PROGRAM_TITLE), sg.Push()],
    [sg.VPush()],
    [sg.Text("Fetching network, please wait a few seconds...")]
  ]
  window = sg.Window(f"{PROGRAM_TITLE} - Splash Screen", layout)
  window.read(timeout=0) # ! this is a blocking function until an event is triggered. Set a timeout (ms)
  return window




def open_config():
  global CONFIG

  # TODO finish this
    # "GAS_SCRIPT_URL": "https://script.google.com/macros/s/AKfycbzlxDo4MBRgXPUQ6KCxBD9k9gIlLNBz3ZgpbyCqVCaP5sBAvwO6PXWgpbSKnjFHPZs/exec",
    # "GAS_AUTHCODE": "k6idf8alf9asdkwer0sasg334",
    # "IP_UPDATE_INTERVAL": 10,
    # "MACHINE_NAME": "HOME_DESKTOP",
    # "IP_SERVICE": "https://api.ipify.org",
    # "USE_ENCRYPTED_DATABASE": false,
    # "IP_ENCRYPTION_KEY": "ZPVU06_oHGNe8hFb5AVG9-QqjZI42VgYaHOowOW7bUY="
  layout = [
    [sg.Push(), sg.Text("Settings"), sg.Push()],
    [sg.Text('GAS script url:'), sg.Input(CONFIG['GAS_SCRIPT_URL'], key='-GAS_SCRIPT_URL-', expand_x=True)],
    [sg.Text('GAS AuthCode:'), sg.Input(CONFIG['GAS_AUTHCODE'], key='-GAS_AUTHCODE-', expand_x=True)],
    [sg.Text('Network update interval (secs):'), sg.Input(CONFIG['IP_UPDATE_INTERVAL'], key='-IP_UPDATE_INTERVAL-', expand_x=True)],
    [sg.Text('Machine label:'), sg.Input(CONFIG['MACHINE_NAME'], key='-MACHINE_LABEL-', expand_x=True)],
    [sg.Text('IP retrieval service:'), sg.Input(CONFIG['IP_SERVICE'], key='-IP_SERVICE-', expand_x=True)],
    [sg.Text('Use encrypted database:'), sg.Checkbox('', default=bool(CONFIG['USE_ENCRYPTED_DATABASE']), key='-USE_ENCRYPTED_DATABASE-', expand_x=True)],
    [sg.Text('Encryption key:'), sg.Input(CONFIG['IP_ENCRYPTION_KEY'], key='-IP_ENCRYPTION_KEY-', expand_x=True)],
    [sg.Button('Discard changes'), sg.Button('Save changes', key='-SAVE-', expand_x=True)],
  ]
  window = sg.Window(f'{PROGRAM_TITLE} - Config', layout)
  event, values = window.read() # ! this is a blocking function until an event is triggered.

  print('event of settings: ', event)
  print('values of settings: ', values)

  if event == '-SAVE-':
    CONFIG['GAS_SCRIPT_URL'] = values['-GAS_SCRIPT_URL-']
    CONFIG['GAS_AUTHCODE'] = values['-GAS_AUTHCODE-']
    CONFIG['IP_UPDATE_INTERVAL'] = values['-IP_UPDATE_INTERVAL-']
    CONFIG['MACHINE_NAME'] = values['-MACHINE_LABEL-']
    CONFIG['IP_SERVICE'] = values['-IP_SERVICE-']
    CONFIG['USE_ENCRYPTED_DATABASE'] = values['-USE_ENCRYPTED_DATABASE-']
    CONFIG['IP_ENCRYPTION_KEY'] = values['-IP_ENCRYPTION_KEY-']

    save_config(CONFIG, config_file_path)
    window.close()

  else:
    window.close()
  









# TODO generate_random_authcode()





def main():
  IP_MANAGER = IPManager(CONFIG)

  # if a new key is generated, we write it to the config.json
  if CONFIG['IP_ENCRYPTION_KEY'] == '':
    CONFIG['IP_ENCRYPTION_KEY'] = IP_MANAGER.encryption_key.decode()
    print(f'Saving new key: ', CONFIG['IP_ENCRYPTION_KEY'])
    with open('config.json', 'w') as config_file:
      json.dump(CONFIG, config_file)

  # IP_MANAGER.update()





  
  sg.theme("DefaultNoMoreNagging")  # Choose a theme for the window

  
  # Event loop to process events and update the window
  first_loop = True
  reloads = 0

  while True:
    if first_loop == True:
      window = splash_window()
      network = IP_MANAGER.update()
      window.close()
      window = sg.Window(f"{PROGRAM_TITLE} - Reloads: {reloads}", create_main_window_layout(network))
      first_loop = False

    event, values = window.read(timeout=100000) # ! this is a blocking function until an event is triggered. Set a timeout (ms)


    # TODO implement regular IP_MANAGER.update()s using:
    # TODO https://www.pysimplegui.org/en/latest/call%20reference/#window-the-window-object
    # TODO look for "timer_start" method


    print('event (main loop): ', event)

    # Exit the program when the window is closed
    if event == sg.WIN_CLOSED or event == None:
      break

    if event == '-BUTTON_OPEN_CONFIG-':
      open_config()

    if event == '-BUTTON_RELOAD_WINDOW-':
      window.close()
      window = sg.Window(f"{PROGRAM_TITLE} - Reloads: {reloads}", create_main_window_layout(network)) # TODO change MOCK_NETWORK in production
      reloads += 1

    if event == '-BUTTON_FORCE_NETWORK_UPDATE-':
      print('event: ', event)
      window['-BUTTON_FORCE_NETWORK_UPDATE-'].update('Updating...', disabled=True)
      window.refresh()

      network = IP_MANAGER.update()
      window.close()
      window = sg.Window(f"{PROGRAM_TITLE} - Reloads: {reloads}", create_main_window_layout(network)) # TODO change MOCK_NETWORK in production
      # window.refresh()


    if event.startswith("-BUTTON_COPY_IP_"):
      print('event: ', event)
      index = int(event.split("_")[3].replace('-', ''))
      client_ip = window[f'-CLIENT_{index}_IP-'].get()
      sg.clipboard_set(client_ip)
      sg.popup_no_buttons(f"IP '{client_ip}' copied to clipboard!", no_titlebar=True, auto_close=True, auto_close_duration=2)





  # Close the window and end the program
  window.close()




if __name__ == "__main__":
    main()



























quit()
















# ip = '151.96.56.23'
# encrypted = IP_MANAGER.encrypt_str(ip)
# decrypted = IP_MANAGER.decrypt_str(encrypted)
# print('ip: ', ip)
# print('encrypted: ', encrypted, type(encrypted))
# print('decrypted: ', decrypted, type(decrypted))





# Schedule the task
schedule.every(CONFIG['IP_UPDATE_INTERVAL']).minutes.do(IP_MANAGER.update)

# Loop so that the scheduled tasks keep on running all time.
while True:
  for i in tqdm(range(300), desc="Waiting for next check: "):
    time.sleep(1)
  schedule.run_pending()




