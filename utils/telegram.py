import json
from pathlib import Path

from telethon import TelegramClient


def get_tg(cfg=None, session=None, api_id=None, api_hash=None, phone=None, proxy=None):
    config = {}
    if cfg is None:
        cfg = Path('cfg/telegram.cfg')
    else:
        cfg = Path(cfg)

    if not cfg.is_file():
        raise Exception('%s must be an exists file.' % cfg)

    with open(str(cfg), 'r') as fp:
        config.update(json.load(fp))

    if session:
        config['session'] = session
    else:
        return None
    if api_id:
        config['api_id'] = api_id
    else:
        return None
    if api_hash:
        config['api_hash'] = api_hash
    else:
        return None
    if phone:
        config['phone'] = phone
    else:
        return None
    if proxy:
        config['proxy'] = proxy
    else:
        config['proxy'] = config.get('proxy', None)

    client = TelegramClient(config['session'], config['api_id'], config['api_hash'], proxy=config['proxy'])
    client.connect()

    if not client.is_user_authorized():
        # client.send_code_request(config['phone'])
        # client.sign_in(config['phone'], input('Enter the code: '))
        client.sign_in(phone=config['phone'])
        client.sign_in(code=input('Enter the code: '))

    return client


if __name__ == '__main__':
    c = get_tg_client('ameb')
    print(c.get_me())
