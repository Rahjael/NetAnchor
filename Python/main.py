import json
import os
import schedule
import time
from tqdm import tqdm
import PySimpleGUI as sg

from ip_manager import IPManager

config_file_path = os.path.join(os.getcwd(), 'config.json')

if os.path.exists(config_file_path):
  print('Config file exists.')
else:
  raise Exception('Config file not found. Unable to run program.')

print('Loading config...')
with open(config_file_path, "r") as file:
  CONFIG = json.load(file)
print('Config loaded.')



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


def create_layout(network):
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



    print('network_frame_rows: ', network_frame_rows)




    network_frame = sg.Frame('Network', network_frame_rows, key='-NETWORK_FRAME-')

    
    log_frame_rows = [[sg.Text(row)] for row in MOCK_LOGS] # TODO need dynamic logs. implement a Logger class? Observer maybe?

    log_frame = sg.Frame('Log', log_frame_rows)


    links_column = sg.Column([
      [sg.Text("Download TightVNC")],
      [sg.Text("Open sheet in Google Drive")],
      [sg.Text("Donate")],
      [sg.Text("Github")],
    ], element_justification='r', expand_x=True)


    upper_row = [network_frame, sg.Push(), sg.Button('Reload window', key='-BUTTON_RELOAD_WINDOW-'), sg.Button('Update now', key='-BUTTON_FORCE_NETWORK_UPDATE-'), sg.Push()]
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

      # TODO message "Please wait for network to update..." in the Logger
      # window.disappear()
      # window.reappear()

      

      network = IP_MANAGER.update()
      window.close()
      window = sg.Window(f"{PROGRAM_TITLE} - Reloads: {reloads}", create_layout(network)) # TODO change MOCK_NETWORK in production
      first_loop = False


    event, values = window.read(timeout=100000) # ! this is a blocking function until an event is triggered. Set a timeout (ms)


    # TODO implement regular IP_MANAGER.update()s using:
    # TODO https://www.pysimplegui.org/en/latest/call%20reference/#window-the-window-object
    # TODO look for "timer_start" method


    print('event (main loop): ', event)



    if event == '-BUTTON_RELOAD_WINDOW-':
      window.close()
      window = sg.Window(f"{PROGRAM_TITLE} - Reloads: {reloads}", create_layout(network)) # TODO change MOCK_NETWORK in production
      reloads += 1


    if event == '-BUTTON_FORCE_NETWORK_UPDATE-':
      print('event: ', event)
      window['-BUTTON_FORCE_NETWORK_UPDATE-'].update('Updating...', disabled=True)
      window.refresh()

      network = IP_MANAGER.update()
      window.close()
      window = sg.Window(f"{PROGRAM_TITLE} - Reloads: {reloads}", create_layout(network)) # TODO change MOCK_NETWORK in production
      # window.refresh()


    if event.startswith("-BUTTON_COPY_IP_"):
      print('event: ', event)
      index = int(event.split("_")[3].replace('-', ''))
      client_ip = window[f'-CLIENT_{index}_IP-'].get()
      sg.clipboard_set(client_ip)
      sg.popup_no_buttons(f"IP '{client_ip}' copied to clipboard!", no_titlebar=True, auto_close=True, auto_close_duration=2)


    # Exit the program when the window is closed
    if event == sg.WIN_CLOSED:
      break


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




