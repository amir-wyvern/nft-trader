"""
python version 3.9
"""

from pyhmy.rpc.exceptions import RequestsError ,RPCError ,RequestsTimeoutError
from pyhmy import transaction 
from getpass import getpass
from pyhmy import signing 
from pyhmy import account
from web3 import Web3
import redis

from logger import create_logger
from account import Account 
from utils import Utils

log = create_logger('sell')

utl = Utils()

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
            
            log.error(f'!! RequestsError - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                log.info(f'!! failed tx [{hero_id}, {price}] ')
                return False

            failed_count_of_req += 1

        except RequestsTimeoutError :

            log.error(f'!! RequestsTimeoutError - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                log.info(f'!! failed tx [{hero_id}, {price}] ')
                return False
    
            failed_count_of_req += 1

        except Exception as e :

            log.error(f'!! error - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                log.info(f'!! 3 time failed tx [{hero_id}-{price}] ')
                return False
            
            failed_count_of_req += 1


    build_tx = hero_contract.functions.createAuction(hero_id, w3.toWei(price, 'wei') ,w3.toWei(price, 'wei'), 60 , 0 ).buildTransaction({
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
                'gas': utl.configs['gas_limit'],
                'gasPrice': utl.configs['gas_price'],
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
            rsep_hash = transaction.send_raw_transaction(rawTx, utl.get_network() )
            log.info(f'- Tx Hash ({hero_id}-{price}) [{resp_hash}]')

            state = wait_for_transaction_receipt(rsep_hash, timeout=20, endpoint=utl.get_network() )
            status = state['status']
            break
        
        except RequestsError as e:

            log.error(f'!! RequestsError - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                status = False
                break

            failed_count_of_req += 1

        except RPCError as e:

            log.error(f'!! RPCError - [{e}]')
            if failed_count_of_req > 3 :
                status = False
                break

            failed_count_of_req += 1

        except RequestsTimeoutError as e:
            
            log.error(f'!! RequestsTimeoutError - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                status = False
                break
            
            failed_count_of_req += 1
        
        except Exception as e :

            log.error(f'!! error - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                status = False
                break
            
            failed_count_of_req += 1


    if status:
        log.info(f'- successfully tx [{hero_id}, {price}] - [{rsep_hash}]')
        r.set(f'history:sellhero:{hero_id}' ,'confirm' ,ex=utl.configs['hero_time_cache'])
        return True

    else:
        log.info(f'!! failed tx [{hero_id}, {price}] ')
        return False


def main():

    p = r.pubsub()
    p.subscribe('sell')

    log.debug('[sell.py runing ...]')

    for item in p.listen():

        utl.update_conf() 

        if type(item) != dict:

            try :
                if not r.get('history:sellhero:{0}'.format(item['hero_id'])) :
                    sell_hero(item['pub'], item['hero_id'] ,item['price'])

            except KeyboardInterrupt :
                log.error('Exit!')
                exit(0)

            except Exception as e:
                log.error(f'!!! error [{e}]')


if __name__ == '__main__':

    log.debug('# ======= > run sell.py < ======= #')

    password_provided = getpass()
    password = password_provided.encode() 
    
    accounts_handler = Account(password)

    main()
