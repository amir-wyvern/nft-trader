"""
python version 3.9
"""

from typing import Dict ,List ,Tuple
import logging
from time import time
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from getpass import getpass

from decimal import Decimal
from web3 import Web3
import json

from pyhmy import signing 
from pyhmy import account
from pyhmy import transaction 
from web3._utils.threads import Timeout

import redis

from account import Account 

r = redis.Redis(host='127.0.0.1' ,port='6070' ,decode_responses=True)
global_vars = {
    'period_check_price' : time(),
    'buy_price_by_period_time' : None,
    'period_check_conf' : 300,
    'index_network' : 0
}

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)-24s] [%(levelname)-8s] | %(message)s',
    handlers=[
        logging.FileHandler("debug_main.log"),
        logging.StreamHandler()
    ]
)

try :
    with open('./config.json' ,'r') as fi:
        conf = json.load(fi)    

except Exception as e:
    logging.error(f'!! error in file config.json [{e}]')    
    exit(0)


w3 = Web3(Web3.HTTPProvider('https://api.s0.t.hmny.io'))
hero_contract = w3.eth.contract(address= Web3.toChecksumAddress(conf['hero']['address']), abi=conf['hero']['abi'])

 
def get_buy_price_by_period_time():

    if  time() - global_vars['time_check_price'] > conf['period_time_check_price'] :
        buy_price = r.get('hero:price:latest') - conf['min_diff_buy']

    else:
        buy_price = global_vars['buy_price_by_period_time'] 

    return buy_price


def wait_for_transaction_receipt(transaction_hash, timeout: float = 20, poll_latency: float = 0.1 ,endpoint= endpoint) :
        try:
            with Timeout(timeout) as _timeout:
                while True:
                    try:
                        tx_receipt = transaction.get_transaction_receipt(transaction_hash, endpoint= endpoint)

                    except TransactionNotFound:
                        tx_receipt = None

                    if tx_receipt is not None:
                        break

                    _timeout.sleep(poll_latency)

            return tx_receipt

        except Timeout:
            raise TimeExhausted(
                f"Transaction is not in the chain "
                f"after {timeout} seconds"
            )


def buy_hero(hero_id ,price):

    address = accounts.getAddress()
    pri = accounts.getPri()

    failed_count_of_req = 0

    while True:
        try :
            nonce = account.get_account_nonce(address ,block_num='latest' ,endpoint= get_network() )
            break

        except RequestsError as e:

            logging.error(f'!! RequestsError - [{e}]')
            get_network(_next= True)
            if failed_count_of_req > 3 :
                return False

            failed_count_of_req += 1

        except RequestsTimeoutError :

            logging.error(f'!! RequestsTimeoutError - [{e}]')
            get_network(_next= True)
            if failed_count_of_req > 3 :
                False
            
            failed_count_of_req += 1

    build_tx = hero_contract.functions.bid(hero_id, w3.toWei(price, 'ether')).buildTransaction({
            'nonce': nonce,
            'maxFeePerGas': 1,
            'maxPriorityFeePerGas': 1,
            'gas': 1,
            'from': address,
            'chainId':1
            })

    tx = {
                'chainId': 1,
                'from': address,
                'gas': 10165700,
                'gasPrice': 39000000000,
                'data': build_tx['data'],
                'nonce': nonce,
                'shardID': 0,
                'to': build_tx['to'],
                'toShardID': 0,
                'value': 0
            }

    rawTx = signing.sign_transaction(tx, pri).rawTransaction.hex()

    while True:
        
        try :
            res = transaction.send_raw_transaction(rawTx, get_network() )
            state = wait_for_transaction_receipt(res, timeout=20, endpoint=get_network() )
            break
        
        except RequestsError as e:

            logging.error(f'!! RequestsError - [{e}]')
            get_network(_next= True)
            if failed_count_of_req > 3 :
                return False

            failed_count_of_req += 1

        except RPCError as e:

            logging.error(f'!! RPCError - [{e}]')
            if failed_count_of_req > 3 :
                return False

            failed_count_of_req += 1

        except RequestsTimeoutError as e:
            
            logging.error(f'!! RequestsTimeoutError - [{e}]')
            get_network(_next= True)
            if failed_count_of_req > 3 :
                False
            
            failed_count_of_req += 1


    if state['status']:
        logging.info(f'- successfully tx [{hero_id}, {price}] - [{resp}]')

        return True

    else:
        logging.info(f'!! failed tx [{hero_id}, {price}] - [{resp}]')
        return False


def decode_response(tx):

    cleanInput = tx['input'][2:]
    func = cleanInput[:8]

    if func == '4ee42914':

        argByte = 8
        arg1 = cleanInput[argByte:argByte+64]
        arg1 = int(arg1 ,16)

        argByte = argByte + 64
        arg2 = cleanInput[argByte:argByte+64]
        arg2 = int(arg2 ,16) / 10**18

        argByte = argByte + 64
        arg3 = cleanInput[argByte:argByte+64]
        arg3 = int(arg3 ,16) /10**18
        
        argByte = argByte + 64
        arg4 = cleanInput[argByte:argByte+64]
        arg4 = int(arg4 ,16)

        argByte = argByte + 64
        arg5 = cleanInput[argByte:argByte+64]
        arg5 = int(arg5 ,16)

        return (arg1, arg2, arg3, arg4 ,arg5)

    return ()


def get_network(_next= False):

    if _next:
        
        global_vars['index_network'] += 1
        global_vars['index_network'] = global_vars['index_network'] % conf['networks']

        logging.info('- change network to [{0}]'.format( global_vars['index_network'] ) ) 

    return conf['networks'][global_vars['index_network']]


def main():

    while True:

        while True:
            try:
                first_100_tx_hashes = account.get_transaction_history(conf['hero']['address'] ,order='DESC', page=0, page_size=10, include_full_tx=True, endpoint= get_network() )
                break

            except RequestsError as e:

                logging.error(f'!! RequestsError - [{e}]')
                get_network(_next= True)

            except RPCError as e:

                logging.error(f'!! RPCError - [{e}]')

            except RequestsTimeoutError as e:
                
                logging.error(f'!! RequestsTimeoutError - [{e}]')
                get_network(_next= True)

        buy_price = get_buy_price_by_period_time()
        const_min_price = conf['const_min_price']
        const_min_hero_id = conf['const_min_hero_id']

        try :
    
            # NOTE : check fake address

            for i in first_100_tx_hashes :
                    
                if tx := decode_response(i):
                    
                    # tx = (hero_id, price, ... )
                    if tx[1] >= const_min_price and tx[1] <= buy_price and tx[0] > const_min_hero_id : #NOTE : i need temp var for save buy already hero to dont buy again old hero!
                        
                        logging.info( '(^-^) Found Hero [id : {0}} ,price : {1}]'.format(tx[0] ,tx[1]) )
                        buy_hero(hero_id, price)

        except KeyboardInterrupt :
            logging.error('Exit!')
            exit()

        except Exception as e:
            logging.error(f'!!! error [{e}]')


if __name__ == '__main__':

    logging.info('# ======= > run < ======= #')

    # password_provided = getpass()
    # password = password_provided.encode() 
    password = 'defiprivatewyvern@79!'.encode()
    accounts = Account(password)

    global_vars['buy_price_by_period_time'] = r.get('hero:price:latest') - conf['min_diff_buy']# init
    accounts.update()
    buy_hero(172491,20 )


