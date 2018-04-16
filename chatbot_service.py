from chatterbot import ChatBot
from opencc import OpenCC
from chatterbot.trainers import ChatterBotCorpusTrainer

class ChatBotService:
    def __init__(self):
        self.bot = ChatBot(
            'line-bot',
            storage_adapter='chatterbot.storage.SQLStorageAdapter',
            database='db.sqlite3'
        )
        self.bot.set_trainer(ChatterBotCorpusTrainer)
        self.bot.train('chatterbot.corpus.chinese')
        self.openCC_s2t = OpenCC('s2t')
        self.openCC_s2t.set_conversion('s2tw')
        self.openCC_t2s = OpenCC('t2s')
        self.openCC_t2s.set_conversion('tw2s')

    
    def ask_question(self, message):
        question = self.openCC_t2s.convert(message)
        response = str(self.bot.get_response(question))
        response = self.openCC_s2t.convert(response)
        return response
