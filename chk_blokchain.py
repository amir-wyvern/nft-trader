import redis
from pyhmy import account
import logging
from pyhmy.rpc.exceptions import RequestsError ,RPCError ,RequestsTimeoutError
from utils import Utils
from time import time
import json


utl = Utils()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)-24s] [%(levelname)-8s] | %(message)s',
    handlers=[
        logging.FileHandler("debug_chkblokhcain.log"),
        logging.StreamHandler()
    ]
)

r = redis.Redis(host=utl.configs['redis_host'] ,port=utl.configs['redis_port'] ,decode_responses=True)

while True:

    try:
        first_10_tx_hashes = account.get_transaction_history(utl.configs['hero']['address'] ,order='DESC', page=0, page_size=10, include_full_tx=True, endpoint= utl.get_network() )
        r.set('hero:contract:tx' , json.dumps(first_10_tx_hashes))    

    except RequestsError as e:

        logging.error(f'!! RequestsError - [{e}]')
        utl.get_network(_next= True)

    except RPCError as e:

        logging.error(f'!! RPCError - [{e}]')

    except RequestsTimeoutError as e:
        
        logging.error(f'!! RequestsTimeoutError - [{e}]')
        utl.get_network(_next= True)
    
    except Exception as e :

        logging.error(f'!! error - [{e}]')
