import configparser
import threading
import logging
import os
import urllib
from logging.handlers import RotatingFileHandler
from chatbot_service import ChatBotService
from wit_ai import WitAIService
from flask import Flask, request, abort, jsonify
from flask import send_file
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
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
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
region = ''
location = ''

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

@app.route('/image/<region>/<location>/<service_type>')
def get_image(region, location, service_type):
    app.logger.info(location)
    file_path = 'data/' + region + '/' + location + '/' + service_type + '.png'
    return send_file(file_path, mimetype='image/png')

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == '選單':
        buttons_template_message = TemplateSendMessage(
            alt_text='服務功能 template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://www8.water.gov.tw/ch/images/01_img/image002.png',
                title='選擇服務',
                text='請選擇',
                actions=[
                    MessageTemplateAction(
                        label='漏水小區狀態查詢',
                        text='查詢漏水區域'
                    )
                ]
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            buttons_template_message
        )
    elif '澎湖' in event.message.text:
        global region
        region = '澎湖'
        location_list = os.listdir('data/澎湖')
        response = '您已選擇' + '[' + region + ']小區，' + \
        '可選擇以下共' + str(len(location_list)) + '個地點來查看漏水小區域資訊\n' + \
        '[' + ','.join(location_list) + ']'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
    elif event.message.text in os.listdir('data/' + region):
        global location
        location = event.message.text
        response = '您已選擇' + '[' + location + ']小區地點，可輸入[event]查看漏水事件圖' + \
        '[map]查看管線分佈位置地圖'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )

    elif event.message.text == 'map' or event.message.text == 'event':
        region_encoded = urllib.parse.quote(region)
        location_encoded = urllib.parse.quote(location)
        service_type = event.message.text
        image_url = config['server']['url'] + '/image/' + region_encoded + '/' + location_encoded + '/' + service_type
        app.logger.info("image url: {}".format(image_url))
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
        )
    else:
        entity_list = wit_ai.retrive_message_entity(event.message.text)
        if 'region' in entity_list:
            region_list = os.listdir('data')
            region_str = '[' + ','.join(region_list) + ']'
            response = '總計有' + region_str + '共' + str(len(region_list)) + '個小區\n' + \
                       '請說要查詢的漏水小區名稱'
            app.logger.info('info')
        else:
            response = '寶寶聽不懂，所以寶寶不說QQ'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
if __name__ == "__main__":
    log_handler = RotatingFileHandler('debug.log', maxBytes=10000, backupCount=1)
    log_handler.setLevel(logging.INFO)
    app.logger.addHandler(log_handler)
    app.run(debug=True)
