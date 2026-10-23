"""
Proxy Routes

Main LLM proxy endpoint that handles:
1. Authentication & Authorization
2. BAML Type Validation
3. Headroom Compression
4. PII Detection
5. Payload Routing to LLM Providers
"""

import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from src.gateway.config import settings
from src.gateway.auth import verify_api_key
from src.baml_engine.validator import BAMLValidator
from src.headroom.content_router import ContentRouter
from src.headroom.compressor import HeadroomCompressor
from src.guardrails.pii_detector import PIIDetector
from src.guardrails.prompt_injection import PromptInjectionDetector
from src.cache.cache_aligner import CacheAligner

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str
    messages: list
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    tools: Optional[list] = None


class CompletionResponse(BaseModel):
    """OpenAI-compatible completion response."""
    id: str
    object: str
    created: int
    model: str
    choices: list
    usage: Optional[Dict[str, int]] = None


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    tenant_id: str = Depends(verify_api_key)
):
    """
    OpenAI-compatible chat completions endpoint with Perimeter security.
    
    Processing Pipeline:
    1. Authentication & Rate Limiting
    2. BAML Type Validation
    3. Prompt Injection Detection
    4. PII Sanitization
    5. Headroom Compression & Caching
    6. Cache Alignment Optimization
    7. Forward to LLM Provider
    8. Response Validation & Reconstruction
    """
    start_time = time.time()
    
    try:
        # Step 1: BAML Type Validation
        validator = BAMLValidator()
        validated_messages = await validator.validate_messages(body.messages)
        
        # Step 2: Prompt Injection Detection
        if settings.PROMPT_INJECTION_DETECTION:
            injection_detector = PromptInjectionDetector()
            for msg in validated_messages:
                if msg.get("role") == "user":
                    is_malicious = await injection_detector.detect(msg["content"])
                    if is_malicious:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Potential prompt injection detected"
                        )
        
        # Step 3: PII Detection & Sanitization
        if settings.PII_DETECTION_ENABLED:
            pii_detector = PIIDetector()
            sanitized_messages = []
            for msg in validated_messages:
                sanitized_content = await pii_detector.sanitize(msg["content"])
                sanitized_messages.append({
                    **msg,
                    "content": sanitized_content
                })
            validated_messages = sanitized_messages
        
        # Step 4: Headroom Compression & Caching
        redis_client = request.app.state.redis
        compressor = HeadroomCompressor(redis_client)
        
        content_router = ContentRouter()
        compressed_payload = await content_router.route_and_compress(
            validated_messages,
            compressor
        )
        
        # Step 5: Cache Alignment Optimization
        aligner = CacheAligner()
        optimized_payload = await aligner.optimize_for_kv_cache(compressed_payload)
        
        # Step 6: Add sovereign tool for cache retrieval
        tools = body.tools or []
        tools.append({
            "type": "function",
            "function": {
                "name": "headroom_retrieve",
                "description": "Retrieve compressed context from local cache",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hash": {
                            "type": "string",
                            "description": "64-bit hash of cached content"
                        }
                    },
                    "required": ["hash"]
                }
            }
        })
        
        # Step 7: Forward to LLM Provider
        from src.gateway.llm_client import forward_to_provider
        
        response = await forward_to_provider(
            model=body.model,
            messages=optimized_payload,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            stream=body.stream,
            tools=tools
        )
        
        # Step 8: Track Usage
        usage_tracker = request.app.state.usage_tracker
        await usage_tracker.track_request(
            tenant_id=tenant_id,
            tokens_saved=compressor.get_tokens_saved(),
            compression_ratio=compressor.get_compression_ratio()
        )
        
        # Log metrics
        processing_time = (time.time() - start_time) * 1000
        logger.info(
            f"Request processed in {processing_time:.2f}ms | "
            f"Compression: {compressor.get_compression_ratio():.2%} | "
            f"Tokens saved: {compressor.get_tokens_saved()}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/tool/headroom_retrieve")
async def headroom_retrieve(
    request: Request,
    body: Dict[str, Any],
    tenant_id: str = Depends(verify_api_key)
):
    """
    Sovereign tool for retrieving compressed context from local cache.
    
    Called by LLM when it needs access to cached content.
    """
    try:
        hash_key = body.get("hash")
        if not hash_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing hash parameter"
            )
        
        redis_client = request.app.state.redis
        cached_content = await redis_client.get(f"cache:{tenant_id}:{hash_key}")
        
        if not cached_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cached content not found"
            )
        
        return {
            "hash": hash_key,
            "content": cached_content,
            "retrieved_at": int(time.time())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cached content"
        )
