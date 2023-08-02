from cryptography.fernet import Fernet
import json
import re
import requests
from typing import Union
from urllib.parse import urlparse



class IPManager:
  def __init__(self, CONFIG: dict, logger=None, network=[], last_known_ip=None):
    self.CONFIG = CONFIG
    self.gas_script_url = CONFIG['GAS_SCRIPT_URL']
    self.gas_auth_code = CONFIG['GAS_AUTHCODE']
    self.ip_service = CONFIG['IP_SERVICE']
    self.machine_label = CONFIG['MACHINE_NAME']
    self.get_own_ip_attempts = 0
    self.last_known_ip = last_known_ip
    self.encryption_key = CONFIG['IP_ENCRYPTION_KEY'] if CONFIG['IP_ENCRYPTION_KEY'] != '' else Fernet.generate_key()
    self.network = network # this is useful to update this instance coming from another one (check open_config_window() in main.py)
    self.logger = logger

    self.network_has_been_given = False

    if logger == None:
      raise Exception('Logger not set. Exiting program.')


  def update(self) -> list[str]:
    self.get_network_from_GAS()


  def get_network_from_GAS(self) -> list[str]:
    self.logger.log('Requesting network to GAS...')
    address = self.gas_script_url
    headers = {'Content-Type': 'application/json'}
    data = {
      'authCode': self.gas_auth_code,
      'serviceName': self.machine_label,
      'requestType': 'REQUEST_NETWORK',
      'ip': self.last_known_ip,
    }

    if not is_valid_url(address):
      self.logger.log(f'Invalid url: {address}')
      return
    
    response = requests.post(address, headers=headers, data=json.dumps(data))

    # Ignore html messages from GAS
    if '<!DOCTYPE html>' in response.text:
      self.logger.log('ERROR: received html data from server. Database sheet is probably offline, try again later')
      return

    self.logger.log('Response from server: ', response.text)    
    fetched_network = [[value[0], value[1]] for value in json.loads(response.content)['value']]

    for record in fetched_network:
      if not self.is_valid_ipv4(record[1]): # If it's not valid ip, it could be an encrypted string, so it tries to decrypt it
        self.logger.log('IP is encrypted. Decoding...')
        # TODO an error is raised if the encryption key is wrong. Should return something to the UI
        decoded_ip = self.decrypt_str(record[1])
        if self.is_valid_ipv4(decoded_ip):
          self.logger.log('IP decoded.')
          record[1] = decoded_ip
        else:
          raise Exception('Error decrypting IP') # ? This could just update the fetched network with the same string
        
    self.network = fetched_network
    self.network_has_been_given = False
    self.logger.log('Network: ')
    for entry in self.network:
      self.logger.log(entry)
  
  def has_network_been_given(self):
    return self.network_has_been_given

  def is_valid_ipv4(self, ip: str) -> bool:
    pattern = r"^(?:\d{1,3}\.){3}\d{1,3}$"
    return bool(re.match(pattern, ip))
  
  def get_network(self):
    self.network_has_been_given = True
    return self.network
  
  def get_current_ip(self):
    return self.last_known_ip



def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
