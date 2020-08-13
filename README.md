# line-auto-store

もしも LINE で無人コンビニをつくるなら

## 
[![DemoMovie](http://img.youtube.com/vi/_iTLLJa2nt0/0.jpg)](http://www.youtube.com/watch?v=_iTLLJa2nt0 "Demo")


## How to Run

### DB の設定

Python をインタラクティブモードで起動し、DB の設定を行う

```
$ python
>>> from app import db
>>> db.create_all()
```

### LIFF & Bot の Token を用意

[LINE Developers](https://developers.line.biz/ja/)から LINE ログイン、Messagin API のチャネルを作成後、必要な変数を用意し.env に設定(設定するエンドポイントについては`Endpoints`を参照)

### ライブラリのインストール

以下のコマンドを実行しライブラリをインストールする。

```
pip install -r requirements.txt
```

### アプリの実行

```
python app.py
```

## 商品のスキャン

`NFC/nfc_scanner.py`で商品 ID を登録した NFC タグを読み取ってトランザクションデータに登録する（nfcpy をインストールしたパソコンか Raspberry Pi 上で動かす）

### ライブラリのセットアップ

```
pip install nfcpy
```

### NFC タグのセット

`NFC/set_tag.py`を実行し、prodct_id を登録する

## Endpoints

- `/callback`
  Messaging API の Webhook URL に設定するエンドポイント
- `/startapp`
  QR アプリを起動するためのエンドポイント
- `/checkin`
  チェックイン時のエンドポイント
- `/checkout`
  チェックアウト時のエンドポイント
- `/insertproduct`
  商品用の DB に追加するためのエンドポイント

  ```
  # Request body
  {
      'product_name':'Cola',
      'price':200
  }
  ```

- `/set_transaction`
  スキャンした商品をトランザクションデータに登録(`/insertproduct`をリクエストしたときに返ってくる product_id を呼び出す)

  ```
  # Request Body
  {
      'product_id': 1
  }
  ```
