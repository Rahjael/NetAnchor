from cryptography.fernet import Fernet
import json
import re
import requests
from typing import Union
from urllib.parse import urlparse



class IPManager:
  """Handles IP retrieval, checks and POST requests to the GAS script"""
  def __init__(self, CONFIG: dict, logger=None, network=[], last_known_ip=None):
    """_summary_

    Args:
      ip_service (str): The service to use for IP retrieval
      gas_script_url (str): The URL where the GAS script resides
      gas_auth_code (str): The security password so GAS can accept requests
      machine_label (str): The label for this machine
      encryption_key (str): The encryption key for encrypted requests
    """

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


  def get_own_ip(self) -> Union[str, None]:
    """Sends a GET request to the IP retrieval service of choice.

    Returns:
      Union[str, None]: either the current IP (str) or None if retrieval fails
    """
    self.logger.log('Getting own IP...')
    try:
      ip = requests.get(self.ip_service).text
    except requests.exceptions.RequestException as e:
      self.logger.log(e)
      ip = None
    return ip

  def send_ip_to_gas(self, current_ip: str) -> None:
    self.logger.log('Sending own IP to GAS...')
    address = self.gas_script_url
    headers = {'Content-Type': 'application/json'}
    ip_to_send = self.encrypt_str(current_ip) if self.CONFIG['USE_ENCRYPTED_DATABASE'] else current_ip
    machine_label = self.encrypt_str(self.machine_label) if self.CONFIG['USE_ENCRYPTED_DATABASE'] else self.machine_label

    data = {
      'authCode': self.gas_auth_code,
      # TODO "serviceName" should be changed to "machineLabel", but we have to sync this change with GAS routes or the program breaks
      'serviceName': machine_label,
      'requestType': 'UPDATE_IP',
      'ip': ip_to_send,
    }
    self.logger.log(f'Sending this to GAS: ', data)
    
    if not is_valid_url(address):
      self.logger.log(f'Invalid url: {address}')
      return
    
    response = requests.post(address, headers=headers, data=json.dumps(data))

    # Ignore html messages from GAS
    if '<!DOCTYPE html>' in response.text:
      self.logger.log('ERROR: received html data from server. Database sheet is probably offline, try again later')
      return
    
    self.logger.log('Response from server: ', response.text)

  def update(self) -> list[str]:
    self.get_own_ip_attempts += 1
    current_ip = self.get_own_ip()

    if current_ip is None:
      self.logger.log("Unable to retrieve IP")
    elif not self.is_valid_ipv4(current_ip):
      self.logger.log(f'Failed to retrieve valid ip address ({self.get_own_ip_attempts} tries)')
    # elif current_ip != self.last_known_ip:
    elif self.is_valid_ipv4(current_ip):
      self.send_ip_to_gas(current_ip)
      self.last_known_ip = current_ip
    # else:
    #   self.logger.log(f'IP has not changed since last check. ({current_ip}/{self.last_known_ip})')
    
    self.get_own_ip_attempts = 0
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

  def encrypt_str(self, string_to_encrypt: str) -> str:
    cipher_suite = Fernet(self.encryption_key)
    encrypted_bytes = cipher_suite.encrypt(string_to_encrypt.encode())
    return encrypted_bytes.decode()
  
  def decrypt_str(self, string_to_decrypt: str) -> str:
    cipher_suite = Fernet(self.encryption_key)
    decrypted_bytes = cipher_suite.decrypt(string_to_decrypt.encode())
    return decrypted_bytes.decode()

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
