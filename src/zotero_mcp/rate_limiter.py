"""
Rate limiter for Zotero API calls with proper handling of rate limit headers.
"""

import time
import logging
from typing import Any, Callable, Optional, TypeVar
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RateLimiter:
    """
    Rate limiter for Zotero API that respects Backoff and Retry-After headers.
    Implements exponential backoff strategy.
    """

    def __init__(self,
                 initial_delay: float = 0.1,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 max_retries: int = 5):
        """
        Initialize rate limiter.
        
        Args:
            initial_delay: Initial delay between requests in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Factor to multiply delay by on each retry
            max_retries: Maximum number of retries before giving up
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.max_retries = max_retries
        self.last_request_time = 0
        self.current_backoff = 0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        if self.current_backoff > 0:
            wait_time = self.current_backoff
            logger.info(f"Rate limit backoff: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
            self.current_backoff = 0
        else:
            # Basic rate limiting between requests
            elapsed = time.time() - self.last_request_time
            if elapsed < self.initial_delay:
                time.sleep(self.initial_delay - elapsed)

        self.last_request_time = time.time()

    def handle_rate_limit_response(self, response: Any) -> bool:
        """
        Handle rate limit response from Zotero API.
        
        Args:
            response: Response object from pyzotero
            
        Returns:
            True if rate limit was detected and handled
        """
        # Check for rate limit status code
        if hasattr(response, 'status_code') and response.status_code == 429:
            # Check for Retry-After header
            retry_after = None
            if hasattr(response, 'headers'):
                retry_after = response.headers.get('Retry-After')

            if retry_after:
                try:
                    self.current_backoff = float(retry_after)
                    logger.warning(f"Rate limit hit (429). Retry-After: {self.current_backoff} seconds")
                except ValueError:
                    self.current_backoff = self.max_delay
            else:
                # No Retry-After header, use exponential backoff
                if self.current_backoff > 0:
                    self.current_backoff = min(
                        self.current_backoff * self.backoff_factor,
                        self.max_delay
                    )
                else:
                    self.current_backoff = self.initial_delay
                logger.warning(
                    f"Rate limit hit (429). Using exponential backoff: "
                    f"{self.current_backoff} seconds"
                )

            return True
        
        # Check for Backoff header (can be in any response)
        if hasattr(response, 'headers') and 'Backoff' in response.headers:
            try:
                backoff_seconds = float(response.headers['Backoff'])
                self.current_backoff = backoff_seconds
                logger.info(f"Backoff header detected: {backoff_seconds} seconds")
                return True
            except ValueError:
                pass

        return False

    def with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to add rate limiting and retry logic to a function.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function with rate limiting
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    # Wait before making request
                    self.wait_if_needed()

                    # Make the request
                    result = func(*args, **kwargs)

                    # Reset backoff on success
                    self.current_backoff = 0

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if this is a rate limit error from pyzotero
                    error_msg = str(e).lower()
                    is_rate_limit = (
                        '429' in error_msg or
                        'rate limit' in error_msg or
                        'too many requests' in error_msg
                    )
                    if is_rate_limit and attempt < self.max_retries:
                        # Calculate backoff with jitter
                        base_backoff = self.initial_delay * (
                            self.backoff_factor ** attempt
                        )
                        jitter = random.uniform(0, 1)
                        backoff = min(base_backoff + jitter, self.max_delay)
                        logger.warning(
                            f"Rate limit error on attempt {attempt + 1}. "
                            f"Retrying in {backoff:.1f} seconds..."
                        )
                        time.sleep(backoff)
                        continue

                    # For non-rate limit errors, raise immediately
                    raise
            
            # If we've exhausted all retries, raise the last exception
            if last_exception:
                logger.error(f"Failed after {self.max_retries + 1} attempts")
                raise last_exception

        return wrapper


# Global rate limiter instance
rate_limiter = RateLimiter()


def with_rate_limit(func: Callable[..., T]) -> Callable[..., T]:
    """
    Convenience decorator to apply rate limiting to a function.
    
    Usage:
        @with_rate_limit
        def my_zotero_api_call():
            return zot.items()
    """
    return rate_limiter.with_retry(func)


class RateLimitedZoteroClient:
    """
    Wrapper for pyzotero client that adds rate limiting to all API methods.
    """

    def __init__(self, zotero_client: Any,
                 rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize rate-limited Zotero client.
        
        Args:
            zotero_client: Instance of pyzotero.Zotero
            rate_limiter: Optional custom rate limiter instance
        """
        self._client = zotero_client
        self._rate_limiter = rate_limiter or RateLimiter()

    def __getattr__(self, name: str) -> Any:
        """Wrap all methods of the Zotero client with rate limiting."""
        attr = getattr(self._client, name)

        # If it's a method, wrap it with rate limiting
        if callable(attr):
            return self._rate_limiter.with_retry(attr)

        return attr