import configparser
import threading
from chatbot_service import ChatBotService
from wit_ai import WitAIService
from flask import Flask, request, abort, jsonify
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
# chat_bot = ChatBotService()
wit_ai = WitAIService()
lock = threading.Lock()

@app.route("/notify", methods=['POST'])
def notify():
    try:
        json_dict = request.get_json()
        email_message = json_dict['message']
    # email_message = '小區名稱:延平小區 商校街 100mm\n' + \
    #     '事件名稱:壓力低於歷史量\n' + \
    #     '事件日期2018-02-06~2018-02-08\n' + \
    #     '事件日期2018-02-07~2018-02-08\n' + \
    #     '事件日期2018-02-07~2018-02-09\n' + \
    #     '事件日期2018-02-08~2018-02-09\n' + \
    #     '事件日期2018-02-08~2018-02-10\n' + \
    #     '事件日期2018-02-09~2018-02-10\n' + \
    #     '事件日期2018-02-09~2018-02-11\n' + \
    #     '事件持續天數:2\n' + \
    #     '允許雜質比(%):5\n' + \
    #     '誤差比率(%):20\n' + \
    #     '事件數目:72\n' + \
    #     '預估漏水量:-36.11\n'
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=email_message)
        )
    except LineBotApiError:
        abort(400)
    result_dict = {"status": "ok", "description": "push message success!"}
    return jsonify(result_dict)

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
    if event.message.text == '查詢管線狀況':
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
        entity_list = wit_ai.retrive_message_entity(event.message.text)
        if 'region' in entity_list:
            response = '好的，請說要查詢的漏水小區'
        else:
            response = '寶寶聽不懂，所以寶寶不說QQ'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
if __name__ == "__main__":
    app.run(debug=True)
