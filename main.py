import os

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, URIAction)

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
    R = rakumaSearchOnSale(search_word_list)
    result_list = M + R
    return result_list

def mercariSearchOnSale(search_word_list):
    result_list = []
    for search_word in search_word_list:
        page = 'https://www.mercari.com/jp/search/?keyword={0}&status_on_sale=1'.format(search_word)
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        res = requests.get(page, headers=headers)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text,features="html.parser")
        elems_name = soup.select('.items-box-name')
        elems_price = soup.select('.items-box-price')
        elems_photo = soup.select('.items-box-photo')
        elems_url = soup.findAll('section',{'class':'items-box'})
        elems_image = soup.findAll('figure',{'class','items-box-photo'})
        for i in range(len(elems_name)):
            new_elems_name = elems_name[i].text.replace(",", "")
            new_elems_price = elems_price[i].text.replace(",", "").replace("¥","")
            new_elems_photo = re.search('figcaption', str(elems_photo[i].__str__))
            new_elems_url = 'https://www.mercari.com' + elems_url[i].find('a').attrs['href']
            new_elems_image = elems_image[i].find('img').attrs['data-src']  # https://static.mercdn.net/c!/w=240/thumb/photos/m54024365745_1.jpg?1596248228
            new_elems_image.replace(new_elems_image[26:40],'item/detail/orig') # https://static.mercdn.net/item/detail/orig/photos/m54024365745_1.jpg?1596248228
            if not new_elems_photo and int(new_elems_price) >= 30000:
                result_list.append([new_elems_name, new_elems_price, new_elems_url, new_elems_image])
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
        elems_url = soup.findAll("div",{"class":"item-box__image-wrapper"})
        elems_image = soup.findAll("div",{"class":"item-box__image-wrapper"})
        ## elems_nameは検索結果が0件でも2つ存在しているため
        if len(elems_price) != 0:
            for i in range(len(elems_price)):
                new_elems_name = elems_name[i].text.replace(",", "")
                new_elems_price = elems_price[i].text.replace(",", "").replace("¥","")
                new_elems_sold = re.search('item-box__soldout_ribbon', str(elems_sold[i].__str__))
                new_elems_url = elems_url[i].find('a').attrs['href']
                new_elems_image = elems_image[i].find('a').find('img').attrs['data-original']  # https://img.fril.jp/img/301356431/m/850895908.jpg?1582422155
                new_elems_image.replace(new_elems_image[34],'l') # https://img.fril.jp/img/301356431/l/850895908.jpg?1582422155
                if not new_elems_sold and int(new_elems_price) >= 30000:
                    result_list.append([new_elems_name, new_elems_price, new_elems_url, new_elems_image])
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
    # item[0]:name
    # item[1]:price
    # item[2]:url
    # item[3]:image_url
    if event.message.text == "PPAP":
        for i in range(100):
            if i == 0:
                result_list = searchUsedMarket(search_word_list)
                result_list.sort(key=lambda x: int(x[1])) # priceでsort
            else:
                new_result_list = searchUsedMarket(search_word_list)
                new_result_list.sort(key=lambda x: int(x[1])) # priceでsort
                if new_result_list != result_list:
                    result_list = new_result_list
                    line_bot_api.push_message(USER_ID, TextSendMessage(text = "新しいLG gramが出品されました"))
                else:
                    line_bot_api.push_message(USER_ID, TextSendMessage(text = "新しいLG gramは出品されていません"))
            time.sleep(1800)
    else:
        try:
            result_list = searchUsedMarket(search_word_list)
            result_list.sort(key=lambda x: int(x[1])) # priceでsort
            size = 10 # Max10個までなので
            for start in range(0, len(result_list), size):
                notes = []
                ten_digit_result_list = result_list[start:start+size]
                for result in ten_digit_result_list:
                    new_column = CarouselColumn(thumbnail_image_url = result[3],
                                                title = result[0],
                                                text = str("{:,}".format(int(result[1]))), # set number format
                                                actions = [URIAction(label='詳しく見る',uri=result[2])])
                    notes.append(new_column)
                messages = TemplateSendMessage(
                                alt_text='LG gram search result',
                                template=CarouselTemplate(columns=notes),
                                )
                line_bot_api.push_message(USER_ID, messages=messages)
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text = "検索出来ませんでした"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)