# coding: utf-8
from flask import Flask, request, abort, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json
import uuid
from linepay import LinePayApi

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent,
    MessageEvent,
    TextMessage,
    TextSendMessage,
    StickerSendMessage,
    FlexSendMessage,
    BubbleContainer
)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# LINE BOTの設定
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# LINE Pay API
LINE_PAY_CHANNEL_ID = os.environ.get("LINE_PAY_CHANNEL_ID")
LINE_PAY_CHANNEL_SECRET = os.environ.get("LINE_PAY_CHANNEL_SECRET")
LINE_PAY_REQEST_BASE_URL = "https://{}".format(
    # set your server host name at HOST_NAME on .env file
    os.environ.get("HOST_NAME")
)
linePay = LinePayApi(
    LINE_PAY_CHANNEL_ID,
    LINE_PAY_CHANNEL_SECRET,
    is_sandbox=True
)

# アプリケーションの設定
app = Flask(__name__, static_folder='static')
CORS(app)
CACHE = {}

# データベースの設定
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)


# モデルの設定
class userTransaction(db.Model):
    __tablename__ = 'user_transaction'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255))
    product_id = db.Column(db.Integer)
    bought = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.now()
    )
    updated_at = db.Column(
        db.DateTime,
        server_default=db.text('CURRENT_TIMESTAMP')
    )

    def __init__(self, data):
        self.user_id = data['user_id']
        self.product_id = data['product_id']
        self.bought = data['bought']

    def __repr__(self):
        return '<userTransaction {}>'.format(self.user_id)


class userCheckIn(db.Model):
    __tablename__ = 'user_checkin'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255))
    status = db.Column(
        db.Enum('checkin', 'checkout', name='status_flag'),
        default='checkin'
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.now()
    )
    updated_at = db.Column(
        db.DateTime,
        server_default=db.text('CURRENT_TIMESTAMP')
    )

    def __init__(self, data):
        self.user_id = data['user_id']
        self.status = data['status']

    def __repr__(self):
        return '<userCheckin> {}'.format(self.user_id)


class products(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255))
    price = db.Column(db.Integer, default=0)

    def __init__(self, data):
        self.product_name = data['product_name']
        self.price = data['price']

    def __repr__(self):
        return '<products> {}'.format(self.id)


@app.route('/')
def connect():
    return "Hello from Flask"


@app.route('/checkin')
def check_in():
    return render_template('checkin.html')


@app.route('/callcheckin', methods=['POST'])
def call_checkin():
    body = request.get_json()
    app.logger.info('Request body: ' + json.dumps(body))

    # DBに登録
    checkinDB = userCheckIn(body)
    db.session.add(checkinDB)
    db.session.commit()

    response = {
        "message": "OK",
        "status": 200
    }
    return jsonify(response)


@app.route('/reqcheckin')
def req_checkin():
    return render_template('reqcheckin.html')


@app.route('/reqcheckout')
def req_checkout():
    return render_template('reqcheckout.html')


@app.route('/startapp')
def start_app():
    return render_template('startapp.html')


@app.route('/checkout')
def check_out():
    # 入店中のユーザーを特定
    check_user_status = db.session.query(userCheckIn).\
        filter(userCheckIn.status == 'checkin').\
        order_by(db.desc(userCheckIn.updated_at)).\
        first()
    app.logger.info('Got user: ' + check_user_status.user_id)
    user_id = check_user_status.user_id
    # トランザクションデータを取り出す
    userTransactionDB = db.session.query(userTransaction).\
        filter(userTransaction.user_id == user_id,
               userTransaction.bought.is_(False))
    bought_data = []
    total = 0
    for data in userTransactionDB:
        productData = db.session.query(products).\
            filter(products.id == data.product_id).\
            first()
        bought_product = {
            'product_name': productData.product_name,
            'price': productData.price
        }
        bought_data.append(bought_product)
        total += productData.price
    bought_data.append({
        'product_name': '合計',
        'price': total
    })

    # LINE Pay用の設定
    order_id = str(uuid.uuid4())
    currency = "JPY"
    CACHE["order_id"] = order_id
    CACHE["amount"] = total
    CACHE["currency"] = currency
    CACHE["userId"] = user_id
    request_options = {
        "amount": total,
        "currency": currency,
        "orderId": order_id,
        "packages": [
            {
                "id": "package-999",
                "amount": total,
                "name": "Sample package",
                "products": [
                    {
                        "id": "product-001",
                        "name": "LINEオートストア",
                        "imageUrl": 'https://{}{}'.format(
                            os.environ.get('HOST_NAME'),
                            '/static/img/conbiniense_store.png'
                        ),
                        "quantity": 1,
                        "price": total
                    }
                ]
            }
        ],
        "redirectUrls": {
            "confirmUrl": LINE_PAY_REQEST_BASE_URL + "/confirm",
            "cancelUrl": LINE_PAY_REQEST_BASE_URL + "/cancel"
        }
    }
    app.logger.debug(request_options)
    response = linePay.request(request_options)
    app.logger.debug(response)

    return render_template('checkout.html', data=bought_data, result=response)


@app.route('/confirm')
def pay_confirm():
    transaction_id = int(request.args.get('transactionId'))
    app.logger.info("transaction_id: %s", str(transaction_id))
    response = linePay.confirm(
        transaction_id,
        float(CACHE.get("amount", 0)),
        CACHE.get("currency", "JPY")
    )
    app.logger.info(response)

    # トランザクションデータを取り出す
    userId = CACHE.get("userId", '')
    userTransactionDB = db.session.query(userTransaction).\
        filter(userTransaction.user_id == userId and
               not userTransaction.bought)
    # 購入済みにする
    contents = [{
        "type": "separator",
        "color": "#000000"
    }]
    amount = 0
    for data in userTransactionDB:
        # 購入済みにする
        data.bought = True

        # 明細をセット
        productData = db.session.query(products).\
            filter(products.id == data.product_id).\
            first()
        box = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                  "type": "text",
                  "text": productData.product_name,
                  "size": "lg",
                  "align": "start"
              },
                {
                  "type": "text",
                  "text": "¥{}".format(productData.price),
                  "align": "end",
                  "gravity": "bottom",
                  "color": "#000000"
              }
            ]
        }
        contents.append(box)
        amount += productData.price
    # 合計金額をセット
    contents += [{
        "type": "separator",
        "color": "#000000"
    },
        {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                  "text": "合計"
            },
            {
                "type": "text",
                "text": '¥{}'.format(amount),
                "align": "end"
            }
        ]
    }]

    # レシート用のjsonを読み込む
    with open('recipt.json', 'r', encoding='utf-8') as f:
        recipt_form = json.load(f)
    # パラメータの設定
    recipt_form['contents']['body']['contents'] = contents
    recipt_form['contents']['footer']['contents'][0]['contents'][1]['text'] = transaction_id

    # レシートの送信
    container_obj = FlexSendMessage.new_from_json_dict(recipt_form)
    line_bot_api.push_message(
        userId,
        messages=container_obj
    )

    # チェックアウトの処理
    userCheckInDB = db.session.query(userCheckIn).\
        filter(userCheckIn.user_id == userId and
               userCheckIn.status == 'checkin').\
        order_by(db.desc(userCheckIn.updated_at)).\
        first()
    userCheckInDB.status = 'checkout'
    db.session.commit()

    return render_template('confirm.html')


@app.route('/insertproduct', methods=['POST'])
def insert_product():
    body = request.get_json()
    app.logger.info('Request Body: ' + json.dumps(body))

    # DBに登録
    productsDB = products(body)
    db.session.add(productsDB)
    db.session.commit()

    response = {
        'message': 'OK',
        'status': 200
    }
    return jsonify(response)


@app.route('/set_transaction', methods=['POST'])
def set_transaction():
    body = request.get_json()
    app.logger.info('Request Body: ' + json.dumps(body))

    # 入店中のユーザーを特定
    check_user_status = db.session.query(userCheckIn).\
        filter(userCheckIn.status == 'checkin').\
        order_by(db.desc(userCheckIn.updated_at)).\
        first()
    app.logger.info('Got user: ' + check_user_status.user_id)

    # DBに登録
    data = {
        'user_id': check_user_status.user_id,
        'product_id': body['product_id'],
        'bought': False
    }
    userTransactionDB = userTransaction(data)
    db.session.add(userTransactionDB)
    db.session.commit()

    response = {
        'message': 'OK',
        'status': 200
    }
    return jsonify(response)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # Connect Check
    data = json.loads(body)
    userId = data["events"][0]["source"]["userId"]
    if userId == "Udeadbeefdeadbeefdeadbeefdeadbeef":
        return "OK"

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


@handler.add(FollowEvent)
def handle_follow(event):
    message = "{}{}".format(
        '友だち追加ありがとうございます！このbotが使えるコンビニでお買い物しよう！',
        '\n※このアカウントは空想上のプロトタイプなので、実際の挙動とは異なります')
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=message),
            StickerSendMessage(
                package_id=11537,
                sticker_id=52002739
            )
        ]
    )


if __name__ == "__main__":
    app.debug = True
    app.run()
