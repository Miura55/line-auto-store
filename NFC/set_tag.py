import nfc
import ndef
import logging
import coloredlogs

# logging
logger = logging.getLogger('NFC Reader')
coloredlogs.install()


def on_connect(tag):
    old_record = tag.ndef.records
    # product_idをセットする
    new_record = [ndef.TextRecord("5", "en")]
    if old_record == new_record:
        logger.warning("already written")
    else:
        tag.ndef.records = new_record
        logger.info("Complete!")
    return True


if __name__ == '__main__':
    logger.info('------------Waiting for writing--------------')
    with nfc.ContactlessFrontend('usb') as clf:
        clf.connect(rdwr={'on-connect': on_connect})
    logger.info('------------      Finish       --------------')
