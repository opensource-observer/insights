import logging
from typing import Any, Dict
from flipside import Flipside
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def init_flipside(api_key: str) -> Flipside:
    return Flipside(api_key, "https://api-v2.flipsidecrypto.xyz")


def parse_result(result: Any) -> Any:
    return result.rows[0][0] if result.rows else None


def execute_query(flipside: Flipside, query: str, project_info: Dict[str, Any]) -> Any:
    start_time = time.time()
    status = "success"
    value = None

    try:
        result = flipside.query(query)
        value = parse_result(result)
    except Exception as e:
        status = "failed"
        logger.error(f"Query execution failed: {str(e)}")
        logger.error(f"Query: {query}")

    end_time = time.time()
    execution_time = end_time - start_time

    log_query_attempt(project_info, status, execution_time, value)

    return value


def log_query_attempt(project_info: Dict[str, Any], status: str, execution_time: float, value: Any) -> None:
    log_fields = [
        f"{key}: {value}"
        for key, value in project_info.items()
    ]
    additional_info = ", ".join(log_fields)
    log_message = (
        f"Query Attempt: "
        f"{additional_info}, "
        f"Status: {status}, "
        f"Execution Time: {execution_time:.2f} seconds, "
        f"Value: {value}"
    )
    logger.info(log_message)

