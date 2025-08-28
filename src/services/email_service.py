import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from handlers.logging_handler import get_logger, logging, logging
from config import Config


class EmailService:
    def __init__(self, config: Config):
        self.config = config
        self.logger: logging.Logger = get_logger()
        self.last_email_time = 0



    def send_email(self, subject: str, body: str):
        self.logger.debug("Preparing to send email...")
        try:
            # Get email configuration from config
            smtp_server = self.config.get("email.smtp_server", "smtp.example.com")
            smtp_port = self.config.get("email.smtp_port", 587)
            user = self.config.get("email.user", "your_email@example.com")
            password = self.config.get("email.password", "your_password")
            recipient = self.config.get("email.recipient", "recipient@example.com")
            
            # Check if enough time has passed since last email
            email_interval = self.config.get("email_sending.interval", 300)  # 5 minutes default
            current_time = time.time()
            if current_time - self.last_email_time < email_interval:
                self.logger.info(f"Skipping email send to respect interval. Next email can be sent in {email_interval - (current_time - self.last_email_time):.0f} seconds.")
                return

            msg = MIMEMultipart()
            msg["From"] = user
            msg["To"] = recipient
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html", "utf-8"))

            self.logger.debug(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg, from_addr=user, to_addrs=recipient)

            self.last_email_time = time.time()
            self.logger.info("Email sent successfully")
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            raise
