class PaddleOCRError(Exception):
    """Base exception for all tool errors."""


class RateLimitError(PaddleOCRError):
    """HTTP 429 — daily quota exhausted."""


class JobFailedError(PaddleOCRError):
    """API reports job state == 'failed'."""


class JobTimeoutError(PaddleOCRError):
    """Polling exceeded the configured timeout."""
