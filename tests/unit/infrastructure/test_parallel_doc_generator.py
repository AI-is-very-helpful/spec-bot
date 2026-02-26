"""Unit tests for ParallelDocumentGenerator (asyncio-based parallel document generation)"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


class TestParallelDocumentGenerator:
    """Test cases for ParallelDocumentGenerator with asyncio.gather"""
    
    def test_initialization(self) -> None:
        """Test generator initialization"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        generator = ParallelDocumentGenerator(
            api_key="test_key",
            api_endpoint="https://test.openai.azure.com/",
            api_version="2024-02-15-preview",
            deployment_name="test-model"
        )
        
        assert generator is not None
    
    @pytest.mark.asyncio
    async def test_generate_api_spec_parallel(self) -> None:
        """Test parallel generation of all 7 documents"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        # Mock OpenAI client
        with patch("src.infrastructure.services.parallel_doc_generator.AzureOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            
            # Return valid JSON for each document
            mock_message.content = json.dumps({
                "content": "# API Specification\n\n## Endpoints\n- GET /users"
            })
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            generator = ParallelDocumentGenerator(
                api_key="test_key",
                api_endpoint="https://test.openai.azure.com/",
                api_version="2024-02-15-preview",
                deployment_name="test-model"
            )
            
            # Should generate all 7 documents in parallel
            result = await generator.generate_all({
                "api_spec": "controller code...",
                "erd": "entity code...",
                "sequence": "service code...",
                "architecture": "config code...",
                "dependencies": "pom.xml...",
                "structure": "all files...",
                "state_machine": "enum code...",
            })
            
            assert "api_spec" in result
            assert "erd" in result
            assert "sequence" in result
            assert "architecture" in result
            assert "dependencies" in result
            assert "structure" in result
            assert "state_machine" in result
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self) -> None:
        """Test that documents are generated in parallel (not sequentially)"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        call_times: list[float] = []
        
        async def mock_create(*args, **kwargs):
            import time
            call_times.append(time.time())
            await asyncio.sleep(0.1)  # Simulate API call
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = json.dumps({"content": "test"})
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response
        
        import asyncio
        
        with patch("src.infrastructure.services.parallel_doc_generator.AzureOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client
            
            generator = ParallelDocumentGenerator(
                api_key="test_key",
                api_endpoint="https://test.openai.azure.com/",
                api_version="2024-02-15-preview",
                deployment_name="test-model"
            )
            
            contexts = {
                "api_spec": "test",
                "erd": "test",
                "sequence": "test",
                "architecture": "test",
                "dependencies": "test",
                "structure": "test",
                "state_machine": "test",
            }
            
            import time
            start = time.time()
            result = await generator.generate_all(contexts)
            total_time = time.time() - start
            
            # If sequential, would take 7 * 0.1 = 0.7 seconds
            # If parallel, should take ~0.1 seconds
            assert total_time < 0.5, f"Execution took {total_time}s - not parallel!"
    
    @pytest.mark.asyncio
    async def test_error_handling(self) -> None:
        """Test error handling in parallel generation"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        call_count = 0
        
        async def mock_create_error(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception("API Error")
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = json.dumps({"content": "fallback"})
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response
        
        with patch("src.infrastructure.services.parallel_doc_generator.AzureOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_create_error
            mock_client_class.return_value = mock_client
            
            generator = ParallelDocumentGenerator(
                api_key="test_key",
                api_endpoint="https://test.openai.azure.com/",
                api_version="2024-02-15-preview",
                deployment_name="test-model"
            )
            
            # Should handle errors gracefully
            result = await generator.generate_all({
                "api_spec": "test",
                "erd": "test",
                "sequence": "test",
                "architecture": "test",
                "dependencies": "test",
                "structure": "test",
                "state_machine": "test",
            })
            
            # Should still return results for all documents
            assert len(result) == 7
    
    def test_system_prompt_for_api_spec(self) -> None:
        """Test API spec system prompt includes detailed requirements"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        generator = ParallelDocumentGenerator(
            api_key="test_key",
            api_endpoint="https://test.openai.azure.com/",
            api_version="2024-02-15-preview",
            deployment_name="test-model"
        )
        
        prompt = generator._get_system_prompt("api_spec")
        
        # Should include detailed requirements for API spec
        assert "Request Body" in prompt
        assert "Response Body" in prompt
        assert "Header" in prompt
        assert "Parameters" in prompt
    
    def test_system_prompt_for_erd(self) -> None:
        """Test ERD system prompt includes Mermaid syntax"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        generator = ParallelDocumentGenerator(
            api_key="test_key",
            api_endpoint="https://test.openai.azure.com/",
            api_version="2024-02-15-preview",
            deployment_name="test-model"
        )
        
        prompt = generator._get_system_prompt("erd")
        
        assert "erDiagram" in prompt
        assert "Mermaid" in prompt
    
    def test_system_prompt_for_sequence(self) -> None:
        """Test Sequence system prompt"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        generator = ParallelDocumentGenerator(
            api_key="test_key",
            api_endpoint="https://test.openai.azure.com/",
            api_version="2024-02-15-preview",
            deployment_name="test-model"
        )
        
        prompt = generator._get_system_prompt("sequence")
        
        assert "sequenceDiagram" in prompt
    
    def test_system_prompt_for_architecture(self) -> None:
        """Test Architecture system prompt"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        generator = ParallelDocumentGenerator(
            api_key="test_key",
            api_endpoint="https://test.openai.azure.com/",
            api_version="2024-02-15-preview",
            deployment_name="test-model"
        )
        
        prompt = generator._get_system_prompt("architecture")
        
        assert "flowchart" in prompt
    
    def test_system_prompt_for_state_machine(self) -> None:
        """Test State Machine system prompt"""
        from src.infrastructure.services.parallel_doc_generator import ParallelDocumentGenerator
        
        generator = ParallelDocumentGenerator(
            api_key="test_key",
            api_endpoint="https://test.openai.azure.com/",
            api_version="2024-02-15-preview",
            deployment_name="test-model"
        )
        
        prompt = generator._get_system_prompt("state_machine")
        
        assert "stateDiagram-v2" in prompt
