"""
Structured logging configuration.

Provides JSON-formatted logging with request IDs, timing, and context
for better observability and log aggregation.
"""

import logging
import sys
import time
from typing import Any

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log records."""
        super().add_fields(log_record, record, message_dict)

        # Add request ID if available
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_record["request_id"] = request_id

        # Add duration if available
        duration = getattr(record, "duration", None)
        if duration:
            log_record["duration_ms"] = round(duration * 1000, 2)

        # Standardize field names
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["timestamp"] = self.formatTime(record, self.datefmt)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure structured JSON logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Set custom JSON formatter
    formatter = CustomJsonFormatter(
        fmt="%(timestamp)s %(level)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Set uvicorn loggers to use same format
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.addHandler(console_handler)
        logger.setLevel(getattr(logging, level.upper()))


class LoggingMiddleware:
    """
    Middleware for structured request logging.

    Logs each request with:
    - Method and path
    - Request ID
    - Response status code
    - Duration in milliseconds
    - Client IP
    """

    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("api.requests")

    async def __call__(self, scope, receive, send):
        """Log request/response with timing."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Get request info
        method = scope["method"]
        path = scope["path"]
        client_ip = scope.get("client", ("unknown", 0))[0]

        # Get request ID from state (set by RequestIDMiddleware)
        request_id = scope.get("state", {}).get("request_id", "unknown")

        # Track timing
        start_time = time.time()

        # Capture response status
        status_code = None

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            return await send(message)

        try:
            # Process request
            await self.app(scope, receive, send_wrapper)
        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Log request
            extra = {
                "request_id": request_id,
                "duration": duration,
                "method": method,
                "path": path,
                "status_code": status_code,
                "client_ip": client_ip,
            }

            # Choose log level based on status code
            if status_code and status_code >= 500:
                log_func = self.logger.error
            elif status_code and status_code >= 400:
                log_func = self.logger.warning
            else:
                log_func = self.logger.info

            log_func(
                f"{method} {path} - {status_code}",
                extra=extra,
            )
