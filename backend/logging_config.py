import logging
import sys
import uuid

import structlog


def _add_trace_id(logger, method_name, event_dict):
    """Add trace_id from context vars to each log entry."""
    trace_id = structlog.contextvars.get_contextvars().get("trace_id")
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def configure_logging(json_format: bool = True):
    """Configure structured logging for AgentRoom.

    JSON output for production parsing; pretty console for development.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_trace_id,
    ]

    if json_format:
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Redirect standard library logging through structlog
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer()
            if json_format
            else structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )
    )
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)


def get_logger(name: str):
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def new_trace_id() -> str:
    """Generate a new trace ID."""
    return uuid.uuid4().hex[:16]
