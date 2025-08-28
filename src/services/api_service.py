import requests as rq
import logging
from handlers.logging_handler import setup_logger
from handlers.datetime_handler import current_formatted_time
from services.request_service import RequestService
from bs4 import BeautifulSoup


class APIService:
    API_URL: str = "https://www.tenderguru.ru/api2.3/export"

    cur_time: str = current_formatted_time()
    logger: logging.Logger = setup_logger(__name__, "Logs", f"APIService_Log_{cur_time}.log")

    request_service: RequestService


    def __init__(self, _request_service: RequestService):
        self.request_service = _request_service


    def request(self, payload: dict) -> list:
        try: 
            self.logger.debug(f"Requesting {self.API_URL} with params {payload}...")
            response: rq.Response = self.request_service.make_request(self.API_URL, payload)

            if response == None:
                raise Exception(response)
            else:
                self.logger.debug(f"Request succeeded: {response}")

            data: list = response.json() # list of dictionaries
            return data

        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return ["ERROR"]


    # TODO: сделать для ИП
    # TODO: учитывать, что на запрос может найтись несколько компаний

    def parse_webpage_ip(self, text:str) -> dict:
        

    def parse_webpage_ooo(self, text: str) -> dict:
        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")
        
        result: dict = {
            "reg_date": None,
            "capital": None,
            "connections": None,
            "gz_data": None,
            "gz_link": None,
            "licenses": None
        }

        try:
            card: BeautifulSoup = soup.find("div", id="anketa")
            if card:
                requisites: BeautifulSoup = card.find("div", class_="company-requisites").find_all("div", class_="company-row")[1].find_all("dl", class_="company-col")
                result["reg_date"] = requisites[0].find("dd", class_="company-info__text").get_text(strip=True)
                result["capital"] = requisites[1].find("dd", class_="company-info__text").get_text(strip=True)
        except Exception:
            pass

        try:
            connections_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'connections'})
            if connections_card:
                connections_html: str = connections_card.find("div", class_="tab-item active")
                if connections_html:
                    result["connections"] = str(connections_html)
        except Exception:
            pass

        try:
            gz_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'gz'})
            if gz_card:
                gz_data_element = gz_card.find("p", class_="tile-item__text")
                gz_link_element = gz_card.find("a", class_="see-details")
                
                if gz_data_element:
                    result["gz_data"] = gz_data_element.get_text(strip=True)
                if gz_link_element:
                    result["gz_link"] = gz_link_element.get("href")
        except Exception:
            pass

        try:
            licenses_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'licenses'})
            if licenses_card:
                result["licenses"] = licenses_card.get_text(strip=True)
        except Exception:
            pass

        return result


    def iterate_pages(self, start_page: int = 1) -> None:
        page_number: int = start_page

        json: list = ["Initial"]
        while json != []:
            try:
                payload: dict = {
                    "mode" : "reject",
                    "dtype" : "json",
                    "api_code" : self.API_CODE,
                    "page" : f"{page_number}",
                }
                json = self.request(payload)

                if json[0] == "ERROR":
                    raise Exception(f"API returned error (page {page_number})")

                # TODO: парсинг rusprofile
                # TODO: обработка и отправка в email_service

                page_number += 1
            except Exception as e:
                self.logger.error(f"Iteration {page_number} failed: {e}. Retrying...")#
            

