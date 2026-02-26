"""Unit tests for Azure Blob Storage Service"""

import io
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.infrastructure.services.blob_storage import (
    AzureBlobStorageService,
    BlobUploadResult,
)


class TestBlobUploadResult:
    """Test cases for BlobUploadResult"""
    
    def test_blob_upload_result_creation(self) -> None:
        """Test creating BlobUploadResult"""
        result = BlobUploadResult(
            blob_url="https://storage.blob.core.windows.net/container/doc.zip",
            sas_token="sv=2021-06&se=2024-01-01T00:00:00Z&sig=abc123",
            expires_in_seconds=86400
        )
        
        assert result.blob_url == "https://storage.blob.core.windows.net/container/doc.zip"
        assert result.sas_token == "sv=2021-06&se=2024-01-01T00:00:00Z&sig=abc123"
        assert result.expires_in_seconds == 86400
    
    def test_full_url_property(self) -> None:
        """Test full URL with SAS token"""
        result = BlobUploadResult(
            blob_url="https://storage.blob.core.windows.net/container/doc.zip",
            sas_token="sv=2021-06&se=2024-01-01T00:00:00Z",
            expires_in_seconds=86400
        )
        
        full_url = result.full_url
        assert "https://storage.blob.core.windows.net/container/doc.zip?" in full_url
        assert "sv=2021-06" in full_url


class TestAzureBlobStorageService:
    """Test cases for AzureBlobStorageService"""
    
    def test_service_initialization(self) -> None:
        """Test service initialization"""
        service = AzureBlobStorageService(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc123==",
            container_name="documents"
        )
        
        assert service._container_name == "documents"
    
    def test_service_initialization_defaults(self) -> None:
        """Test service with default container"""
        service = AzureBlobStorageService(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc123=="
        )
        
        assert service._container_name == "spec-bot-documents"
    
    def test_generate_blob_name(self) -> None:
        """Test generating unique blob name"""
        service = AzureBlobStorageService(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc123=="
        )
        
        import time
        timestamp = int(time.time())
        
        blob_name = service._generate_blob_name("owner-repo")
        
        assert blob_name.startswith(f"owner-repo-{timestamp}")
        assert blob_name.endswith(".zip")
    
    def test_generate_sas_token(self) -> None:
        """Test SAS token generation"""
        service = AzureBlobStorageService(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc123=="
        )
        
        # Test with default expiry (24 hours)
        sas = service._generate_sas_token("test-blob.zip", expiry_hours=24)
        
        assert "sv=" in sas  # Storage version
        assert "se=" in sas  # Expiry time
        assert "sig=" in sas  # Signature
        assert "sp=r" in sas  # Read permission
    
    def test_generate_sas_token_custom_expiry(self) -> None:
        """Test SAS token with custom expiry"""
        service = AzureBlobStorageService(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc123=="
        )
        
        sas = service._generate_sas_token("test-blob.zip", expiry_hours=2)
        
        assert "sv=" in sas
        assert "se=" in sas
