"""
LLM Provider Client

Handles forwarding requests to OpenAI, Anthropic, and other LLM providers.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

from src.gateway.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for forwarding requests to LLM providers."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS)
    
    async def forward_to_openai(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
        tools: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Forward request to OpenAI API."""
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
        
        try:
            response = await self.client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Error forwarding to OpenAI: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with LLM provider: {str(e)}"
            )
    
    async def forward_to_anthropic(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
        tools: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Forward request to Anthropic API."""
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # Convert OpenAI format to Anthropic format
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": stream
        }
        
        if system_message:
            payload["system"] = system_message
        
        if tools:
            payload["tools"] = tools
        
        try:
            response = await self.client.post(
                f"{settings.ANTHROPIC_BASE_URL}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Error forwarding to Anthropic: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with LLM provider: {str(e)}"
            )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def forward_to_provider(
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float,
    max_tokens: Optional[int],
    stream: bool,
    tools: Optional[List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Route request to appropriate LLM provider based on model name.
    
    Args:
        model: Model identifier
        messages: Chat messages
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        stream: Whether to stream response
        tools: Available tools/functions
        
    Returns:
        LLM response in OpenAI format
    """
    client = LLMClient()
    
    try:
        # Route based on model prefix
        if model.startswith("gpt-") or model.startswith("o1-"):
            return await client.forward_to_openai(
                model, messages, temperature, max_tokens, stream, tools
            )
        elif model.startswith("claude-"):
            return await client.forward_to_anthropic(
                model, messages, temperature, max_tokens, stream, tools
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported model: {model}"
            )
    finally:
        await client.close()
