import os

import socks
import telethon
from telethon import TelegramClient
from qrcode import QRCode
from base64 import urlsafe_b64encode as base64url
from dotenv import load_dotenv
load_dotenv()
qr = QRCode()

TG_API_ID = os.environ.get("TG_API_ID", "")
TG_API_HASH = os.environ.get("TG_API_HASH", "")
TG_SESSION_NAME = os.environ.get("TG_SESSION_NAME", "quark_bot")  # 默认值
tg_proxy = os.environ.get("TG_PROXY", False)
proxy_host = os.environ.get("TG_PROXY_HOST", "127.0.0.1")
proxy_port = os.environ.get("TG_PROXY_PORT", 7890)
my_proxy = (socks.SOCKS5, proxy_host, proxy_port)
def gen_qr(token:str):
    qr.clear()
    qr.add_data(token)
    qr.print_ascii()

def display_url_as_qr(url):
    print(url)  # do whatever to show url as a qr to the user
    gen_qr(url)

async def main(client: telethon.TelegramClient):
    if(not client.is_connected()):
        await client.connect()
    client.connect()
    qr_login = await client.qr_login()
    print(client.is_connected())
    r = False
    while not r:
        display_url_as_qr(qr_login.url)
        # Important! You need to wait for the login to complete!
        try:
            r = await qr_login.wait(10)
        except:
            await qr_login.recreate()

TELEGRAM_API_ID= TG_API_ID
TELEGRAM_API_HASH=TG_API_HASH
proxy = my_proxy if tg_proxy else None
client = TelegramClient(TG_SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH, proxy=proxy)
client.loop.run_until_complete(main(client))