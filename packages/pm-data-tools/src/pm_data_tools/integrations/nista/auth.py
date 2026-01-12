"""NISTA authentication client with OAuth 2.0 and mTLS support.

This module provides secure authentication for NISTA API access using:
- OAuth 2.0 client credentials flow
- Optional mutual TLS (mTLS) for enhanced security
- Token caching and automatic refresh
- Support for sandbox and production environments
"""

from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import httpx
import os


class NISTAAuthConfig(BaseModel):
    """Configuration for NISTA authentication.

    Attributes:
        client_id: OAuth 2.0 client ID (provided by NISTA)
        client_secret: OAuth 2.0 client secret
        certificate_path: Optional path to client certificate for mTLS
        private_key_path: Optional path to private key for mTLS
        environment: Environment ('sandbox' or 'production')
        base_url: Base URL for NISTA API (auto-configured by environment)
        token_url: OAuth 2.0 token endpoint (auto-configured by environment)
        timeout_seconds: Request timeout in seconds
    """

    client_id: str = Field(..., min_length=1, description="OAuth 2.0 client ID")
    client_secret: str = Field(..., min_length=1, description="OAuth 2.0 client secret")
    certificate_path: Optional[str] = Field(
        None,
        description="Path to client certificate for mTLS (.pem format)"
    )
    private_key_path: Optional[str] = Field(
        None,
        description="Path to private key for mTLS (.pem format)"
    )
    environment: str = Field(
        default="sandbox",
        pattern=r"^(sandbox|production)$",
        description="NISTA environment"
    )
    base_url: Optional[str] = Field(
        None,
        description="Override base URL (auto-configured if not provided)"
    )
    token_url: Optional[str] = Field(
        None,
        description="Override token URL (auto-configured if not provided)"
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Request timeout in seconds"
    )

    def model_post_init(self, __context) -> None:
        """Auto-configure URLs based on environment if not provided."""
        if self.base_url is None:
            if self.environment == "sandbox":
                self.base_url = "https://api-sandbox.nista.gov.uk/v1"
            else:
                self.base_url = "https://api.nista.gov.uk/v1"

        if self.token_url is None:
            if self.environment == "sandbox":
                self.token_url = "https://auth-sandbox.nista.gov.uk/oauth/token"
            else:
                self.token_url = "https://auth.nista.gov.uk/oauth/token"

    @classmethod
    def from_env(cls) -> "NISTAAuthConfig":
        """Create configuration from environment variables.

        Environment variables:
            NISTA_CLIENT_ID: OAuth client ID
            NISTA_CLIENT_SECRET: OAuth client secret
            NISTA_CERT_PATH: Path to client certificate (optional)
            NISTA_KEY_PATH: Path to private key (optional)
            NISTA_ENVIRONMENT: 'sandbox' or 'production' (default: sandbox)
            NISTA_API_URL: Override base URL (optional)
            NISTA_TOKEN_URL: Override token URL (optional)

        Returns:
            NISTAAuthConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        client_id = os.getenv("NISTA_CLIENT_ID")
        client_secret = os.getenv("NISTA_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError(
                "NISTA_CLIENT_ID and NISTA_CLIENT_SECRET environment variables required"
            )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            certificate_path=os.getenv("NISTA_CERT_PATH"),
            private_key_path=os.getenv("NISTA_KEY_PATH"),
            environment=os.getenv("NISTA_ENVIRONMENT", "sandbox"),
            base_url=os.getenv("NISTA_API_URL"),
            token_url=os.getenv("NISTA_TOKEN_URL"),
        )


class NISTAAuthClient:
    """OAuth 2.0 authentication client for NISTA API.

    Handles token acquisition, caching, and automatic refresh using OAuth 2.0
    client credentials flow. Supports optional mTLS for enhanced security.

    Example:
        >>> config = NISTAAuthConfig(
        ...     client_id="your_id",
        ...     client_secret="your_secret",
        ...     environment="sandbox"
        ... )
        >>> auth = NISTAAuthClient(config)
        >>> token = await auth.get_access_token()
        >>> # Token is cached and automatically refreshed when expired
    """

    def __init__(self, config: NISTAAuthConfig):
        """Initialize authentication client.

        Args:
            config: NISTA authentication configuration
        """
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def get_access_token(self) -> str:
        """Get valid access token (cached or freshly fetched).

        Returns:
            Valid OAuth 2.0 access token

        Raises:
            httpx.HTTPError: If token fetch fails
            ValueError: If authentication fails
        """
        if self._is_token_valid():
            return self._access_token

        return await self._fetch_new_token()

    async def refresh_token(self) -> str:
        """Force refresh of access token.

        Returns:
            Newly fetched access token

        Raises:
            httpx.HTTPError: If token fetch fails
            ValueError: If authentication fails
        """
        return await self._fetch_new_token()

    def _is_token_valid(self) -> bool:
        """Check if cached token is still valid.

        Returns:
            True if token exists and not expired (with 60s buffer)
        """
        if not self._access_token or not self._token_expires:
            return False

        # Refresh if token expires within 60 seconds
        buffer = timedelta(seconds=60)
        return datetime.utcnow() < (self._token_expires - buffer)

    async def _fetch_new_token(self) -> str:
        """Fetch new access token from NISTA OAuth server.

        Uses OAuth 2.0 client credentials flow:
        POST /oauth/token
        grant_type=client_credentials
        client_id=...
        client_secret=...

        Returns:
            Access token string

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If authentication fails or response invalid
        """
        client = await self._get_http_client()

        # OAuth 2.0 client credentials request
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            response = await client.post(
                self.config.token_url,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"NISTA authentication failed: {e.response.status_code} {e.response.text}"
            ) from e

        # Parse token response
        token_data = response.json()

        if "access_token" not in token_data:
            raise ValueError("Invalid token response: missing access_token")

        # Cache token and expiration
        self._access_token = token_data["access_token"]

        expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
        self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in)

        return self._access_token

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with mTLS if configured.

        Returns:
            Configured async HTTP client

        Raises:
            FileNotFoundError: If certificate or key file not found
        """
        if self._http_client is not None:
            return self._http_client

        # Configure mTLS if certificate paths provided
        cert = None
        if self.config.certificate_path and self.config.private_key_path:
            if not os.path.exists(self.config.certificate_path):
                raise FileNotFoundError(
                    f"Certificate not found: {self.config.certificate_path}"
                )
            if not os.path.exists(self.config.private_key_path):
                raise FileNotFoundError(
                    f"Private key not found: {self.config.private_key_path}"
                )

            cert = (self.config.certificate_path, self.config.private_key_path)

        self._http_client = httpx.AsyncClient(
            cert=cert,
            timeout=self.config.timeout_seconds,
            headers={
                "User-Agent": "pda-platform/pm-data-tools NISTA Integration",
            },
        )

        return self._http_client

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "NISTAAuthClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
