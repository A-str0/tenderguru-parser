import logging
import threading
import time
from handlers.logging_handler import get_logger
from services.api_service import APIService
from services.request_service import RequestService
from services.parsing_service import ParsingService
from services.email_service import EmailService
from services.database_service import DatabaseService
from config import Config
import datetime


class OrchestratorService:
    def __init__(self, config: Config):
        self.config = config
        self.logger: logging.Logger = get_logger()
        self.request_service = RequestService(config)
        self.api_service = APIService(self.request_service, config)
        self.parsing_service = ParsingService()
        self.email_service = EmailService(config)
        self.database_service = DatabaseService(config.get("database.path", "tenderguru.db"))
        
        self.processing_thread = None
        self.stop_processing_event = threading.Event()

    def start_processing(self, api_code: str, start_page: int = 0, date: datetime.datetime = datetime.datetime.now()) -> None:
        if self.processing_thread and self.processing_thread.is_alive():
            self.logger.warning("Processing is already running")
            return

        self.stop_processing_event.clear()
        self.processing_thread = threading.Thread(
            target=self.process_data, 
            args=(api_code, start_page, date)
        )
        self.processing_thread.start()
        self.logger.info("Started processing thread")

    def stop_processing(self) -> None:
        self.logger.info("Stopping processing...")
        self.stop_processing_event.set()

    def is_processing(self) -> bool:
        return self.processing_thread and self.processing_thread.is_alive()

    def process_data(self, api_code: str, start_page: int = None, date: datetime.datetime = datetime.datetime.now()) -> None:
        self.logger.info("Starting data processing...")
        
        # Get last processed page from database or use provided start_page
        if start_page is None:
            page_number = self.database_service.get_last_processed_page()
            self.logger.info(f"Resuming from page {page_number}")
        else:
            page_number = start_page
            self.logger.info(f"Starting from page {page_number}")
        
        all_data: list = []

        while not self.stop_processing_event.is_set():
            try:
                self.logger.debug(f"Processing page {page_number} with date {date.strftime('%Y-%m-%d')}")
                payload: dict = {
                    "mode": "reject",
                    "dtype": "json",
                    "api_code": api_code,
                    "page": f"{page_number}",
                    "date": f"{date.strftime('%Y-%m-%d')}"
                }
                
                json_data = self.api_service.request(payload)

                if len(json_data) == 0:
                    self.logger.error(f"API returned 0 items (page {page_number}, date {date.strftime('%Y-%m-%d')})")
                    self.stop_processing()

                if json_data[0] == "ERROR":
                    self.logger.error(f"API returned error (page {page_number}, date {date.strftime('%Y-%m-%d')})")

                    if not self.stop_processing_event.wait(5):
                        continue
                    else:
                        break

                if not json_data:
                    self.logger.info("No more data to process")
                    self.database_service.update_last_processed_page(0)  # Reset to start from beginning next time
                    break

                for item in json_data:
                    if self.stop_processing_event.is_set():
                        self.logger.info("Processing stopped by user")
                        break
                    
                    # Check for duplicates
                    reg_number = item.get('reg_number')
                    publish_date = item.get('publish_date')
                    
                    if reg_number and publish_date:
                        if self.database_service.is_contract_processed(reg_number, publish_date):
                            self.logger.debug(f"Skipping duplicate contract: {reg_number} - {publish_date}")
                            continue
                    
                    parsed_data = self.parse_item_data(item)

                    combined_data = {**item, **parsed_data}
                    
                    # Check if parsing failed (reg_date is None)
                    if parsed_data.get('reg_date') is None:
                        self.logger.warning(f"Parsing failed for contract {reg_number}. Possible CAPTCHA or parsing issue.")
                        continue
                    
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
                        
                        # Mark contract as processed after successful email
                        if reg_number and publish_date:
                            self.database_service.mark_contract_as_processed(reg_number, publish_date)
                            
                    except Exception as e:
                        self.logger.error(f"Failed to send email for item: {item.get('recipient_inn', 'Unknown')}. Error: {e}")
                    
                    all_data.append(combined_data)

                if self.stop_processing_event.is_set():
                    self.logger.info("Processing stopped by user")
                    break

                # Update last processed page in database
                self.database_service.update_last_processed_page(page_number)
                page_number += 1
                
                # Use configurable delay between requests
                request_delay = self.config.get("parsing.request_delay", 1)
                self.logger.info(f"Processed page {page_number - 1}. Waiting {request_delay} seconds before next page...")
                time.sleep(request_delay)

            except Exception as e:
                self.logger.error(f"Iteration {page_number} failed: {e}")

                if not self.stop_processing_event.wait(5):
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

