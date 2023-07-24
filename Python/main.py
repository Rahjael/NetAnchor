import base64
from cryptography.fernet import Fernet
import json
import os
import re
import requests
import schedule
import time
from typing import Union
from tqdm import tqdm

config_file_path = os.path.join(os.getcwd(), 'config.json')

if os.path.exists(config_file_path):
  print('Config file exists.')
else:
  raise Exception('Config file not found. Unable to run program.')

print('Loading config...')
with open(config_file_path, "r") as file:
  CONFIG = json.load(file)
print('Config loaded.')


#
# CLASSES DEFINITION
#
class IPManager:
  """Handles IP retrieval, checks and POST requests to the GAS script"""
  def __init__(self, ip_service: str, gas_script_url: str, gas_auth_code: str, machine_label: str, encryption_key: str):
    """_summary_

    Args:
      ip_service (str): The service to use for IP retrieval
      gas_script_url (str): The URL where the GAS script resides
      gas_auth_code (str): The security password so GAS can accepts requests
      machine_label (str): The label for this machine
      encryption_key (str): The encryption key for encrypted requests
    """
    self.gas_script_url = gas_script_url
    self.gas_auth_code = gas_auth_code
    self.ip_service = ip_service
    self.machine_label = machine_label
    self.get_own_ip_attempts = 0
    self.last_known_ip = None
    self.encryption_key = encryption_key if encryption_key != '' else Fernet.generate_key()
    self.network = []


  def get_own_ip(self) -> Union[str, None]:
    """Sends a GET request to the IP retrieval service of choice.

    Returns:
      Union[str, None]: either the current IP (str) or None if retrieval fails
    """
    print('Getting own IP...')
    try:
      ip = requests.get(self.ip_service).text
    except requests.exceptions.RequestException as e:
      print(e)
      ip = None
    return ip

  def send_ip_to_gas(self, current_ip: str) -> None:
    print('Sending own IP to GAS...')
    address = self.gas_script_url
    headers = {'Content-Type': 'application/json'}
    ip_to_send = self.encrypt_str(current_ip) if CONFIG['USE_ENCRYPTED_DATABASE'] else current_ip
    machine_label = self.encrypt_str(self.machine_name) if CONFIG['USE_ENCRYPTED_DATABASE'] else current_ip

    data = {
      'authCode': self.gas_auth_code,
      # TODO "serviceName" should be changed to "machineLabel", but we have to sync this change with GAS routes or the program breaks
      'serviceName': machine_label,
      'requestType': 'UPDATE_IP',
      'ip': ip_to_send,
    }
    print(f'Sending this to GAS: ', data)
    response = requests.post(address, headers=headers, data=json.dumps(data))
    print('Response from server: ', response.text)

  def update(self) -> None:
    self.get_own_ip_attempts += 1
    current_ip = self.get_own_ip()

    if current_ip is None:
      print("Unable to retrieve IP")
    elif not self.is_valid_ipv4(current_ip):
      print(f'Failed to retrieve valid ip address ({self.get_own_ip_attempts} tries)')
    elif current_ip != self.last_known_ip:
      print(f'IP changed to {current_ip}')
      self.send_ip_to_gas(current_ip)
      self.last_known_ip = current_ip
    else:
      print(f'IP has not changed since last check. ({current_ip}/{self.last_known_ip})')
    self.get_own_ip_attempts = 0
    self.get_network_from_GAS()

  def get_network_from_GAS(self) -> None:
    print('Requesting network to GAS...')
    address = self.gas_script_url
    headers = {'Content-Type': 'application/json'}
    data = {
      'authCode': self.gas_auth_code,
      'serviceName': self.machine_label,
      'requestType': 'REQUEST_NETWORK',
      'ip': self.last_known_ip,
    }
    response = requests.post(address, headers=headers, data=json.dumps(data))
    print('Response from server: ', response.text)
    
    fetched_network = [[value[0], value[1]] for value in json.loads(response.content)['value']]

    for record in fetched_network:
      if not self.is_valid_ipv4(record[1]):
        print('IP is encrypted. Decoding...')
        # TODO an error is raised if the encryption key is wrong.
        decoded_ip = self.decrypt_str(record[1])
        if self.is_valid_ipv4(decoded_ip):
          print('IP decoded.')
          record[1] = decoded_ip
        else:
          raise Exception('Error decrypting IP')
        
    self.network = fetched_network
    print('Network: ', self.network)

  def is_valid_ipv4(self, ip: str) -> bool:
    pattern = r"^(?:\d{1,3}\.){3}\d{1,3}$"
    return bool(re.match(pattern, ip))

  def encrypt_str(self, string_to_encrypt: str) -> str:
    cipher_suite = Fernet(self.encryption_key)
    encrypted_bytes = cipher_suite.encrypt(string_to_encrypt.encode())
    return encrypted_bytes.decode()
  
  def decrypt_str(self, string_to_decrypt: str) -> str:
    cipher_suite = Fernet(self.encryption_key)
    decrypted_bytes = cipher_suite.decrypt(string_to_decrypt.encode())
    return decrypted_bytes.decode()



#
# RUNTIME
#
print('Program started')

IP_MANAGER = IPManager(CONFIG['IP_SERVICE'], CONFIG['GAS_SCRIPT_URL'], CONFIG['GAS_AUTHCODE'], CONFIG['MACHINE_NAME'], CONFIG['IP_ENCRYPTION_KEY'])


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




