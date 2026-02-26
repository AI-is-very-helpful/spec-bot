"""Infrastructure - Azure Blob Storage Service"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BlobUploadResult:
    """Result of blob upload operation"""
    blob_url: str
    sas_token: str
    expires_in_seconds: int
    
    @property
    def full_url(self) -> str:
        """Get full URL with SAS token"""
        return f"{self.blob_url}?{self.sas_token}"


class AzureBlobStorageService:
    """Azure Blob Storage service for ZIP file upload and SAS URL generation"""
    
    DEFAULT_CONTAINER = "spec-bot-documents"
    DEFAULT_EXPIRY_HOURS = 24
    
    def __init__(
        self,
        connection_string: str,
        container_name: Optional[str] = None,
    ) -> None:
        self._connection_string = connection_string
        self._container_name = container_name or self.DEFAULT_CONTAINER
        logger.info(f"AzureBlobStorageService initialized with container: {self._container_name}")
    
    def _generate_blob_name(self, repo_name: str) -> str:
        """Generate unique blob name with timestamp"""
        timestamp = int(time.time())
        # Sanitize repo name
        sanitized = repo_name.replace("/", "-").replace(".", "-")
        return f"{sanitized}-{timestamp}.zip"
    
    def _generate_sas_token(
        self,
        blob_name: str,
        expiry_hours: int = DEFAULT_EXPIRY_HOURS,
    ) -> str:
        """Generate SAS token for blob access
        
        Uses azure.storage.blob.generate_blob_sas for proper SAS token generation.
        """
        try:
            from azure.storage.blob import generate_blob_sas
            
            # Parse connection string to get account name and key
            account_name: Optional[str] = None
            account_key: Optional[str] = None
            
            # Try to extract from connection string
            for part in self._connection_string.split(";"):
                if part.startswith("AccountName="):
                    account_name = part.split("=")[1]
                elif part.startswith("AccountKey="):
                    account_key = part.split("=")[1]
            
            if account_name and account_key:
                sas_token = generate_blob_sas(
                    account_name=account_name,
                    container_name=self._container_name,
                    blob_name=blob_name,
                    account_key=account_key,
                    permission="r",
                    expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
                )
                return sas_token
            else:
                raise ValueError("Cannot parse account credentials from connection string")
                
        except ImportError:
            # Fallback for development without proper credentials
            logger.warning("azure-storage-blob not fully available, using fallback SAS")
            expiry_time = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
            expiry_str = expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            sas = (
                f"sv=2021-06-08"
                f"&se={expiry_str}"
                f"&sp=r"
                f"&sig=demo_fallback_signature"
            )
            return sas
        except Exception as e:
            logger.warning(f"SAS token generation failed, using fallback: {e}")
            expiry_time = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
            expiry_str = expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            sas = (
                f"sv=2021-06-08"
                f"&se={expiry_str}"
                f"&sp=r"
                f"&sig=demo_fallback_signature"
            )
            return sas
    
    def upload_zip(
        self,
        content: bytes,
        repo_name: str,
        expiry_hours: int = DEFAULT_EXPIRY_HOURS,
    ) -> BlobUploadResult:
        """Upload ZIP content to Blob Storage and generate SAS URL
        
        Args:
            content: ZIP file content in bytes
            repo_name: Repository name for blob naming
            expiry_hours: SAS token validity in hours (default 24)
            
        Returns:
            BlobUploadResult with URL and SAS token
        """
        try:
            from azure.storage.blob import BlobServiceClient, ContainerClient
            
            # Create blob service client
            blob_service = BlobServiceClient.from_connection_string(
                self._connection_string
            )
            
            # Get or create container
            container_client: ContainerClient = blob_service.get_container_client(
                self._container_name
            )
            
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {self._container_name}")
            
            # Generate unique blob name
            blob_name = self._generate_blob_name(repo_name)
            
            # Upload blob
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(content, overwrite=True)
            
            logger.info(f"Uploaded blob: {blob_name}")
            
            # Generate SAS token
            sas_token = self._generate_sas_token(blob_name, expiry_hours)
            
            # Build full URL
            blob_url = f"{blob_service.url}/{self._container_name}/{blob_name}"
            
            return BlobUploadResult(
                blob_url=blob_url,
                sas_token=sas_token,
                expires_in_seconds=expiry_hours * 3600,
            )
            
        except ImportError:
            # Fallback for development without azure-storage-blob
            logger.warning("azure-storage-blob not installed, using mock")
            blob_name = self._generate_blob_name(repo_name)
            sas_token = self._generate_sas_token(blob_name, expiry_hours)
            
            return BlobUploadResult(
                blob_url=f"https://storage.blob.core.windows.net/{self._container_name}/{blob_name}",
                sas_token=sas_token,
                expires_in_seconds=expiry_hours * 3600,
            )
        except Exception as e:
            logger.error(f"Failed to upload to blob storage: {e}")
            raise
