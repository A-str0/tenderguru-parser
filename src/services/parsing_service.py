import logging
from bs4 import BeautifulSoup
from handlers.logging_handler import get_logger


class ParsingService:
    def __init__(self):
        self.logger: logging.Logger = get_logger()

    def parse_webpage_ip(self, text: str) -> dict:
        self.logger.debug("Starting to parse webpage for IP...")
        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")

        result: dict = {
            "reg_date": None,
            "capital": None,
            "connections": None,
            "gz_data": None,
            "gz_link": None,
            "licenses": None,
            "finances": None
        }

        try:
            self.logger.debug("Parsing requisites for IP...")
            requisites: BeautifulSoup = soup.find("div", class_="tiles__main").find_all("div", class_="requisites-ip")[2].find_all("dl", class_="requisites-ip__list")
            result["reg_date"] = requisites[1].find("dd").get_text(strip=True)
            self.logger.debug(f"Successfully parsed reg_date: {result['reg_date']}")
        except Exception as e:
            self.logger.error(f"Requisites parsing error: {e}")
        
        try:
            self.logger.debug("Parsing connections for IP...")
            connections_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'connections'})
            if connections_card:
                connections_html: str = connections_card.find("div", class_="tab-item active")
                if connections_html:
                    result["connections"] = str(connections_html.text.strip())
                    self.logger.debug("Successfully parsed connections")
            else:
                self.logger.debug("No connections card found")
        except Exception as e:
            self.logger.error(f"Connections parsing error: {e}")

        try:
            self.logger.debug("Parsing GosZakupki data for IP...")
            gz_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'gz'})
            if gz_card:
                gz_data_element = gz_card.find("p", class_="tile-item__text")
                gz_link_element = gz_card.find("a", class_="see-details")
                
                if gz_data_element:
                    result["gz_data"] = gz_data_element.get_text(strip=True)
                    self.logger.debug(f"Successfully parsed gz_data: {result['gz_data']}")
                if gz_link_element:
                    result["gz_link"] = "https://www.rusprofile.ru" + str(gz_link_element.get("href"))
                    self.logger.debug(f"Successfully parsed gz_link: {result['gz_link']}")
            else:
                self.logger.debug("No GosZakupki card found")
        except Exception as e:
            self.logger.error(f"GosZakupki parsing error: {e}")
        
        try:
            self.logger.debug("Parsing licenses for IP...")
            licenses_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'licenses'})
            if licenses_card:
                result["licenses"] = licenses_card.get_text(strip=True)
                self.logger.debug("Successfully parsed licenses")
            else:
                self.logger.debug("No licenses card found")
        except Exception as e:
            self.logger.error(f"Licenses parsing error: {e}")
        
        self.logger.debug(f"Finished parsing webpage for IP. Result: {result}")
        return result

    def parse_webpage_ooo(self, text: str) -> dict:
        self.logger.debug("Starting to parse webpage for OOO...")
        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")
        
        result: dict = {
            "reg_date": None,
            "capital": None,
            "connections": None,
            "gz_data": None,
            "gz_link": None,
            "licenses": None,
            "finances": None
        }

        try:
            self.logger.debug("Parsing requisites for OOO...")
            card: BeautifulSoup = soup.find("div", id="anketa")
            if card:
                requisites: BeautifulSoup = card.find("div", class_="company-requisites").find_all("div", class_="company-row")[1].find_all("dl", class_="company-col")
                result["reg_date"] = requisites[0].find("dd", class_="company-info__text").get_text(strip=True)
                result["capital"] = requisites[1].find("dd", class_="company-info__text").get_text(strip=True)
                self.logger.debug(f"Successfully parsed reg_date: {result['reg_date']}, capital: {result['capital']}")
            else:
                self.logger.debug("No anketa card found")
        except Exception as e:
            self.logger.error(f"Requisites parsing error: {e}")

        try:
            self.logger.debug("Parsing connections for OOO...")
            connections_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'connections'})
            if connections_card:
                connections_html: str = connections_card.find("div", class_="tab-item active")
                if connections_html:
                    result["connections"] = str(connections_html.text.strip())
                    self.logger.debug("Successfully parsed connections")
                else:
                    self.logger.debug("No active connections tab found")
            else:
                self.logger.debug("No connections card found")
        except Exception as e:
            self.logger.error(f"Connections parsing error: {e}")

        try:
            self.logger.debug("Parsing GosZakupki data for OOO...")
            gz_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'gz'})
            if gz_card:
                gz_data_element = gz_card.find("p", class_="tile-item__text")
                gz_link_element = gz_card.find("a", class_="see-details")
                
                if gz_data_element:
                    result["gz_data"] = gz_data_element.get_text(strip=True)
                    self.logger.debug(f"Successfully parsed gz_data: {result['gz_data']}")
                if gz_link_element:
                    result["gz_link"] = "https://www.rusprofile.ru" + str(gz_link_element.get("href"))
                    self.logger.debug(f"Successfully parsed gz_link: {result['gz_link']}")
            else:
                self.logger.debug("No GosZakupki card found")
        except Exception as e:
            self.logger.error(f"GosZakupki parsing error: {e}")

        try:
            self.logger.debug("Parsing licenses for OOO...")
            licenses_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'licenses'})
            if licenses_card:
                result["licenses"] = licenses_card.get_text(strip=True)
                self.logger.debug("Successfully parsed licenses")
            else:
                self.logger.debug("No licenses card found")
        except Exception as e:
            self.logger.error(f"Licenses parsing error: {e}")

        try:
            self.logger.debug("Parsing finances for OOO...")
            accounting_card: BeautifulSoup = soup.find("div", attrs={'data-name': 'accounting'})
            if accounting_card:
                result["finances"] = accounting_card.find("div", class_="finance-col space-between")
                self.logger.debug("Successfully parsed finances")
            else:
                self.logger.debug("No accounting card found")
        except Exception as e:
            self.logger.error(f"Finances parsing error: {e}")

        self.logger.debug(f"Finished parsing webpage for OOO. Result: {result}")
        return result
