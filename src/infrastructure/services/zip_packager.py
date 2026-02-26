"""Infrastructure - ZIP Packaging Service"""

import io
import logging
from typing import Any

import zipfile

logger = logging.getLogger(__name__)


class ZIPPackagingService:
    """Service for packaging documents into ZIP file in memory"""
    
    def create_zip(self, documents: dict[str, str]) -> bytes:
        """Create ZIP file from documents in memory
        
        Args:
            documents: Dictionary of filename -> content
            
        Returns:
            ZIP file content as bytes
        """
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in documents.items():
                # Convert content to bytes, handle None
                content_bytes = content.encode("utf-8") if content else b""
                zf.writestr(filename, content_bytes)
        
        zip_bytes = buffer.getvalue()
        logger.info(f"Created ZIP with {len(documents)} documents, size: {len(zip_bytes)} bytes")
        
        return zip_bytes
    
    def calculate_size(self, zip_bytes: bytes) -> int:
        """Calculate ZIP file size
        
        Args:
            zip_bytes: ZIP file content
            
        Returns:
            Size in bytes
        """
        return len(zip_bytes)
    
    def verify_zip(self, zip_bytes: bytes) -> bool:
        """Verify ZIP file is valid
        
        Args:
            zip_bytes: ZIP file content
            
        Returns:
            True if valid
        """
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                return zf.testzip() is None
        except Exception as e:
            logger.error(f"ZIP verification failed: {e}")
            return False
