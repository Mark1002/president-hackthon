import configparser
from wit import Wit

config = configparser.ConfigParser()
config.read('config.ini')

class WitAIService:
    def __init__(self):
        self.access_token = config['wit_ai']['Server_Access_Token'] 
        self.client = Wit(self.access_token)
    
    def retrive_message_entity(self, message):
        res_dict = self.client.message(message)
        return res_dict['entities']
