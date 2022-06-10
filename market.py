import redis
from time import sleep ,time ,mktime
import requests
from contracts import load_contracs
from web3 import Web3
import logging 
import json
from utils import Utils

logging.basicConfig( 
    level=logging.WARNING,
    format='(Market) [%(asctime)-24s] [%(levelname)-8s] [%(lineno)d] | %(message)s',
    handlers=[
        logging.FileHandler("debug_market.log"),
        logging.StreamHandler()
    ]
)   

utl = Utils()

r = redis.Redis(host=utl.configs['redis_host'] ,port=utl.configs['redis_port'] ,decode_responses=True)

w3 = Web3(Web3.HTTPProvider('https://api.s0.t.hmny.io'))


params = {"limit":1,"params":[{"field":"saleprice","operator":">=","value":1000000000000000000},{'field':'network' ,'operator':'=' ,'value':'hmy'}],"offset":0,"order":{"orderBy":"saleprice","orderDir":"asc"}}
headers = {
        'authority':'us-central1-defi-kingdoms-api.cloudfunctions.net',
        'method':'POST',
        'path':'/query_heroes',
        'scheme':'https',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,fa;q=0.8',
        'content-length': '199',
        'content-type':'application/json',
        'origin': 'https://beta.defikingdoms.com',
        'referer': 'https://beta.defikingdoms.com/',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': "Linux",
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
        }


if __name__ == '__main__':

    logging.info('[market.py runing ...]')
    count = 0
    saleprice = 0
    while True:

        if count >= 60 :
            count = 0
            logging.info(f'- after 1 hour : hero price [{saleprice}]')

        try:
            resp = requests.post('https://us-central1-defi-kingdoms-api.cloudfunctions.net/query_heroes' ,json=params ,headers= headers )
            saleprice = resp.json()[0]['saleprice'] 
            
            saleprice = f'{int(saleprice) / 10**18:.2f}'
            r.set('hero:price:latest' , float(saleprice) )

        except Exception as e:
            logging.error(f'!! hero price [{e}]')

        sleep(60)
