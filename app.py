import configparser
import threading
from chatbot_service import ChatBotService
from flask import Flask, request, abort
from linebot.models import TemplateSendMessage
from linebot.models import ButtonsTemplate
from linebot.models import MessageTemplateAction
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])
user_id = config['line_bot']['User_Id']
chat_bot = ChatBotService()
lock = threading.Lock()

@app.route("/notify", methods=['GET'])
def notify():
    app.logger.info("notify body")
    try:
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="通知！")
        )
    except LineBotApiError:
        abort(400)
    return 'OK'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == '查詢漏水區域':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='查詢漏水區域功能實作中！')
        )
    elif event.message.text == '查詢管線狀況':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='查詢管線狀況功能實作中！')
        )
    elif event.message.text == '選單':
        buttons_template_message = TemplateSendMessage(
            alt_text='服務功能 template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://www8.water.gov.tw/ch/images/01_img/image002.png',
                title='選擇服務',
                text='請選擇',
                actions=[
                    MessageTemplateAction(
                        label='查詢漏水區域',
                        text='查詢漏水區域'
                    ),
                    MessageTemplateAction(
                        label='查詢管線狀況',
                        text='查詢管線狀況'
                    )
                ]
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            buttons_template_message
        )
    else:
        with lock:
            response = chat_bot.ask_question(event.message.text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
if __name__ == "__main__":
    app.run(debug=True)
