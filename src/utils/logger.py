import logging
import os
from datetime import datetime

def setup_logger(name, log_file='app.log', level=logging.INFO):
    """Function to setup a logger that writes to a file and console."""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger

# Example usage (can be removed if not needed for direct execution)
if __name__ == "__main__":
    # Ensure the logs directory exists
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    my_logger = setup_logger('my_app', log_file=log_file_path)
    my_logger.info('This is an info message from the example.')
    my_logger.warning('This is a warning message from the example.')
    my_logger.error('This is an error message from the example.')