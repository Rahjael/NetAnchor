import json
import os
import schedule
import time
from tqdm import tqdm

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

IP_MANAGER = IPManager(CONFIG)


# if a new key is generated, we write it to the config.json
if CONFIG['IP_ENCRYPTION_KEY'] == '':
  CONFIG['IP_ENCRYPTION_KEY'] = IP_MANAGER.encryption_key.decode()
  print(f'Saving new key: ', CONFIG['IP_ENCRYPTION_KEY'])
  with open('config.json', 'w') as config_file:
    json.dump(CONFIG, config_file)

IP_MANAGER.update()



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




