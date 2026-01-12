"""NISTA (National Infrastructure and Service Transformation Authority) integration.

This module provides secure integration with NISTA systems for GMPP quarterly
reporting, including:
- OAuth 2.0 + mTLS authentication
- GMPP quarterly return submission
- Project metadata synchronization
- Comprehensive audit logging (7-year retention)

Example:
    >>> from pm_data_tools.integrations.nista import NISTAAuthClient, NISTAAPIClient
    >>> auth_config = NISTAAuthConfig(
    ...     client_id="your_id",
    ...     client_secret="your_secret",
    ...     environment="sandbox"
    ... )
    >>> auth = NISTAAuthClient(auth_config)
    >>> client = NISTAAPIClient(auth)
    >>> result = await client.submit_quarterly_return(project_id, report)
"""

from pm_data_tools.integrations.nista.auth import NISTAAuthClient, NISTAAuthConfig
from pm_data_tools.integrations.nista.client import NISTAAPIClient, SubmissionResult
from pm_data_tools.integrations.nista.audit import AuditLogger, AuditEntry

__all__ = [
    "NISTAAuthClient",
    "NISTAAuthConfig",
    "NISTAAPIClient",
    "SubmissionResult",
    "AuditLogger",
    "AuditEntry",
]
