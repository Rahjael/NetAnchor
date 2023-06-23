import json
import re
import requests
import schedule
import time
from tqdm import tqdm


print('Loading config...')
with open('config.json', "r") as file:
  CONFIG = json.load(file)
print('Config loaded.')


#
# CLASSES DEFINITION
# 


class IPManager:
  def __init__(self, ip_service, gas_script_url, gas_auth_code, machine_name):
    self.gas_script_url = gas_script_url
    self.gas_auth_code = gas_auth_code
    self.ip_service = ip_service
    self.machine_name = machine_name
    self.get_own_ip_attempts = 0
    self.last_known_ip = None
    self.network = []

  def get_own_ip(self):
    print('Getting own IP...')
    try:
      ip = requests.get(self.ip_service).text
    except requests.exceptions.RequestException as e:
      print(e)
      ip = None
    return ip

  def send_ip_to_gas(self, current_ip):
    print('Sending own IP to GAS...')
    address = self.gas_script_url
    headers = {'Content-Type': 'application/json'}
    data = {
      'authCode': self.gas_auth_code,
      'serviceName': self.machine_name,
      'requestType': 'UPDATE_IP',
      'ip': current_ip,
    }
    response = requests.post(address, headers=headers, data=json.dumps(data))
    print('Response from server: ', response.text)

  def update(self):
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

  def get_network_from_GAS(self):
    print('Requesting network to GAS...')
    address = self.gas_script_url
    headers = {'Content-Type': 'application/json'}
    data = {
      'authCode': self.gas_auth_code,
      'serviceName': self.machine_name,
      'requestType': 'REQUEST_NETWORK',
      'ip': self.last_known_ip,
    }
    response = requests.post(address, headers=headers, data=json.dumps(data))
    print('Response from server: ', response.text)
    print('Network: ', json.loads(response.content)['value'])

  def is_valid_ipv4(self, ip):
    pattern = r"^(?:\d{1,3}\.){3}\d{1,3}$"
    return bool(re.match(pattern, ip))





#
# RUNTIME
#
print('Program started')

IP_MANAGER = IPManager(CONFIG['IP_SERVICE'], CONFIG['GAS_SCRIPT_URL'], CONFIG['GAS_AUTHCODE'], CONFIG['MACHINE_NAME'])
IP_MANAGER.update()



# Schedule the task
schedule.every(CONFIG['IP_UPDATE_INTERVAL']).minutes.do(IP_MANAGER.update)

# Loop so that the scheduled tasks keep on running all time.
while True:
  for i in tqdm(range(60), desc="Waiting for next check: "):
    time.sleep(1)
  schedule.run_pending()




