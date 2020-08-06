import os

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn)

import requests
import bs4

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'I1HVvaO4TBkowJFcYhdwARPGL3xhMogYT8tOSQ5dUQriMzfITnbKMrenHQo/+mXhtxxDhgDevovtIpN6JUL7ARZCBqImBe7Voy+kv2TTKPXl9fOA/pcZGE09o/GxxDxRl8FCswD6Ff5hv+03PVw03gdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '708857c7a0cff5555d7bea327d126b2a'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def mercariSearch(search_word):
    result_list = []
    ## https://www.mercari.com/jp/search/?keyword=LGgram
    page = 'https://www.mercari.com/jp/search/?keyword={0}'.format(search_word)
 
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    res = requests.get(page, headers=headers)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text)
    elems_name = soup.select('.items-box-name')
    elems_price = soup.select('.items-box-price')
    for i in range(len(elems_name)):
        result_list.append([elems_name[i].text, elems_price[i].text])

    return result_list


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def response_message(event):
    search_word = "LGgram"
    try:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = "検索を開始しました"))
        result_message = ""
        result_list = mercariSearch(search_word)
        for result in result_list:
            result_message += result[0] + "\n" + result[1] + "\n"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = result_message))
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = "検索出来ませんでした"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)