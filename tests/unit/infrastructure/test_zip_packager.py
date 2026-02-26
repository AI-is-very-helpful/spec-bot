"""Unit tests for ZIP Packaging Service"""

import io
import pytest
import zipfile

from src.infrastructure.services.zip_packager import ZIPPackagingService


class TestZIPPackagingService:
    """Test cases for ZIPPackagingService"""
    
    def test_create_zip_from_documents(self) -> None:
        """Test creating ZIP from document package"""
        service = ZIPPackagingService()
        
        documents = {
            "api_spec.md": "# API Specification",
            "erd.md": "# ERD",
            "sequence.md": "# Sequence",
        }
        
        zip_bytes = service.create_zip(documents)
        
        # Verify ZIP is valid
        assert len(zip_bytes) > 0
        
        # Verify ZIP contents
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            names = zf.namelist()
            assert "api_spec.md" in names
            assert "erd.md" in names
            assert "sequence.md" in names
    
    def test_create_zip_all_5_documents(self) -> None:
        """Test creating ZIP with all 5 documents (5 agents)"""
        service = ZIPPackagingService()
        
        documents = {
            "api_spec.md": "# API Spec",
            "erd.md": "# ERD",
            "architecture.md": "# Architecture",
            "tech_stack.md": "# Tech Stack",
            "schema.sql": "-- DDL",
        }
        
        zip_bytes = service.create_zip(documents)
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert len(zf.namelist()) == 5
    
    def test_create_zip_content_verification(self) -> None:
        """Test ZIP content is correct"""
        service = ZIPPackagingService()
        
        documents = {
            "api_spec.md": "API Specification Content",
            "test.txt": "Test Content",
        }
        
        zip_bytes = service.create_zip(documents)
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert zf.read("api_spec.md").decode() == "API Specification Content"
            assert zf.read("test.txt").decode() == "Test Content"
    
    def test_create_zip_with_empty_content(self) -> None:
        """Test ZIP with empty document content"""
        service = ZIPPackagingService()
        
        documents = {
            "empty.md": "",
        }
        
        zip_bytes = service.create_zip(documents)
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            content = zf.read("empty.md").decode()
            assert content == ""
    
    def test_create_zip_returns_bytes(self) -> None:
        """Test returned ZIP is bytes"""
        service = ZIPPackagingService()
        
        documents = {"test.md": "content"}
        
        result = service.create_zip(documents)
        
        assert isinstance(result, bytes)
    
    def test_calculate_size(self) -> None:
        """Test size calculation"""
        service = ZIPPackagingService()
        
        documents = {
            "api_spec.md": "# API Specification",
            "erd.md": "# ERD",
        }
        
        zip_bytes = service.create_zip(documents)
        size = service.calculate_size(zip_bytes)
        
        assert size == len(zip_bytes)
        assert size > 0
