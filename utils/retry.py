from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx


def retry_on_transient(max_attempts: int = 3):
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    )
