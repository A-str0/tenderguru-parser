import requests as rq
import logging
import time
from handlers.logging_handler import get_logger
from config import Config

class RequestService:
    def __init__(self, config: Config):
        self.config = config
        self.REQUEST_URL = "https://www.rusprofile.ru/search"
        self.logger: logging.Logger = get_logger()
        
        self.request_delay = config.get("api.request_delay", 1)
        self.timeout = config.get("api.timeout", 30)
        self.max_retries = config.get("api.max_retries", 3)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        }

    def make_request(self, url: str, payload: dict) -> rq.Response:
        for attempt in range(self.max_retries):
            try: 
                self.logger.debug(f"Making request to {url} with params {payload} (attempt {attempt + 1})")
                response = rq.get(url, params=payload, headers=self.headers, timeout=self.timeout)

                if response.status_code == 200:
                    self.logger.info(f"Request succeeded: {response.status_code}")
                else:
                    raise Exception(f"{response}: {response.status_code}")
                
                time.sleep(self.request_delay)
                return response

            except Exception as e:
                self.logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.request_delay)
                else:
                    self.logger.error("Max retries reached. Request failed.")
                    return None
