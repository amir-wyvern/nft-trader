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

log = create_logger('buy')

utl = Utils()

r = redis.Redis(host=utl.configs['redis_host'] ,port=utl.configs['redis_port'] ,decode_responses=True)

w3 = Web3(Web3.HTTPProvider('https://api.s0.t.hmny.io'))
hero_contract = w3.eth.contract(address= Web3.toChecksumAddress(utl.contracts['hero']['address']), abi=utl.contracts['hero']['abi'])

def buy_hero(hero_id ,price):

    address = accounts_handler.getAddress()
    pri = accounts_handler.getPri() 

    failed_count_of_req = 0

    while True:
        try :
            nonce = account.get_account_nonce(address ,block_num='latest' ,endpoint= utl.get_network() )
            break

        except RequestsError as e:
            
            log.error(f'!! RequestsError - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                log.info(f'!! 3 time failed tx [{hero_id}-{price}] ')
                return False

            failed_count_of_req += 1

        except RequestsTimeoutError :

            log.error(f'!! RequestsTimeoutError - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                log.info(f'!! 3 time failed tx [{hero_id}-{price}] ')
                return False
            
            failed_count_of_req += 1
        
        except Exception as e :

            log.error(f'!! error - [{e}]')
            utl.get_network(_next= True)
            if failed_count_of_req > 3 :
                log.info(f'!! 3 time failed tx [{hero_id}-{price}] ')
                return False
            
            failed_count_of_req += 1
        

    build_tx = hero_contract.functions.bid(int(hero_id), w3.toWei(price, 'wei')).buildTransaction({
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
            resp_hash = transaction.send_raw_transaction(rawTx, utl.get_network() )
            log.info(f'- Tx Hash ({hero_id}-{price}) [{resp_hash}]')

            state = utl.wait_for_transaction_receipt(resp_hash, timeout=20, endpoint=utl.get_network() )
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
        log.info(f'- successfully tx ({hero_id}-{price}) [{resp_hash}]')
        accounts_handler.nextIndex()
        r.set(f'history:buyhero:{hero_id}' ,'confirm' ,ex=utl.configs['hero_time_cache'])
        return True

    else:
        log.info(f'!! failed tx [{hero_id}, {price}] ')
        return False


def main():
    
    log.debug('[buy.py runing ...]')

    while True:

        utl.update_conf() 

        while True:
            try:
                first_10_tx = account.get_transaction_history(utl.contracts['hero']['address'] ,order='DESC', page=0, page_size=10, include_full_tx=True, endpoint= utl.get_network() )
                break

            except RequestsError as e:

                log.error(f'!! RequestsError - [{e}]')
                utl.get_network(_next= True)

            except RPCError as e:

                log.error(f'!! RPCError - [{e}]')

            except RequestsTimeoutError as e:
                
                log.error(f'!! RequestsTimeoutError - [{e}]')
                utl.get_network(_next= True)
            
            except Exception as e :

                log.error(f'!! error - [{e}]')


        buy_price = utl.get_buy_price()
        const_min_price = utl.configs['const_min_price']
        const_min_hero_id = utl.configs['const_min_hero_id']

        try :
    
            # NOTE : check fake address

            for i in first_10_tx :
                    
                if tx := utl.decode_response(i):
                    
                    # tx = (hero_id, price, ... )
                    if tx[1] >= int(const_min_price * 10**18) and tx[1] <= buy_price and \
                        tx[0] > const_min_hero_id and not r.get('history:buyhero:{0}'.format(tx[0])): #NOTE : i need temp var for save buy already hero to dont buy again old hero!
                        
                        log.info( '(^-^) Found Hero [id : {0}} ,price : {1}]'.format(tx[0] ,tx[1]) )
                        buy_hero(tx[0], tx[1])

        except KeyboardInterrupt :
            log.error('Exit!')
            exit(0)

        except Exception as e:
            log.error(f'!!! error [{e}]')
        

if __name__ == '__main__':

    log.debug('# ======= > run buy.py < ======= #')

    password_provided = getpass()
    password = password_provided.encode() 
    
    accounts_handler = Account(password)
    
    main()



