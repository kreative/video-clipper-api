import random
import time

import openai
from flask import current_app as app
from sentry_sdk import capture_message


def retry_on_db_error(func):
    def wrapper(*args, **kwargs):
        retries = 3
        while retries > 0:
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                retries -= 1
                if retries == 0:
                    raise e
                sleep(2 + (1 * random.random()))
        return None

    return wrapper


def retry_with_exp_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 3,
    errors: tuple = (openai.RateLimitError, openai.APIError),
):
    """Retry a function with exponential backoff

    Parameters
    ----------
    func: function
        The function to retry
    initial_delay: float
        The initial delay in seconds
    exponential_base: float
        The base for the exponential backoff
    jitter: bool
        Whether to add jitter to the delay
    max_retries: int
        The maximum number of retries
    errors: tuple
        The errors to retry on

    """
    def wrapper(*args, **kwargs):
        num_retries = 0
        delay = initial_delay
        while True:  # Loop until a successful response or max_retries
            try:
                return func(*args, **kwargs)
            except Exception as e:
                errstr = str(e)
                # if the error contains rate limiting, then we should retry
                if "rate limiting" in errstr:
                    app.logger.error(
                        f"Rate Limiting Error for {func.__name__}",
                    )
                    _ = capture_message(
                        f"Rate Limiting Error for {func.__name__}",
                        level="info",
                    )
                else:
                    app.logger.error(
                        f"Error for {func.__name__}: {errstr}",
                    )
                    _ = capture_message(f"Error for {func.__name__}: {errstr}", level="error")
                num_retries += 1  # Increment retries
                if num_retries > max_retries:
                    app.logger.error(
                        f"Maximum Number of Retries for {func.__name__}"
                        + f"({max_retries}) exceeded.",
                    )
                    return None
                delay *= exponential_base * \
                    (1 + jitter * random.random())  # Increment the delay
                time.sleep(delay)
            except errors:  # Retry on specific errors
                num_retries += 1  # Increment retries
                if num_retries > max_retries:
                    app.logger.error(
                        f"Maximum Number of Retries for {func.__name__}"
                        + f"({max_retries}) exceeded.",
                    )
                    _ = capture_message(f"Maximum Number of Retries for {func.__name__}"
                                        + f"({max_retries}) exceeded.", level="fatal")
                    return None
                delay *= exponential_base * \
                    (1 + jitter * random.random())  # Increment the delay
                time.sleep(delay)
            except Exception as e:
                raise e  # Raise exceptions for unspecified errors
    return wrapper  # type: ignore[return-value]


def generic_retry(func, max_retries=3, initial_delay=1, exponential_base=2, jitter=True):
    """Retry a function with exponential backoff

    Args:
    ----
        func (): the function to retry
        max_retries (): the maximum number of retries
        initial_delay (): the initial delay in seconds
        exponential_base (): the base for the exponential backoff
        jitter (): the jitter for the exponential backoff

    Returns:
    -------
        None: the function is not returned

    """
    def wrapper(*args, **kwargs):
        num_retries = 0
        delay = initial_delay
        while True:  # Loop until a successful response or max_retries
            try:
                return func(*args, **kwargs)
            except Exception as e:
                e_str = str(e)
                app.logger.error(e_str)
                capture_message(f"Error for {func.__name__}: {e_str}, retrying...", level="warn")

                num_retries += 1  # Increment retries
                if num_retries > max_retries:
                    app.logger.error("max retries reached")

                    capture_message(f"Exceeded max retries of {max_retries} for {func.__name__}", level="fatal")
                    raise e
                delay *= exponential_base * \
                    (1 + jitter * random.random())  # Increment the delay
                time.sleep(delay)
    return wrapper
