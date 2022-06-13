"""
python version 3.9
"""

from getpass import getpass
from time import sleep 
from web3 import Web3
import requests
import redis
import json

from logger import create_logger 
from account import Account 
from utils import Utils

log = create_logger('chk_Account')

w3 = Web3(Web3.HTTPProvider('https://api.s0.t.hmny.io'))

utl = Utils()

hero_contract = w3.eth.contract(address= Web3.toChecksumAddress(utl.contracts['hero']['address']), abi=utl.contracts['hero']['abi'])
profile = w3.eth.contract(address= Web3.toChecksumAddress(utl.contracts['profile']['address']), abi=utl.contracts['profile']['abi'])
jewel = w3.eth.contract(address= Web3.toChecksumAddress(utl.contracts['jewel']['address']), abi=utl.contracts['jewel']['abi'])

r = redis.Redis(host=utl.configs['redis_host'], port=utl.configs['redis_port'] ,decode_responses=True)

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

gen = {'0' : [0] ,'1':[1] ,'2':[2] ,'3456789':[3,4,5,6,7,8,9]}
level = {}
rarity = {}
summons = {'0':[0,1] ,'123':[1,2,3] ,'4567':[4,5,6,7] ,'89' :[8,9] }
mainclass = {'01234567':[0,1,2,3,4,5,6,7] }

def place_feature(attr ,feature , name):

    tmp = attr
    for key ,value in feature.items():

        if str(attr) in key:
            tmp = value

    dict_attr = {}
    
    if name == 'mainclass':
        dict_attr = [ {"field": 'mainclass', 'operator': 'in', 'value': tmp} ]
    else:
        if type(tmp) != list:
            tmp = [int(item) for item in str(tmp)]

        dict_attr = [ {'field': name, 'operator': '>=', 'value': min(tmp) }]

    return dict_attr

def check_features(hero):

    ls = []
    ls.extend([{'field': 'network', 'operator': '=','value': 'hmy'}] )
    ls.extend([{'field': "saleprice", 'operator': ">=", 'value': 1000000000000000000}])
    ls.extend(place_feature(hero['generation'] ,gen ,'generation'))
    ls.extend(place_feature(hero['level'] ,level ,'level'))
    ls.extend(place_feature(hero['rarity'] ,rarity ,'rarity'))
    ls.extend(place_feature(hero['summons_remaining'] ,summons ,'summons_remaining'))
    ls.extend(place_feature(hero['mainclass'] ,mainclass ,'mainclass'))

    return ls

def main():

    log.debug('chk_account.py runing ...')

    while True:
        
        address = accounts_handler.getAddress()

        params = {"limit":100,"params":[],"offset":0,"order":{"orderBy":"saleprice","orderDir":"asc"}}

        params['params']  = [{"field":"owner","operator":"=","value": address},{"field":"network","operator":"=","value":"hmy"} ]

        ls_hero = requests.post('https://us-central1-defi-kingdoms-api.cloudfunctions.net/query_heroes' ,json=params ,headers= headers ).json()
        balance = jewel.functions.balanceOf(address).call() / 10**18
    
        while True:
            
            try :

                resp = requests.post('https://us-central1-defi-kingdoms-api.cloudfunctions.net/query_heroes' ,json=params ,headers= headers )
                ls_hero = resp.json()
                break

            except requests.exceptions.Timeout:

                log.error(f'!! RequestsTimeoutError - [{e}]')
                sleep(2)

            except requests.exceptions.RequestException as e:

                log.error(f'!! RequestException - [{e}]')
                sleep(2)

            except Exception as e:

                log.error(f'!! error - [{e}]')
                sleep(2)


        for hero in ls_hero:
            
            sell_params = {"limit":3,"params":[],"offset":0,"order":{"orderBy":"saleprice","orderDir":"asc"}}
            sell_params['params'] = check_features(hero)
            resp = requests.post('https://us-central1-defi-kingdoms-api.cloudfunctions.net/query_heroes' ,json=sell_params ,headers= headers )	     
            
            info_update = resp.json()

            price_for_sale = int(info_update[0]['saleprice']) // 10**18 - 0.1
            price_for_sale = int(price_for_sale * 10**18)
             
            if hero['saleprice'] is None:
                log.debug('send hero for sale [{0}-{1}]'.format(hero['id'] ,price_for_sale))
                data = {'pub': address ,'hero_id':hero['id'] ,'price':price_for_sale}
                r.publish('sell' ,json.dumps(data) )
        
            elif abs(int(hero['saleprice']) - price_for_sale) >= 2*10**18 :
                log.debug('send hero for cancel sale [{0}]'.format(hero['id']))
                data = {'pub': address ,'hero_id':hero['id'] }
                r.publish('cancel' ,json.dumps(data)) 

        sleep(10)

if __name__ == '__main__':

    log.debug('# ======= > run chk_account.py < ======= #')

    utl.update_conf()

    password_provided = getpass()
    password = password_provided.encode() 

    accounts_handler = Account(password)

    main()
 
