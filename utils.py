"""
python version 3.9
"""

from web3.exceptions import TimeExhausted
from web3._utils.threads import Timeout
from pyhmy import transaction 
from time import time
import redis
import json

from logger import create_logger

log = create_logger('utils')

config_keys = { 'gas_price' ,'gas_limit' ,'time_cache_hero' ,'min_diff_buy' 
                ,'const_min_hero_id','max_repeat' ,'period_time_check_price' ,'period_check_conf' 
                ,'const_min_price' ,'redis_host' ,'redis_port' ,'networks' ,'hero_time_cache'
}

class Utils:

    last_check_price_time = None
    last_check_conf_time = None
    buy_price = None
    index_network = 0
    configs = None
    contracts = None
    redis = None

    __instance = None

    def __init__(self):
        
        self.update_conf()
        self.last_check_price_time = 0

        if self.redis is None:
            self.redis = redis.Redis(host=self.configs['redis_host'] ,port=self.configs['redis_port'] ,decode_responses=True)

        log.debug('- Config ok')    

    def update_conf(self):

        if self.configs is None :
            self.last_check_conf_time = time()  
            try :
                with open('./config.json' ,'r') as fi:
                    self.configs = json.load(fi) 
            
            except Exception as e:
                log.error(f'!! error in file config.json [{e}]')    
                exit(0)
            try :
                with open('./contracts.json' ,'r') as fi:
                    self.contracts = json.load(fi) 
            
            except Exception as e:
                log.error(f'!! error in file contracts.json [{e}]')    
                exit(0)

        elif time() - self.last_check_conf_time > self.configs['period_check_conf'] :

            try :
                with open('./config.json' ,'r') as fi:
                    self.configs = json.load(fi)    
                    self.last_check_conf_time = time()  

            except Exception as e:
                log.error(f'!! error in file config.json [{e}]')  

            try :
                with open('./contracts.json' ,'r') as fi:
                    self.contracts = json.load(fi) 
            
            except Exception as e:
                log.error(f'!! error in file contracts.json [{e}]')    
                exit(0)  

        if re := config_keys - set(self.configs.keys()) :
                
            log.error(f"!! can't found keys{re} in config file")
                        
    def get_buy_price(self):

        if  time() - self.last_check_price_time > self.configs['period_time_check_price'] :
            self.last_check_price_time = time()
            self.buy_price = int( (float(self.redis.get('hero:price:latest')) - self.configs['min_diff_buy'] ) * 10**18)

        return self.buy_price

    def wait_for_transaction_receipt(self, transaction_hash, timeout: float = 20, poll_latency: float = 0.1 ,endpoint= 'https://api.s0.t.hmny.io') :

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

    def decode_response(self, tx):

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

    def get_network(self, _next= False):

        if _next:
            
            self.index_network += 1
            self.index_network = self.index_network % len(self.configs['networks'])

            log.info('- change network to [{0}]'.format( self.configs['networks'][self.index_network] ) ) 

        return self.configs['networks'][self.index_network]
