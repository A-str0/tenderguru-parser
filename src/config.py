import json
import os
from typing import Dict, Any


class Config:
    """
    Configuration class to manage all application settings
    """
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default configuration
        """
        default_config = {
            "api": {
                "base_url": "https://www.tenderguru.ru/api2.3/export",
                "api_code": "YOUR_API_CODE_HERE"
            },
        "email": {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "user": "your_email@example.com",
            "password": "your_password",
            "recipient": "recipient@example.com",
            "subject_template": "Расторжение. Заказчик {publish_date} {recipient_name}",
            "body_template": "<p>Номер контракта: {reg_number}</p>\n<p>Поставщик: {recipient_name}</p>\n<p>Регион Поставщика: {region}</p>\n<p>ИНН: {recipient_inn}</p>\n<p>Телефон: {recipient_phone}</p>\n<p>E-mail: {recipient_mail}</p>\n<p>Заказчик: {customer}</p>\n<p>Дата вступления в силу: {effective_date}</p>\n<p>Ссылка на решение: <a href='{filelink}'>{filelink}</a></p>\n<p>Предмет контракта: {tend_name}</p>\n<p>Причина: {termination_reason}</p>\n<p>Данные с Руспрофайл (ТЗ получение данных с ресурса Руспрофайл)</p>"
        },
            "parsing": {
                "request_delay": 1,  # Delay between requests in seconds
                "max_retries": 3,    # Maximum number of retries for failed requests
                "timeout": 30        # Request timeout in seconds
            },
            "logging": {
                "level": "DEBUG",     # Logging level (DEBUG, INFO, WARNING, ERROR)
                "log_path": "Logs",
                "log_filename": "tenderguru_parser.log"
            },
            "email_sending": {
                "interval": 300      # Interval between email sends in seconds (5 minutes)
            },
            "database": {
                "path": "database.db"  # Path to the SQLite database file
            },
            "scheduler": {
                "enabled": False,        # Enable/disable scheduled parsing
                "interval_minutes": 60   # Interval between scheduled runs in minutes
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with default config to ensure all keys are present
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if sub_key not in config[key]:
                                    config[key][sub_key] = sub_value
                    return config
            except Exception as e:
                print(f"Error loading config file: {e}. Using default configuration.")
                return default_config
        else:
            # Create default config file
            self.save_config(default_config)
            return default_config

    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config file: {e}")

    def get(self, key: str, default=None):
        """
        Get configuration value by key
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value) -> None:
        """
        Set configuration value by key
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config(self.config)
