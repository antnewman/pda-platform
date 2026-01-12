"""NISTA API client for GMPP quarterly return submission and data synchronization.

This module provides a high-level client for interacting with NISTA systems,
including quarterly return submission, project metadata fetching, and error handling.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import httpx

from pm_data_tools.integrations.nista.auth import NISTAAuthClient
from pm_data_tools.gmpp.models import QuarterlyReport


class SubmissionResult(BaseModel):
    """Result of NISTA quarterly return submission.

    Attributes:
        success: Whether submission succeeded
        submission_id: NISTA submission ID (if successful)
        timestamp: Submission timestamp
        validation_warnings: Non-critical validation warnings
        error: Error message (if failed)
        details: Additional error details (if failed)
    """

    success: bool = Field(..., description="Submission success status")
    submission_id: Optional[str] = Field(
        None,
        description="NISTA submission ID (assigned on success)"
    )
    timestamp: datetime = Field(..., description="Submission timestamp")
    validation_warnings: List[str] = Field(
        default_factory=list,
        description="Non-critical validation warnings"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if submission failed"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )


class ProjectMetadata(BaseModel):
    """NISTA project master registry metadata.

    Attributes:
        nista_project_code: Official NISTA project code
        project_name: Official project name from NISTA registry
        department: Owning department
        sro_name: Current Senior Responsible Owner
        sro_email: SRO email address
        category: Project category
        start_date: Project start date
        baseline_completion: Baseline completion date
        last_updated: Last update timestamp in NISTA registry
    """

    nista_project_code: str
    project_name: str
    department: str
    sro_name: str
    sro_email: str
    category: str
    start_date: str
    baseline_completion: str
    last_updated: datetime


class NISTAAPIClient:
    """Client for NISTA API integration.

    Provides methods for:
    - Submitting GMPP quarterly returns
    - Fetching project metadata from NISTA master registry
    - Syncing project data
    - Error handling and retry logic

    Example:
        >>> from pm_data_tools.integrations.nista import NISTAAuthClient, NISTAAPIClient
        >>> auth = NISTAAuthClient(config)
        >>> client = NISTAAPIClient(auth)
        >>>
        >>> result = await client.submit_quarterly_return(
        ...     project_id="DFT-HSR-001",
        ...     report=quarterly_report
        ... )
        >>> if result.success:
        ...     print(f"Submitted: {result.submission_id}")
    """

    def __init__(self, auth_client: NISTAAuthClient):
        """Initialize NISTA API client.

        Args:
            auth_client: Configured authentication client
        """
        self.auth = auth_client
        self.base_url = auth_client.config.base_url
        self._http_client: Optional[httpx.AsyncClient] = None

    async def submit_quarterly_return(
        self,
        project_id: str,
        report: QuarterlyReport,
        validate_before_submit: bool = True,
    ) -> SubmissionResult:
        """Submit GMPP quarterly return to NISTA.

        Args:
            project_id: Internal project identifier
            report: Complete quarterly report
            validate_before_submit: Run local validation before submission

        Returns:
            Submission result with ID or error details

        Raises:
            httpx.HTTPError: If network error occurs
            ValueError: If validation fails and validate_before_submit=True
        """
        # Pre-submission validation (if enabled)
        if validate_before_submit:
            from pm_data_tools.schemas.nista import NISTAValidator

            validator = NISTAValidator(strictness="STANDARD")
            validation = validator.validate(report.model_dump())

            if not validation.compliant:
                raise ValueError(
                    f"Report validation failed: {validation.issues[0].message}"
                )

        # Get access token
        token = await self.auth.get_access_token()

        # Prepare submission data
        submission_data = report.model_dump(mode="json")

        # Add submission metadata
        submission_data["_submission_metadata"] = {
            "submitted_at": datetime.utcnow().isoformat(),
            "client_version": "pm-data-tools-0.2.0",
            "client_name": "pda-platform",
        }

        # Submit to NISTA API
        client = await self._get_http_client()

        try:
            response = await client.post(
                f"{self.base_url}/gmpp/projects/{project_id}/quarterly-returns",
                json=submission_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-NISTA-Project-ID": project_id,
                    "X-Submission-Date": datetime.utcnow().isoformat(),
                },
                timeout=self.auth.config.timeout_seconds,
            )

            # Log submission to audit trail
            from pm_data_tools.integrations.nista.audit import AuditLogger

            AuditLogger().log_submission(
                project_id=project_id,
                report=report,
                response_status=response.status_code,
                response_body=response.json() if response.status_code == 200 else None,
            )

            # Handle successful submission
            if response.status_code == 200:
                response_data = response.json()
                return SubmissionResult(
                    success=True,
                    submission_id=response_data.get("submission_id"),
                    timestamp=datetime.utcnow(),
                    validation_warnings=response_data.get("warnings", []),
                )

            # Handle submission failure
            error_data = response.json()
            return SubmissionResult(
                success=False,
                timestamp=datetime.utcnow(),
                error=error_data.get("error", f"HTTP {response.status_code}"),
                details=error_data.get("details"),
            )

        except httpx.HTTPStatusError as e:
            # HTTP error response
            return SubmissionResult(
                success=False,
                timestamp=datetime.utcnow(),
                error=f"HTTP {e.response.status_code}: {e.response.text}",
            )

        except httpx.RequestError as e:
            # Network/connection error
            return SubmissionResult(
                success=False,
                timestamp=datetime.utcnow(),
                error=f"Request failed: {str(e)}",
            )

    async def fetch_project_metadata(self, project_id: str) -> ProjectMetadata:
        """Fetch project metadata from NISTA master registry.

        Args:
            project_id: NISTA project code or internal project ID

        Returns:
            Project metadata from NISTA registry

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If project not found
        """
        token = await self.auth.get_access_token()
        client = await self._get_http_client()

        try:
            response = await client.get(
                f"{self.base_url}/gmpp/projects/{project_id}/metadata",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                timeout=self.auth.config.timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()
            return ProjectMetadata(**data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Project not found in NISTA registry: {project_id}") from e
            raise

    async def fetch_guidance(self, topic: str) -> Dict[str, Any]:
        """Fetch latest NISTA guidance documents.

        Args:
            topic: Guidance topic (e.g., 'teal_book', 'dca_ratings', 'assurance')

        Returns:
            Guidance document content

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If guidance not found
        """
        token = await self.auth.get_access_token()
        client = await self._get_http_client()

        try:
            response = await client.get(
                f"{self.base_url}/guidance/{topic}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                timeout=self.auth.config.timeout_seconds,
            )
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Guidance not found: {topic}") from e
            raise

    async def get_submission_history(
        self,
        project_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get submission history for a project.

        Args:
            project_id: NISTA project code or internal project ID
            limit: Maximum number of submissions to return

        Returns:
            List of previous submissions with metadata

        Raises:
            httpx.HTTPError: If request fails
        """
        token = await self.auth.get_access_token()
        client = await self._get_http_client()

        response = await client.get(
            f"{self.base_url}/gmpp/projects/{project_id}/submissions",
            params={"limit": limit},
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=self.auth.config.timeout_seconds,
        )
        response.raise_for_status()

        return response.json().get("submissions", [])

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Configured async HTTP client
        """
        if self._http_client is not None:
            return self._http_client

        self._http_client = httpx.AsyncClient(
            timeout=self.auth.config.timeout_seconds,
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

    async def __aenter__(self) -> "NISTAAPIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
