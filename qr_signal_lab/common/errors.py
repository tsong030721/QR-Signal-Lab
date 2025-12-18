"""
Base template for raising specific errors.
    1. Never return None for failures.
    2. Raise as close to the source of failure as possible.
    3. Catch only at boundaries - not helpers.
""" 

class BaseError(Exception):
    """Base class for all errors."""

# Fail-fast: config / inputs
class ConfigError(BaseError):
    """Invalid configuration: missing env vars, invalid paths, etc."""

class InvalidRequest(BaseError):
    """Invalid run request: bad symbols, dates, frequency, etc."""

# External dependency failures (retryable sometimes)
class DataSourceError(BaseError):
    """Upstream data provider / IO failed."""

class NetworkError(DataSourceError):
    """Timeouts, connection errors, 5xx, etc."""

class RateLimitError(DataSourceError):
    """429s / throttling."""

class AuthError(DataSourceError):
    """401/403 from provider."""


# Data came back but is unusable (not retryable)
class DataValidationError(BaseError):
    """Data missing required fields / wrong types / unparsable."""

class EmptyData(BaseError):
    """Succeeded but effectively empty."""

class SchemaMismatch(BaseError):
    """Columns/types differ from what pipeline expects."""
