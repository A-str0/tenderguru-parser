import requests as rq
import logging
from handlers.logging_handler import setup_logger
from handlers.datetime_handler import current_formatted_time

class RequestService:
    REQUEST_URL: str = "https://www.rusprofile.ru/search"

    cur_time: str = current_formatted_time()
    logger: logging.Logger = setup_logger(__name__, "Logs", f"APIService_Log_{cur_time}.log")

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    def make_request(self, url: str, payload: dict) -> rq.Response:
        try: 
            response = rq.get(url, params=payload, headers=self.headers)

            if response.status_code == 200:
                self.logger.info(f"Request succeeded: {response.status_code}")
            else:
                raise Exception(f"{response}: {response.status_code}")
            
            return response

        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None