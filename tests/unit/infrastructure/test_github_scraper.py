"""Unit tests for GitHub Scraper with config files"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.repositories.github import PyGitHubRepository


class TestPyGitHubRepository:
    """Test cases for PyGitHubRepository"""
    
    @patch("src.infrastructure.repositories.github.Github")
    def test_service_initialization(self, mock_github: MagicMock) -> None:
        """Test repository initialization"""
        repo = PyGitHubRepository(token="test_token")
        assert repo._token == "test_token"
    
    @patch("src.infrastructure.repositories.github.Github")
    def test_service_initialization_without_token(self, mock_github: MagicMock) -> None:
        """Test repository initialization without token"""
        repo = PyGitHubRepository()
        assert repo._token is None
    
    def test_is_key_file_python_controller(self) -> None:
        """Test Python controller detection"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("src/controllers/user.py") is True
        assert repo._is_key_file("src/routes/api.py") is True
        assert repo._is_key_file("api/users.py") is True
    
    def test_is_key_file_java_controller(self) -> None:
        """Test Java controller detection"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("src/main/java/com/example/controller/UserController.java") is True
    
    def test_is_key_file_config_maven(self) -> None:
        """Test Maven config file detection"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("pom.xml") is True
        assert repo._is_key_file("project/pom.xml") is True
    
    def test_is_key_file_config_gradle(self) -> None:
        """Test Gradle config file detection"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("build.gradle") is True
        assert repo._is_key_file("app/build.gradle.kts") is True
    
    def test_is_key_file_config_docker(self) -> None:
        """Test Docker config file detection"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("docker-compose.yml") is True
        assert repo._is_key_file("Dockerfile") is True
        assert repo._is_key_file("docker/Dockerfile.prod") is True
    
    def test_is_key_file_config_yaml(self) -> None:
        """Test YAML config file detection"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("application.yml") is True
        assert repo._is_key_file("config/application.yaml") is True
        assert repo._is_key_file("src/main/resources/application.yml") is True
    
    def test_is_key_file_config_json(self) -> None:
        """Test JSON config file detection"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("package.json") is True
        assert repo._is_key_file("tsconfig.json") is True
    
    def test_is_key_file_config_requirements(self) -> None:
        """Test Python requirements detection"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("requirements.txt") is True
        assert repo._is_key_file("requirements-dev.txt") is True
        assert repo._is_key_file("pyproject.toml") is True
    
    def test_is_key_file_ignore_dirs(self) -> None:
        """Test ignore directories"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("node_modules/package.json") is False
        assert repo._is_key_file(".git/config") is False
        assert repo._is_key_file("__pycache__/file.py") is False
        assert repo._is_key_file("tests/test.py") is False
    
    def test_is_key_file_ignore_non_code(self) -> None:
        """Test non-code files are ignored"""
        repo = PyGitHubRepository()
        
        assert repo._is_key_file("README.md") is False
        assert repo._is_key_file("docs/guide.md") is False
    
    def test_classify_file_type_controller(self) -> None:
        """Test file type classification - controller"""
        repo = PyGitHubRepository()
        
        assert repo._classify_file_type("src/controllers/user.py") == "controller"
        assert repo._classify_file_type("api/routes/users.py") == "controller"
    
    def test_classify_file_type_config(self) -> None:
        """Test file type classification - config"""
        repo = PyGitHubRepository()
        
        assert repo._classify_file_type("pom.xml") == "config"
        assert repo._classify_file_type("application.yml") == "config"
        assert repo._classify_file_type("docker-compose.yml") == "config"
