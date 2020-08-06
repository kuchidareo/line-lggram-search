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
    # notesのCarouselColumnの各値は、変更してもらって結構です。
    notes = [CarouselColumn(thumbnail_image_url="https://renttle.jp/static/img/renttle02.jpg",
                            title="【ReleaseNote】トークルームを実装しました。",
                            text="creation(創作中・考え中の何かしらのモノ・コト)に関して、意見を聞けるようにトークルーム機能を追加しました。",
                            actions=[{"type": "message","label": "サイトURL","text": "https://renttle.jp/notes/kota/7"}]),

             CarouselColumn(thumbnail_image_url="https://renttle.jp/static/img/renttle03.jpg",
                            title="ReleaseNote】創作中の活動を報告する機能を追加しました。",
                            text="創作中や考え中の時点の活動を共有できる機能を追加しました。",
                            actions=[
                                {"type": "message", "label": "サイトURL", "text": "https://renttle.jp/notes/kota/6"}]),

             CarouselColumn(thumbnail_image_url="https://renttle.jp/static/img/renttle04.jpg",
                            title="【ReleaseNote】タグ機能を追加しました。",
                            text="「イベントを作成」「記事を投稿」「本を登録」にタグ機能を追加しました。",
                            actions=[
                                {"type": "message", "label": "サイトURL", "text": "https://renttle.jp/notes/kota/5"}])]

    messages = TemplateSendMessage(
        alt_text='template',
        template=CarouselTemplate(columns=notes),
    )
    

    '''
    if event.message.text == "PPAP":
        line_bot_api.reply_message(event.reply_token, messages=messages)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="isnot PPAP"))
    '''
    
    search_word = "LGgram"
    ##line_bot_api.reply_message(event.reply_token, TextSendMessage(text = "検索を開始しました"))
    try:
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