from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout


def run_with_timeout(seconds, func, *args, **kwargs):
    """Run blocking email I/O with a cap so Render does not return 502."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=seconds)
        except FuturesTimeout as exc:
            raise TimeoutError(
                f"Email did not finish within {seconds} seconds. "
                "Set BREVO_API_KEY (xkeysib-…) on Render, verify DEFAULT_FROM_EMAIL in Brevo, "
                "and turn off Brevo IP allowlisting."
            ) from exc
