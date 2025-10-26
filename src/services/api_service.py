import requests as rq
import logging
from handlers.logging_handler import get_logger
from services.request_service import RequestService
from config import Config


class APIService:
    def __init__(self, _request_service: RequestService, config: Config):
        self.config = config
        self.API_URL = config.get("api.base_url", "https://www.tenderguru.ru/api2.3/export")
        self.logger: logging.Logger = get_logger()
        self.request_service = _request_service

    def request(self, payload: dict) -> list:
        try: 
            self.logger.debug(f"Requesting {self.API_URL} with params {payload}...")
            response: rq.Response = self.request_service.make_request(self.API_URL, payload)

            if response is None:
                raise Exception("Response is None")
            else:
                self.logger.debug(f"Request succeeded: {response}")

            data: list = response.json()  # list of dictionaries
            self.logger.debug(f"Received {len(data)} items from API")
            return data

        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return ["ERROR"]
