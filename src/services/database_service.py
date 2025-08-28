import sqlite3
import logging
import os
from typing import Optional, Dict, Any
from handlers.logging_handler import get_logger


class DatabaseService:
    def __init__(self, db_path: str = "tenderguru.db"):
        self.db_path = db_path
        self.logger: logging.Logger = get_logger()
        self.init_database()

    def init_database(self) -> None:
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create table for storing processed contracts to avoid duplicates
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processed_contracts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reg_number TEXT NOT NULL,
                        publish_date TEXT NOT NULL,
                        UNIQUE(reg_number, publish_date)
                    )
                ''')
                
                # Create table for storing last processed page
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parser_state (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        last_page INTEGER DEFAULT 0,
                        last_run_timestamp TEXT
                    )
                ''')
                
                # Insert default row for parser state if not exists
                cursor.execute('''
                    INSERT OR IGNORE INTO parser_state (id, last_page) VALUES (1, 0)
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def is_contract_processed(self, reg_number: str, publish_date: str) -> bool:
        """Check if a contract has already been processed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 1 FROM processed_contracts 
                    WHERE reg_number = ? AND publish_date = ?
                ''', (reg_number, publish_date))
                
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            self.logger.error(f"Failed to check if contract is processed: {e}")
            return False

    def mark_contract_as_processed(self, reg_number: str, publish_date: str) -> None:
        """Mark a contract as processed to avoid duplicates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO processed_contracts (reg_number, publish_date)
                    VALUES (?, ?)
                ''', (reg_number, publish_date))
                conn.commit()
                self.logger.debug(f"Marked contract {reg_number} as processed")
        except Exception as e:
            self.logger.error(f"Failed to mark contract as processed: {e}")

    def get_last_processed_page(self) -> int:
        """Get the last processed page number."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT last_page FROM parser_state WHERE id = 1')
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Failed to get last processed page: {e}")
            return 0

    def update_last_processed_page(self, page_number: int) -> None:
        """Update the last processed page number."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE parser_state 
                    SET last_page = ?, last_run_timestamp = datetime('now')
                    WHERE id = 1
                ''', (page_number,))
                conn.commit()
                self.logger.debug(f"Updated last processed page to {page_number}")
        except Exception as e:
            self.logger.error(f"Failed to update last processed page: {e}")

    def reset_parser_state(self) -> None:
        """Reset the parser state to start from page 0."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE parser_state 
                    SET last_page = 0, last_run_timestamp = datetime('now')
                    WHERE id = 1
                ''')
                conn.commit()
                self.logger.info("Reset parser state to page 0")
        except Exception as e:
            self.logger.error(f"Failed to reset parser state: {e}")
