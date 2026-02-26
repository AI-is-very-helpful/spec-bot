"""Unit tests for ArtifactRouter (intelligent file routing per document type)"""

import pytest
from dataclasses import dataclass, field
from src.domain.entities.repository import SourceFile, FileType


class TestArtifactRouter:
    """Test cases for ArtifactRouter - intelligent file routing for 7 document types"""
    
    def test_initialization(self) -> None:
        """Test router initialization"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        assert router is not None
    
    def test_route_to_api_spec(self) -> None:
        """Test routing files for API Specification document"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        # Files that should be routed to API spec
        api_files = [
            SourceFile(path="src/controllers/user.py", content="def create_user()", file_type=FileType.CONTROLLER),
            SourceFile(path="api/routes/users.py", content="router.post('/users')", file_type=FileType.CONTROLLER),
            SourceFile(path="src/dto/user_request.py", content="class UserRequest", file_type=FileType.ENTITY),
            SourceFile(path="src/dto/user_response.py", content="class UserResponse", file_type=FileType.ENTITY),
        ]
        
        result = router.route_to_api_spec(api_files)
        
        assert len(result) >= 2
        paths = [f.path for f in result]
        assert any("controller" in p for p in paths)
    
    def test_route_to_erd(self) -> None:
        """Test routing files for ERD document"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        # Files that should be routed to ERD
        entity_files = [
            SourceFile(path="src/models/user.py", content="class User", file_type=FileType.ENTITY),
            SourceFile(path="src/entity/order.py", content="class Order", file_type=FileType.ENTITY),
            SourceFile(path="src/schema/user_schema.py", content="class UserSchema", file_type=FileType.ENTITY),
            SourceFile(path="src/models/product.py", content="class Product", file_type=FileType.ENTITY),
        ]
        
        result = router.route_to_erd(entity_files)
        
        assert len(result) >= 2
    
    def test_route_to_sequence(self) -> None:
        """Test routing files for Sequence diagram"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        # Files that should be routed to Sequence
        service_files = [
            SourceFile(path="src/services/user_service.py", content="class UserService", file_type=FileType.SERVICE),
            SourceFile(path="src/services/order_service.py", content="def create_order()", file_type=FileType.SERVICE),
            SourceFile(path="src/usecases/create_order.py", content="class CreateOrderUseCase", file_type=FileType.SERVICE),
        ]
        
        result = router.route_to_sequence(service_files)
        
        assert len(result) >= 2
    
    def test_route_to_architecture(self) -> None:
        """Test routing files for Architecture diagram"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        # Files that should be routed to Architecture
        arch_files = [
            SourceFile(path="src/main.py", content="app = FastAPI()", file_type=FileType.ENTRYPOINT),
            SourceFile(path="src/config/settings.py", content="class Settings", file_type=FileType.CONFIG),
            SourceFile(path="src/repository/user_repo.py", content="class UserRepository", file_type=FileType.REPOSITORY),
        ]
        
        result = router.route_to_architecture(arch_files)
        
        assert len(result) >= 2
    
    def test_route_to_dependencies(self) -> None:
        """Test routing files for Dependencies document"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        # Config files for dependencies
        config_files = [
            SourceFile(path="pom.xml", content="<dependencies>", file_type=FileType.CONFIG),
            SourceFile(path="build.gradle", content="dependencies {", file_type=FileType.CONFIG),
            SourceFile(path="requirements.txt", content="flask", file_type=FileType.CONFIG),
            SourceFile(path="package.json", content="dependencies", file_type=FileType.CONFIG),
            SourceFile(path="docker-compose.yml", content="services:", file_type=FileType.CONFIG),
        ]
        
        result = router.route_to_dependencies(config_files)
        
        assert len(result) >= 3
    
    def test_route_to_structure(self) -> None:
        """Test routing files for Structure document"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        # All files should be routed here
        all_files = [
            SourceFile(path="src/main.py", content="app", file_type=FileType.ENTRYPOINT),
            SourceFile(path="src/controllers/user.py", content="def", file_type=FileType.CONTROLLER),
            SourceFile(path="src/models/user.py", content="class", file_type=FileType.ENTITY),
            SourceFile(path="pom.xml", content="xml", file_type=FileType.CONFIG),
        ]
        
        result = router.route_to_structure(all_files)
        
        # Should return all files
        assert len(result) >= 4
    
    def test_route_to_state_machine(self) -> None:
        """Test routing files for State Machine document"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        # Files with state/enum patterns
        state_files = [
            SourceFile(path="src/enums/order_status.py", content="class OrderStatus(Enum)", file_type=FileType.ENTITY),
            SourceFile(path="src/models/order.py", content="class Order", file_type=FileType.ENTITY),
            SourceFile(path="src/services/order_service.py", content="def process_order()", file_type=FileType.SERVICE),
        ]
        
        result = router.route_to_state_machine(state_files)
        
        assert len(result) >= 1
    
    def test_route_all_documents(self) -> None:
        """Test routing to all 7 document types"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        # Mixed files
        all_files = [
            SourceFile(path="src/controllers/user.py", content="def create_user()", file_type=FileType.CONTROLLER),
            SourceFile(path="src/models/user.py", content="class User", file_type=FileType.ENTITY),
            SourceFile(path="src/services/user_service.py", content="class UserService", file_type=FileType.SERVICE),
            SourceFile(path="pom.xml", content="<dependencies>", file_type=FileType.CONTROLLER),
            SourceFile(path="src/main.py", content="app = FastAPI()", file_type=FileType.ENTRYPOINT),
            SourceFile(path="src/repository/user_repo.py", content="class UserRepository", file_type=FileType.REPOSITORY),
        ]
        
        # Route to all document types
        result = router.route_all(all_files)
        
        assert "api_spec" in result
        assert "erd" in result
        assert "sequence" in result
        assert "architecture" in result
        assert "dependencies" in result
        assert "structure" in result
        assert "state_machine" in result
    
    def test_empty_file_list(self) -> None:
        """Test routing with empty file list"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        result = router.route_to_api_spec([])
        
        assert result == []
    
    def test_filter_by_file_type(self) -> None:
        """Test file type filtering"""
        from src.infrastructure.services.artifact_router import ArtifactRouter
        
        router = ArtifactRouter()
        
        mixed_files = [
            SourceFile(path="src/controllers/user.py", content="def", file_type=FileType.CONTROLLER),
            SourceFile(path="src/models/user.py", content="class", file_type=FileType.ENTITY),
            SourceFile(path="README.md", content="readme", file_type=FileType.OTHER),
        ]
        
        # Filter only controller files
        result = router._filter_by_file_type(mixed_files, FileType.CONTROLLER)
        
        assert len(result) == 1
        assert result[0].file_type == FileType.CONTROLLER
