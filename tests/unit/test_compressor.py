"""
Unit tests for Headroom Compressor
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.headroom.compressor import HeadroomCompressor


@pytest.fixture
def redis_client():
    """Mock Redis client."""
    client = AsyncMock()
    client.set = AsyncMock(return_value=True)
    return client


@pytest.fixture
def compressor(redis_client):
    return HeadroomCompressor(redis_client)


@pytest.mark.asyncio
async def test_compress_code_python(compressor):
    """Test Python code compression."""
    code = """
def calculate_sum(a, b):
    \"\"\"Calculate the sum of two numbers.\"\"\"
    result = a + b
    return result

class Calculator:
    def add(self, x, y):
        return x + y
"""
    
    compressed = await compressor.compress_code(code)
    
    # Should be shorter than original
    assert len(compressed) < len(code)
    # Should contain cache reference
    assert "[CACHED:" in compressed
    # Metrics should be updated
    assert compressor.get_tokens_saved() > 0


@pytest.mark.asyncio
async def test_compress_json(compressor):
    """Test JSON compression."""
    json_content = '{"items": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "meta": {"count": 12}}'
    
    compressed = await compressor.compress_json(json_content)
    
    # Should be shorter
    assert len(compressed) < len(json_content)
    # Should contain cache reference
    assert "_cached_full" in compressed
    assert compressor.get_tokens_saved() > 0


@pytest.mark.asyncio
async def test_compress_prose(compressor):
    """Test prose compression."""
    prose = "This is a test message.    It has    extra    whitespace   and \n\n\n multiple newlines."
    
    compressed = await compressor.compress_prose(prose)
    
    # Should remove extra whitespace
    assert "    " not in compressed
    assert "\n\n\n" not in compressed


@pytest.mark.asyncio
async def test_compression_metrics(compressor):
    """Test compression metrics tracking."""
    code = "def test(): pass"
    
    await compressor.compress_code(code)
    
    assert compressor.get_tokens_saved() >= 0
    ratio = compressor.get_compression_ratio()
    assert 0 <= ratio <= 1.0
