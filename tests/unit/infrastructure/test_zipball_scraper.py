"""Unit tests for ZipballScraper (memory-based GitHub repository download)"""

import pytest
import io
import zipfile
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass


class TestZipballScraper:
    """Test cases for ZipballScraper with memory-based processing"""
    
    def test_initialization(self) -> None:
        """Test scraper initialization"""
        from src.infrastructure.services.zipball_scraper import ZipballScraper
        
        scraper = ZipballScraper(token="test_token")
        assert scraper._token == "test_token"
    
    def test_initialization_without_token(self) -> None:
        """Test scraper initialization without token"""
        from src.infrastructure.services.zipball_scraper import ZipballScraper
        
        scraper = ZipballScraper()
        assert scraper._token is None
    
    def test_fetch_zipball_url(self) -> None:
        """Test zipball URL generation"""
        from src.infrastructure.services.zipball_scraper import ZipballScraper
        
        scraper = ZipballScraper()
        
        # Test URL generation for owner/repo
        url = scraper._get_zipball_url("owner", "repo")
        assert url == "https://api.github.com/repos/owner/repo/zipball"
        
        # Test URL with branch
        url = scraper._get_zipball_url("owner", "repo", "main")
        assert url == "https://api.github.com/repos/owner/repo/zipball/ref/main"
    
    def test_parse_zipball_response(self) -> None:
        """Test zipball response parsing from bytes"""
        from src.infrastructure.services.zipball_scraper import ZipballScraper
        
        scraper = ZipballScraper()
        
        # Create a minimal ZIP file in memory for testing
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test-repo/README.md", "# Test Project")
            zf.writestr("test-repo/src/main.py", "print('hello')")
        
        zip_buffer.seek(0)
        
        # Parse the zip
        files = scraper._parse_zipball(zip_buffer.read())
        
        assert len(files) >= 2
        file_paths = [f.path for f in files]
        assert any("README.md" in p for p in file_paths)
        assert any("main.py" in p for p in file_paths)
    
    def test_filter_key_files(self) -> None:
        """Test key file filtering (max 30 files, 5000 chars each)"""
        from src.infrastructure.services.zipball_scraper import ZipballScraper
        from src.domain.entities.repository import SourceFile, FileType
        
        scraper = ZipballScraper()
        
        # Create mock source files
        mock_files = [
            SourceFile(path="src/controllers/user.py", content="x" * 1000, file_type=FileType.CONTROLLER),
            SourceFile(path="src/models/user.py", content="x" * 1000, file_type=FileType.ENTITY),
            SourceFile(path="pom.xml", content="x" * 1000, file_type=FileType.CONFIG),
            SourceFile(path="README.md", content="x" * 1000, file_type=FileType.OTHER),
        ]
        
        # Filter key files
        key_files = scraper._filter_key_files(mock_files, max_files=30)
        
        # Should exclude README.md (OTHER type)
        assert len(key_files) == 3
        assert all(f.file_type != FileType.OTHER for f in key_files)
    
    def test_truncate_content(self) -> None:
        """Test content truncation to 5000 chars"""
        from src.infrastructure.services.zipball_scraper import ZipballScraper
        
        scraper = ZipballScraper()
        
        long_content = "a" * 10000
        truncated = scraper._truncate_content(long_content, max_chars=5000)
        
        assert len(truncated) == 5000
        assert truncated == "a" * 5000
    
    @patch("requests.Session")
    def test_fetch_repository_success(self, mock_session_class: MagicMock) -> None:
        """Test successful repository fetch"""
        from src.infrastructure.services.zipball_scraper import ZipballScraper
        
        # Create mock zip content
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test-repo/README.md", "# Test")
            zf.writestr("test-repo/src/main.py", "print('hello')")
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = zip_content
        mock_response.headers = {"content-disposition": "attachment; filename=repo.zip"}
        
        # Mock session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        scraper = ZipballScraper()
        files = scraper.fetch_repository("owner", "repo")
        
        assert len(files) >= 2
    
    @patch("requests.Session")
    def test_fetch_repository_rate_limit(self, mock_session_class: MagicMock) -> None:
        """Test rate limit handling"""
        from src.infrastructure.services.zipball_scraper import ZipballScraper
        
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        scraper = ZipballScraper()
        
        with pytest.raises(Exception) as exc_info:
            scraper.fetch_repository("owner", "repo")
        
        assert "rate limit" in str(exc_info.value).lower() or "403" in str(exc_info.value)
