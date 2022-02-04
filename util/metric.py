from prometheus_client import Counter, Summary


ERROR_CODE = Counter(
    "http_response_error_codes_total",
    "Number of times a certain error code has been responded.",
    labelnames=("error_code", "is_system_error")
)


def error_code(code: str, is_system_error: bool):
    ERROR_CODE.labels(code, is_system_error).inc()


SQL_TIME = Summary(
    "sql_exec_time_ms",
    "The time taken for each sql event.",
    labelnames=("event_name",)
)


def sql_time(event_name: str, time: float):
    SQL_TIME.labels(event_name).observe(time)
