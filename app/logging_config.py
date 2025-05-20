import logging
import sys
from pythonjsonlogger import jsonlogger  # JSON formatter for logs

def setup_logging():
    """
    Configure the root logger to emit JSON-formatted logs to stdout,
    set appropriate log levels, and attach any necessary handlers.
    Called before FastAPI app instantiation so all early logs are captured.
    """
    # Create a JSON formatter that includes timestamp, level, logger name, and message
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
    )  # timestamp, level, logger, msg

    # Create a console handler that writes to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # adjust level for production if desired

    # Get the root logger and attach handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)      # default log level
    root_logger.addHandler(console_handler)

    # (Optional) Silence overly verbose libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    # Example of adding a custom logger to app namespace
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG)     

    # Log a startup banner
    root_logger.info("Logging is configured. All logs will be JSON formatted.")
