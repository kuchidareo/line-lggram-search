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
import re
import time

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'I1HVvaO4TBkowJFcYhdwARPGL3xhMogYT8tOSQ5dUQriMzfITnbKMrenHQo/+mXhtxxDhgDevovtIpN6JUL7ARZCBqImBe7Voy+kv2TTKPXl9fOA/pcZGE09o/GxxDxRl8FCswD6Ff5hv+03PVw03gdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '708857c7a0cff5555d7bea327d126b2a'
USER_ID = 'Ub25fb265fec31034d75bb03c70d94900'
search_word_list = [r"LG%20gram","LGgram"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def searchUsedMarket(search_word_list):
    M = mercariSearchOnSale(search_word_list)
    M.append(["mercari","-------"])
    R = rakumaSearchOnSale(search_word_list)
    R.append(["rakuma","-------"])
    result_list = M + R
    return result_list

def mercariSearchOnSale(search_word_list):
    result_list = []
    for search_word in search_word_list:
        page = 'https://www.mercari.com/jp/search/?keyword={0}'.format(search_word)
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        res = requests.get(page, headers=headers)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text,features="html.parser")
        elems_name = soup.select('.items-box-name')
        elems_price = soup.select('.items-box-price')
        elems_photo = soup.select('.items-box-photo')
        for i in range(len(elems_name)):
            new_elems_name = elems_name[i].text.replace(",", "")
            new_elems_price = elems_price[i].text.replace(",", "").replace("¥","")
            new_elems_photo = re.search('figcaption', str(elems_photo[i].__str__))
            if not new_elems_photo and int(new_elems_price) >= 30000:
                result_list.append([new_elems_name, new_elems_price])
    ## 重複を解消する
    result_list = list(map(list, set(map(tuple, result_list))))
    return result_list

def rakumaSearchOnSale(search_word_list):
    result_list = []
    for search_word in search_word_list:
        page = 'https://fril.jp/search/{0}'.format(search_word)
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        res = requests.get(page, headers=headers)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text,features="html.parser")
        elems_name = soup.findAll("span",{"itemprop":"name"})
        elems_price = soup.findAll("span",{"itemprop":"price"})
        elems_sold = soup.select(".link_search_image")
        ## elems_nameは検索結果が0件でも2つ存在しているため
        if len(elems_price) != 0:
            for i in range(len(elems_price)):
                new_elems_name = elems_name[i].text.replace(",", "")
                new_elems_price = elems_price[i].text.replace(",", "").replace("¥","")
                new_elems_sold = re.search('item-box__soldout_ribbon', str(elems_sold[i].__str__))
                if not new_elems_sold and int(new_elems_price) >= 30000:
                    result_list.append([new_elems_name, new_elems_price])
    ## 重複を解消する
    result_list = list(map(list, set(map(tuple, result_list))))
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
    try:
        result_message = ""
        result_list = searchUsedMarket(search_word_list)
        for result in result_list:
            result_message += result[0] + "\n" + result[1] + "円\n"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = result_message))
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = "検索出来ませんでした"))
    '''
    if event.message.text == "PPAP":

    else:
    '''



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)