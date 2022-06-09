"""
python version 3.9
"""

import logging
from time import time ,sleep
from getpass import getpass
from pyhmy import signing 
from pyhmy import account
from pyhmy import transaction 
import json
from account import Account 
from utils import Utils
from pyhmy.rpc.exceptions import RequestsError ,RPCError ,RequestsTimeoutError
from web3 import Web3


utl = Utils()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)-24s] [%(levelname)-8s] | %(message)s',
    handlers=[
        logging.FileHandler("debug_buy.log"),
        logging.StreamHandler()
    ]
)

r = redis.Redis(host=utl.configs['redis_host'] ,port=utl.configs['redis_port'] ,decode_responses=True)

w3 = Web3(Web3.HTTPProvider('https://api.s0.t.hmny.io'))
hero_contract = w3.eth.contract(address= Web3.toChecksumAddress(utl.contracts['hero']['address']), abi=utl.contracts['hero']['abi'])

 
def sell_hero(address, hero_id ,price):

    pri = accounts_handler.getPri(pub=address) 

    failed_count_of_req = 0

    while True:
        try :
            nonce = account.get_account_nonce(address ,block_num='latest' ,endpoint= utl.get_network() )
            break

        except RequestsError as e:
            

            logging.error(f'!! RequestsError - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                return False

            failed_count_of_req += 1

        except RequestsTimeoutError :

            logging.error(f'!! RequestsTimeoutError - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                return False
            
            failed_count_of_req += 1
    # tokenid ,startPrice ,EndPrice ,duration ,winner

    build_tx = hero_contract.functions.createAuction(hero_id, w3.toWei(price, 'ether')).buildTransaction({
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
            res = transaction.send_raw_transaction(rawTx, utl.get_network() )
            state = wait_for_transaction_receipt(res, timeout=20, endpoint=utl.get_network() )
            break
        
        except RequestsError as e:

            logging.error(f'!! RequestsError - [{e}]')
            utl.get_network(_next= True)
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
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                False
            
            failed_count_of_req += 1

    if state['status']:
        logging.info(f'- successfully tx [{hero_id}, {price}] - [{resp}]')

        return True

    else:
        logging.info(f'!! failed tx [{hero_id}, {price}] - [{resp}]')
        return False


def main():

    p = r.pubsub()
    p.subscribe('sell')
    for item in p.listen():

        utl.update_conf() 

        if type(item) != dict:

            try :
                sell_hero(item['pub'], item['hero_id'] ,item['price'])

            except KeyboardInterrupt :
                logging.error('Exit!')
                exit(0)

            except Exception as e:
                logging.error(f'!!! error [{e}]')


if __name__ == '__main__':

    logging.info('# ======= > run < ======= #')

    password_provided = getpass()
    password = password_provided.encode() 
    
    accounts_handler = Account(password)

    utl.buy_price = utl.redis.get('hero:price:latest') - utl.configs['min_diff_buy'] # init
    utl.last_check_price_time = time()
    utl.last_check_conf_time = time()



