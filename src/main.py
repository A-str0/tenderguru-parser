from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QDate
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QTextEdit, QLabel, QLineEdit, QFormLayout, 
                             QGroupBox, QSpinBox, QComboBox, QCheckBox, 
                             QCalendarWidget)
from services.orchestrator_service import OrchestratorService
from handlers.logging_handler import setup_logger
from config import Config
import sys
import logging
import datetime


class LogHandler(QThread):
    new_log = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.logger = setup_logger(config)
        self.handler = logging.StreamHandler(self)
        self.handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s (%(filename)s:%(lineno)d): %(message)s"))
        self.logger.addHandler(self.handler)

    def write(self, message):
        if message.strip():
            self.new_log.emit(message)

    def flush(self):
        pass


class TenderGuruParserApp(QWidget):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.log_handler = LogHandler(self.config)
        self.log_handler.new_log.connect(self.update_log)
        self.log_output = []
        self.orchestrator = OrchestratorService(self.config)
        self.init_ui()
        
        # Initialize scheduler if enabled
        if self.config.get("scheduler.enabled", False):
            self.start_scheduler()

    def init_ui(self):
        self.setWindowTitle('Парсер')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()

        self.title_label = QLabel('Парсер')
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        config_group = QGroupBox("Конфигурация")
        config_layout = QFormLayout()

        api_group = QGroupBox("Настройки API")
        api_layout = QFormLayout()
        self.api_code_input = QLineEdit(self.config.get("api.api_code", ""))
        api_layout.addRow(QLabel("Код API:"), self.api_code_input)
        self.api_base_url_input = QLineEdit(self.config.get("api.base_url", "https://www.tenderguru.ru/api2.3/export"))
        api_layout.addRow(QLabel("URL API:"), self.api_base_url_input)
        self.api_date = QCalendarWidget()
        year, month, day = self.config.get("api.date", datetime.datetime.now().date().strftime("%Y-%m-%d")).split("-")
        self.api_date.setSelectedDate(QDate(int(year), int(month), int(day)))
        api_layout.addRow(QLabel("Дата проверки"), self.api_date)
        api_group.setLayout(api_layout)
        self.api_request_delay_input = QSpinBox()
        self.api_request_delay_input.setValue(self.config.get("api.request_delay", 1))
        api_layout.addRow(QLabel("Задержка запроса (с):"), self.api_request_delay_input)
        self.api_max_retries_input = QSpinBox()
        self.api_max_retries_input.setValue(self.config.get("api.max_retries", 3))
        api_layout.addRow(QLabel("Максимальные попытки:"), self.api_max_retries_input)
        self.api_timeout_input = QSpinBox()
        self.api_timeout_input.setValue(self.config.get("api.timeout", 30))
        api_layout.addRow(QLabel("Таймаут (с):"), self.api_timeout_input)
        api_group.setLayout(api_layout)

        email_group = QGroupBox("Настройки Email")
        email_layout = QFormLayout()
        self.email_smtp_server_input = QLineEdit(self.config.get("email.smtp_server", "smtp.example.com"))
        email_layout.addRow(QLabel("SMTP Сервер:"), self.email_smtp_server_input)
        self.email_smtp_port_input = QSpinBox()
        self.email_smtp_port_input.setRange(0, 10000)
        self.email_smtp_port_input.setValue(self.config.get("email.smtp_port", 587))
        email_layout.addRow(QLabel("SMTP Порт:"), self.email_smtp_port_input)
        self.email_user_input = QLineEdit(self.config.get("email.user", "your_email@example.com"))
        email_layout.addRow(QLabel("Пользователь Email:"), self.email_user_input)
        self.email_password_input = QLineEdit(self.config.get("email.password", ""))
        self.email_password_input.setEchoMode(QLineEdit.Password)
        email_layout.addRow(QLabel("Пароль Email:"), self.email_password_input)
        self.email_recipient_input = QLineEdit(self.config.get("email.recipient", "recipient@example.com"))
        email_layout.addRow(QLabel("Получатель:"), self.email_recipient_input)
        email_group.setLayout(email_layout)

        email_sending_group = QGroupBox("Настройки отправки Email")
        email_sending_layout = QFormLayout()
        self.email_sending_interval_input = QSpinBox()
        self.email_sending_interval_input.setValue(self.config.get("email_sending.interval", 300))
        email_sending_layout.addRow(QLabel("Интервал Email (с):"), self.email_sending_interval_input)
        email_sending_group.setLayout(email_sending_layout)

        logging_group = QGroupBox("Настройки логирования")
        logging_layout = QFormLayout()
        self.logging_level_input = QComboBox()
        self.logging_level_input.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        current_level = self.config.get("logging.level", "INFO")
        index = self.logging_level_input.findText(current_level)
        if index >= 0:
            self.logging_level_input.setCurrentIndex(index)
        logging_layout.addRow(QLabel("Уровень логирования:"), self.logging_level_input)
        logging_group.setLayout(logging_layout)

        scheduler_group = QGroupBox("Настройки планировщика")
        scheduler_layout = QFormLayout()
        self.scheduler_enabled_input = QCheckBox()
        self.scheduler_enabled_input.setChecked(self.config.get("scheduler.enabled", False))
        scheduler_layout.addRow(QLabel("Включить планировщик:"), self.scheduler_enabled_input)
        self.scheduler_interval_input = QSpinBox()
        self.scheduler_interval_input.setRange(1, 1440)
        self.scheduler_interval_input.setValue(self.config.get("scheduler.interval_minutes", 60))
        scheduler_layout.addRow(QLabel("Интервал (минуты):"), self.scheduler_interval_input)
        scheduler_group.setLayout(scheduler_layout)

        config_layout.addRow(api_group)
        config_layout.addRow(email_group)
        config_layout.addRow(email_sending_group)
        config_layout.addRow(logging_group)
        config_layout.addRow(scheduler_group)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        button_layout = QVBoxLayout()
        self.parse_button = QPushButton('Начать парсинг')
        self.parse_button.clicked.connect(
            lambda _: 
                self.start_parsing(
                    datetime.datetime.strptime(
                        self.config.get("api.date", datetime.datetime.now().date()),
                        "%Y-%m-%d"
                    )
                )
        )
        button_layout.addWidget(self.parse_button)

        self.stop_button = QPushButton('Остановить парсинг')
        self.stop_button.clicked.connect(self.stop_parsing)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.reset_button = QPushButton('Сбросить состояние парсера')
        self.reset_button.clicked.connect(self.reset_parser_state)
        button_layout.addWidget(self.reset_button)
        
        self.save_config_button = QPushButton('Сохранить конфигурацию')
        self.save_config_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_config_button)
        
        main_layout.addLayout(button_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(QLabel("Логи:"))
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)

    def save_config(self):
        self.config.set("api.api_code", self.api_code_input.text())
        self.config.set("api.base_url", self.api_base_url_input.text())
        self.config.set("api.date", self.api_date.selectedDate().toString("yyyy-MM-dd"))
        self.config.set("api.request_delay", self.api_request_delay_input.value())
        self.config.set("api.max_retries", self.api_max_retries_input.value())
        self.config.set("api.timeout", self.api_timeout_input.value())

        self.config.set("email.smtp_server", self.email_smtp_server_input.text())
        self.config.set("email.smtp_port", self.email_smtp_port_input.value())
        self.config.set("email.user", self.email_user_input.text())
        self.config.set("email.password", self.email_password_input.text())
        self.config.set("email.recipient", self.email_recipient_input.text())
        self.config.set("email_sending.interval", self.email_sending_interval_input.value())

        self.config.set("logging.level", self.logging_level_input.currentText())
        self.config.set("scheduler.enabled", self.scheduler_enabled_input.isChecked())
        self.config.set("scheduler.interval_minutes", self.scheduler_interval_input.value())
        
        self.log_output.append("Конфигурация успешно сохранена!")
        
        # Start/stop scheduler based on configuration
        if self.scheduler_enabled_input.isChecked():
            self.start_scheduler()
        else:
            self.stop_scheduler()

    def reset_parser_state(self):
        """Reset the parser state to start from page 0."""
        try:
            self.orchestrator.database_service.reset_parser_state()
            self.log_output.append("Состояние парсера сброшено. Начнет с первой страницы.")
        except Exception as e:
            self.log_output.append(f"Ошибка при сбросе состояния: {e}")

    def start_scheduler(self):
        """Start the scheduled parsing."""
        if hasattr(self, 'scheduler_timer') and self.scheduler_timer.isActive():
            self.scheduler_timer.stop()
        
        interval_minutes = self.config.get("scheduler.interval_minutes", 60)
        self.scheduler_timer = QTimer()
        self.scheduler_timer.timeout.connect(self.scheduled_parse)
        self.scheduler_timer.start(interval_minutes * 60 * 1000)  # Convert minutes to milliseconds
        self.log_output.append(f"Планировщик запущен. Интервал: {interval_minutes} минут.")

    def stop_scheduler(self):
        """Stop the scheduled parsing."""
        if hasattr(self, 'scheduler_timer') and self.scheduler_timer.isActive():
            self.scheduler_timer.stop()
            self.log_output.append("Планировщик остановлен.")

    def scheduled_parse(self):
        """Method called by scheduler to start parsing."""
        if not self.orchestrator.is_processing():
            self.log_output.append("Запуск запланированного парсинга...")
            self.start_parsing()

    def start_parsing(self, date: datetime.datetime = datetime.datetime.now()):
        self.save_config()
        
        api_code = self.api_code_input.text().strip()
        if not api_code:
            self.log_output.append("Пожалуйста, введите код API.")
            return

        self.log_output.append(f"Запуск процесса парсинга для даты {date}...")
        self.parse_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.parse_button.setText("Парсинг...")

        self.orchestrator.start_processing(api_code, date=date)

    def stop_parsing(self):
        self.log_output.append("Остановка процесса парсинга...")
        self.orchestrator.stop_processing()
        self.parse_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.parse_button.setText("Начать парсинг")

    def update_log(self, message):
        self.log_output.append(message)

    def closeEvent(self, event):
        if self.orchestrator.is_processing():
            self.orchestrator.stop_processing()
        
        # Stop scheduler if running
        if hasattr(self, 'scheduler_timer') and self.scheduler_timer.isActive():
            self.scheduler_timer.stop()
            
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = TenderGuruParserApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
