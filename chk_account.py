"""
python version 3.9
"""

import logging
from time import time
from getpass import getpass
from pyhmy import signing 
from pyhmy import account
from pyhmy import transaction 

from account import Account 
from utils import Utils
from time import sleep ,time 
from web3 import Web3
import requests

w3 = Web3(Web3.HTTPProvider('https://api.s0.t.hmny.io'))

utl = Utils()

hero_contract = w3.eth.contract(address= Web3.toChecksumAddress(utl.contracts['hero']['address']), abi=utl.contracts['hero']['abi'])
profile = w3.eth.contract(address= Web3.toChecksumAddress(utl.contracts['profile']['address']), abi=utl.contracts['profile']['abi'])
jewel = w3.eth.contract(address= Web3.toChecksumAddress(utl.contracts['jewel']['address']), abi=utl.contracts['jewel']['abi'])


params = {"limit":100,"params":[{"field":"owner","operator":"=","value": None},{"field":"network","operator":"=","value":"hmy"}],"offset":0,"order":{"orderBy":"generation","orderDir":"asc"}}
# params = {"limit":1  ,"params":[{"field":"saleprice","operator":">=","value":1000000000000000000},{'field':'network' ,'operator':'=' ,'value':'hmy'}],"offset":0,"order":{"orderBy":"saleprice","orderDir":"asc"}}

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

gen = {}
level = {}
rarity = {}
summons = {}
classes = {}
 

def main():

    while True:
        
        address = accounts_handler.getAddress()
        
        params['params'][0]['value'] = address
        ls_hreo = requests.post('https://us-central1-defi-kingdoms-api.cloudfunctions.net/query_heroes' ,json=params ,headers= headers )
        balance = jewel.functions.balanceOf(address).call() / 10**18
        for hero in ls_hero:
             if hero['saleprice'] is not None:
                  params['params'][0][]
                  new_info = requests.post('https://us-central1-defi-kingdoms-api.cloudfunctions.net/query_heroes' ,json=params ,headers= headers )
	     
	from pprint import pprint  
        
        #pprint(resp.json() )

        for i ,j in  resp.json()[0].items():
            if 'price' in i:
              print(i , j)
        sleep(5)


if __name__ == '__main__':

    logging.info('# ======= > run < ======= #')
    utl.update_conf()

    password_provided = getpass()
    password = password_provided.encode() 


    accounts_handler = Account(password)

    utl.last_check_price_time = time()
    utl.last_check_conf_time = time()

    main()
 
