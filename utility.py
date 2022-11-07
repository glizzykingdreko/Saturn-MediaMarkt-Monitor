
import logging
from datetime import datetime
from uuid import uuid4
from random import choice

def create_logger(site: str): 
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("monitor")  
    logger.propagate = False
    formatter = logging.Formatter(f"%(asctime)s | %(levelname)s | {site} | %(message)s", "%Y-%m-%d %H:%M:%S")
    handler = logging.FileHandler(f'./logs/{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.log')
    handler.setFormatter(formatter) 
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO) 
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(handler)
    return logger

def get_bypass_headers(obj: object, api_call: str) -> dict:
    data = {
        "Host": f"www.{obj.domain}.de",
        "content-type": "application/json",
        "x-mms-salesline": obj.header,
        "x-cacheable": "false",
        "accept": "*/*",
        "apollographql-client-version": "1.79.0",
        "accept-language": "en-US,en;q=0.9", # Important for custom headers on cloudscraper
        "x-mms-country": "DE",
        "x-flow-id": str(uuid4()),
        "user-agent": "flutterapp - ios - glizzykingdreko+<3",
        "referer": f"https://www.{obj.domain}.de/de/product/_apple-iphone-14-pro-128-gb-dunkellila-dual-sim-2832790.html",
        "apollographql-client-name": "pwa-client",
        "x-mms-language": "de",
        "x-operation": api_call
    } 
    return data 

def proxy_in_json(PROXY) -> dict:
    proxy_full = PROXY.replace('\n','').split(':')
    if len(proxy_full) == 2:
        return {'http': 'http://{}'.format(PROXY),'https': 'http://{}'.format(PROXY),} 
    elif len(proxy_full) == 4:
        ip_port = '{}:{}'.format(proxy_full[0], proxy_full[1]) 
        login_pw = '{}:{}'.format(proxy_full[2], proxy_full[3])
        return {'http': 'http://{}@{}/'.format(login_pw, ip_port),'https': 'http://{}@{}/'.format(login_pw, ip_port)} 
    else:
        return False 

def get_proxy() -> dict:
    data = open("proxies.txt", "r").read().splitlines()
    if len(data) >= 1: return proxy_in_json(choice(data))
    else: return False