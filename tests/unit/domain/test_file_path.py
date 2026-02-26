"""Unit tests for Domain Value Objects - FilePath"""

import pytest

from src.domain.value_objects import FilePath


class TestFilePath:
    """Test cases for FilePath value object"""
    
    def test_valid_file_path(self) -> None:
        """Test valid file path"""
        fp = FilePath(value="src/controllers/user.py")
        assert fp.value == "src/controllers/user.py"
        assert fp.extension == "py"
        assert fp.name == "user.py"
        assert fp.directory == "src/controllers"
    
    def test_file_path_no_extension(self) -> None:
        """Test file path without extension"""
        fp = FilePath(value="Makefile")
        assert fp.extension == ""
        assert fp.name == "Makefile"
        assert fp.directory == ""
    
    def test_file_path_deep_directory(self) -> None:
        """Test file path with deep directory structure"""
        fp = FilePath(value="src/app/modules/users/controllers/user_controller.py")
        assert fp.extension == "py"
        assert fp.name == "user_controller.py"
        assert fp.directory == "src/app/modules/users/controllers"
    
    def test_invalid_empty_path(self) -> None:
        """Test empty path raises error"""
        with pytest.raises(ValueError, match="cannot be empty"):
            FilePath(value="")
    
    def test_path_immutable(self) -> None:
        """Test FilePath is immutable"""
        fp = FilePath(value="src/main.py")
        with pytest.raises(AttributeError):
            fp.value = "new/path.py"  # type: ignore[assignment]
    
    def test_path_equality(self) -> None:
        """Test FilePath equality"""
        fp1 = FilePath(value="src/main.py")
        fp2 = FilePath(value="src/main.py")
        assert fp1 == fp2
