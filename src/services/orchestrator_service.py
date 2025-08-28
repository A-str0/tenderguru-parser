import logging
import threading
from handlers.logging_handler import get_logger
from services.api_service import APIService
from services.request_service import RequestService
from services.parsing_service import ParsingService
from services.email_service import EmailService
from config import Config


class OrchestratorService:
    def __init__(self, config: Config):
        self.config = config
        self.logger: logging.Logger = get_logger()
        self.request_service = RequestService(config)
        self.api_service = APIService(self.request_service, config)
        self.parsing_service = ParsingService()
        self.email_service = EmailService(config)
        
        self.processing_thread = None
        self.stop_processing = threading.Event()

    def start_processing(self, api_code: str, start_page: int = 0) -> None:
        if self.processing_thread and self.processing_thread.is_alive():
            self.logger.warning("Processing is already running")
            return

        self.stop_processing.clear()
        self.processing_thread = threading.Thread(
            target=self.process_data, 
            args=(api_code, start_page)
        )
        self.processing_thread.start()
        self.logger.info("Started processing thread")

    def stop_processing(self) -> None:
        self.logger.info("Stopping processing...")
        self.stop_processing.set()

    def is_processing(self) -> bool:
        return self.processing_thread and self.processing_thread.is_alive()

    def process_data(self, api_code: str, start_page: int = 0) -> None:
        self.logger.info("Starting data processing...")
        page_number: int = start_page
        all_data: list = []

        while not self.stop_processing.is_set():
            try:
                self.logger.debug(f"Processing page {page_number}")
                payload: dict = {
                    "mode": "reject",
                    "dtype": "json",
                    "api_code": api_code,
                    "page": f"{page_number}",
                }
                
                json_data = self.api_service.request(payload)

                if json_data[0] == "ERROR":
                    self.logger.error(f"API returned error (page {page_number})")

                    if not self.stop_processing.wait(5):
                        continue
                    else:
                        break

                if not json_data:
                    self.logger.info("No more data to process")
                    break

                for item in json_data:
                    if self.stop_processing.is_set():
                        self.logger.info("Processing stopped by user")
                        break
                    
                    parsed_data = self.parse_item_data(item)
                    combined_data = {**item, **parsed_data}
                    
                    self.logger.debug(combined_data)

                    try:
                        subject_template: str = self.config.get("email.subject_template", "Расторжение")
                        body_template: str = self.config.get("email.body_template", "")
                        
                        item_count = 1
                        items_data = "\n".join([f"{key}: {value}" for key, value in combined_data.items()])
                        
                        subject = subject_template.format(item_count=item_count, **combined_data)
                        body = body_template.format(item_count=item_count, items_data=items_data, **combined_data)
                        
                        self.email_service.send_email(subject, body)
                        self.logger.info(f"Email sent for item: {item.get('recipient_inn', 'Unknown')}")
                    except Exception as e:
                        self.logger.error(f"Failed to send email for item: {item.get('recipient_inn', 'Unknown')}. Error: {e}")
                    
                    all_data.append(combined_data)

                if self.stop_processing.is_set():
                    self.logger.info("Processing stopped by user")
                    break

                page_number += 1
                self.logger.info(f"Processed page {page_number}")

            except Exception as e:
                self.logger.error(f"Iteration {page_number} failed: {e}")

                if not self.stop_processing.wait(5):
                    continue
                else:
                    break

    def parse_item_data(self, item: dict) -> dict:
        try:
            self.logger.debug(f"Parsing item data: {item}")

            inn = item.get("recipient_inn", None)
            if not inn:
                self.logger.warning("INN not found in item data")
                return {}

            search_payload = {"query": inn}
            response = self.request_service.make_request(
                self.request_service.REQUEST_URL, search_payload
            )

            if response is None or response.status_code != 200:
                self.logger.error(f"Failed to retrieve webpage for INN: {inn}")
                return {}

            is_ip = item.get("type", "").lower() == "ип" or "ип" in item.get("name", "").lower()
            self.logger.debug(f"Item identified as {'IP' if is_ip else 'OOO'}")

            if is_ip:
                parsed_data = self.parsing_service.parse_webpage_ip(response.text)
            else:
                parsed_data = self.parsing_service.parse_webpage_ooo(response.text)

            self.logger.debug(f"Parsed data: {parsed_data}")
            return parsed_data
    
        except Exception as e:
            self.logger.error(f"Error parsing item data: {e}")
            return {}

