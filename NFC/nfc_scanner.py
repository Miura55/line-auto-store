import nfc
import logging
import coloredlogs
import requests

# app.pyを起動しているサーバーのhostname(https://localhostであればlocalhost)
host_name = 'YOUR_HOST_NAME'
# logging
logger = logging.getLogger('NFC Reader')
coloredlogs.install()


def on_connect(tag):
    for record in tag.ndef.records:
        product_id = int(record.text)
        response = requests.post(
            'https://{}/set_transaction'.format(host_name),
            json={
                "product_id": product_id
            })
        logger.info(response.json())
    return True


if __name__ == '__main__':
    logger.info('------------Waiting for writing--------------')
    try:
        while True:
            with nfc.ContactlessFrontend('usb') as clf:
                clf.connect(rdwr={'on-connect': on_connect})
    except KeyboardInterrupt:
        logger.info('------------      Finish       --------------')
