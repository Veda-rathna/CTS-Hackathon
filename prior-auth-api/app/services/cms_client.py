"""CMS Coverage API Client.

Provides a unified interface to the official CMS MCD Coverage API.
https://api.coverage.cms.gov/docs/
"""
from __future__ import annotations

import httpx
import logging
from typing import Any, Dict

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CMSCoverageClient:
    """Client for querying the CMS Coverage API."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.cms_coverage_api_base_url
        self.timeout = self.settings.cms_coverage_api_timeout
        self.max_retries = self.settings.cms_coverage_api_max_retries
        self.enabled = self.settings.cms_coverage_api_enabled
        self._token: str | None = None

        self.headers = {"Accept": "application/json"}
        # If API key is manually provided in config, use it
        if hasattr(self.settings, "cms_coverage_api_key") and self.settings.cms_coverage_api_key:
            self.headers["Authorization"] = f"Bearer {self.settings.cms_coverage_api_key}"

    def _get_token(self) -> str | None:
        """Fetch the license agreement token from CMS API."""
        url = f"{self.base_url.rstrip('/')}/v1/metadata/license-agreement/"
        print(f"Requesting token from: {url}")
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers={"Accept": "application/json"})
                response.raise_for_status()
                data = response.json()
                print(f"Token response structure keys: {data.keys()}")
                
                # The response structure is usually {"data": [{"Token": "..."}]}
                token = None
                if "data" in data and len(data["data"]) > 0:
                    token = data["data"][0].get("Token")
                    
                if token:
                    self._token = token
                    self.headers["Authorization"] = f"Bearer {token}"
                    return token
        except Exception as e:
            print(f"Failed to retrieve CMS license agreement token: {e}")
            logger.warning("Failed to retrieve CMS license agreement token: %s", e)
        return None

    def _get(self, endpoint: str, params: dict | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Ensure we have a token (if we aren't using a fixed API key)
        if "Authorization" not in self.headers:
            print("Authorization not in headers, getting token...")
            self._get_token()
        else:
            print(f"Authorization is in headers: {self.headers}")

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(url, params=params, headers=self.headers)
                    
                    if response.status_code == 401:
                        # Token might be expired, get a new one
                        logger.info("CMS API returned 401. Refreshing token...")
                        new_token = self._get_token()
                        if new_token and attempt < self.max_retries:
                            continue # Try again
                            
                    if response.status_code == 404:
                        return None  # Not found is a valid response
                        
                    if response.status_code >= 400:
                        print(f"API Error {response.status_code}: {response.text}")
                        
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning("CMS API HTTP Error %s for %s (attempt %d)", e.response.status_code, url, attempt + 1)
                if attempt == self.max_retries:
                    raise
            except httpx.RequestError as e:
                logger.warning("CMS API Request Error for %s: %s (attempt %d)", url, e, attempt + 1)
                if attempt == self.max_retries:
                    raise
        return None


        
    def get_document(self, document_id: str, version: int | None = None) -> dict[str, Any] | None:
        """Fetch a specific LCD or Article by its document ID (e.g. L39054 or A12345)."""
        doc_type = "lcd" if document_id.upper().startswith("L") else "article"
        params = {}
        if doc_type == "lcd":
            params["lcdid"] = document_id[1:] if document_id.upper().startswith("L") else document_id
        else:
            params["articleid"] = document_id[1:] if document_id.upper().startswith("A") else document_id
            
        if version is not None:
            params[f"{doc_type}version"] = version
            
        return self._get(f"v1/data/{doc_type}", params=params)

    def get_ncd(self, ncd_id: str, version: int | None = None) -> dict[str, Any] | None:
        """Fetch a specific NCD by its ID."""
        params = {"ncdid": ncd_id}
        if version is not None:
            params["ncdversion"] = version
        return self._get("v1/data/ncd", params=params)


class MockCMSCoverageClient:
    """Mock implementation of the CMS Coverage API Client for testing."""
    
    def __init__(self) -> None:
        self.enabled = True
        # For testing, we can pre-populate responses
        self.mock_responses: Dict[str, Any] = {}
        self.hcpcs_mock_responses: Dict[str, Any] = {}

    def get_document(self, document_id: str, version: int | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        return self.mock_responses.get(document_id)

    def get_ncd(self, ncd_id: str, version: int | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        return self.mock_responses.get(ncd_id)
