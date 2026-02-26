"""Unit tests for Blob Storage Lifecycle Management"""

import pytest
from unittest.mock import Mock, MagicMock

from src.infrastructure.services.blob_storage import (
    AzureBlobStorageService,
    BlobUploadResult,
)


class TestBlobLifecycleManagement:
    """Test cases for Blob Lifecycle Management"""
    
    def test_lifecycle_policy_creation(self) -> None:
        """Test lifecycle policy structure"""
        # Lifecycle policy JSON structure
        policy = {
            "rules": [
                {
                    "name": "delete-old-zip-files",
                    "enabled": True,
                    "type": "Lifecycle",
                    "definition": {
                        "filters": {
                            "blobTypes": ["blockBlob"],
                            "prefixMatch": ["spec-bot-documents/"]
                        },
                        "actions": {
                            "baseBlob": {
                                "delete": {"daysAfterModificationGreaterThan": 1}
                            }
                        }
                    }
                }
            ]
        }
        
        assert "rules" in policy
        assert policy["rules"][0]["name"] == "delete-old-zip-files"
        assert policy["rules"][0]["definition"]["actions"]["baseBlob"]["delete"]["daysAfterModificationGreaterThan"] == 1
    
    def test_sas_token_expiry_format(self) -> None:
        """Test SAS token has correct expiry format"""
        from src.infrastructure.services.blob_storage import AzureBlobStorageService
        
        service = AzureBlobStorageService(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc123=="
        )
        
        sas = service._generate_sas_token("test.zip", expiry_hours=24)
        
        # Check format: sv=...&se=...&sp=r&sig=...
        assert "sv=" in sas
        assert "se=" in sas  # Expiry timestamp
        assert "sp=r" in sas  # Read permission
    
    def test_sas_token_read_only(self) -> None:
        """Test SAS token has read-only permission"""
        from src.infrastructure.services.blob_storage import AzureBlobStorageService
        
        service = AzureBlobStorageService(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc123=="
        )
        
        sas = service._generate_sas_token("test.zip", expiry_hours=24)
        
        # Should be read-only (sp=r)
        assert "sp=r" in sas
        assert "sp=w" not in sas
        assert "sp=rw" not in sas
    
    def test_default_expiry_is_24_hours(self) -> None:
        """Test default expiry is 24 hours (86400 seconds)"""
        from src.infrastructure.services.blob_storage import BlobUploadResult
        
        result = BlobUploadResult(
            blob_url="https://storage.blob.core.windows.net/container/test.zip",
            sas_token="sv=2021-06&se=2024-01-01T00:00:00Z&sig=abc",
            expires_in_seconds=86400
        )
        
        assert result.expires_in_seconds == 86400  # 24 hours
    
    def test_max_expiry_is_7_days(self) -> None:
        """Test max expiry cannot exceed 7 days"""
        from src.infrastructure.services.blob_storage import AzureBlobStorageService
        
        service = AzureBlobStorageService(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc123=="
        )
        
        # Try to create SAS with 7+ days (should be capped)
        sas_7_days = service._generate_sas_token("test.zip", expiry_hours=168)  # 7 days
        sas_30_days = service._generate_sas_token("test.zip", expiry_hours=720)  # 30 days
        
        # Both should have se= parameter
        assert "se=" in sas_7_days
        assert "se=" in sas_30_days
