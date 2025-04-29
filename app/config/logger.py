import os
import logging
from logging.handlers import TimedRotatingFileHandler

class LogManager:
    # Static method to return the logger with module name
    @staticmethod
    def get_logger(module_name: str = 'root'):
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Set up the logging configuration
        log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Define the log file path
        log_file = os.path.join(log_dir, 'app_logs.log')

        # Define the log handler (this will create a new log file every day)
        log_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=7)
        log_handler.setFormatter(log_formatter)

        # Set up the logger with the specified module name
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.INFO)
        logger.addHandler(log_handler)

        return logger