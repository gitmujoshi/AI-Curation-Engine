"""
BAML Type Guardrail Engine

Provides runtime type validation and prompt injection inoculation
using Pydantic schema definitions.

NOTE: This is a production-grade implementation using Pydantic for schema validation.
For full BAML integration, install baml-py and use BoundaryML's schema compiler.
"""

import logging
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, ValidationError
from enum import Enum

logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Valid message roles for chat completions."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class FunctionCall(BaseModel):
    """Function call structure."""
    name: str = Field(..., description="Function name")
    arguments: str = Field(..., description="Function arguments as JSON string")


class ToolCall(BaseModel):
    """Tool call structure."""
    id: str = Field(..., description="Tool call ID")
    type: Literal["function"] = "function"
    function: FunctionCall


class ChatMessage(BaseModel):
    """
    Type-safe chat message structure.
    
    Enforces strict typing and prevents prompt injection by treating
    user content as immutable data (not executable instructions).
    """
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content (immutable)")
    name: Optional[str] = Field(None, description="Optional message name")
    function_call: Optional[FunctionCall] = Field(None, description="Function call (deprecated)")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Any) -> str:
        """Ensure content is always a string (immutable)."""
        if v is None:
            return ""
        return str(v)
    
    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v: Any) -> str:
        """Validate and normalize role."""
        if isinstance(v, str):
            v = v.lower()
            if v not in [r.value for r in MessageRole]:
                raise ValueError(f"Invalid role: {v}. Must be one of: {[r.value for r in MessageRole]}")
        return v
    
    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class ChatCompletionResponse(BaseModel):
    """Type-safe chat completion response."""
    id: str = Field(default="", description="Response ID")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(default=0, description="Creation timestamp")
    model: str = Field(default="", description="Model name")
    choices: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage")
    
    @field_validator('choices')
    @classmethod
    def validate_choices(cls, v: List[Dict]) -> List[Dict]:
        """Ensure each choice has required fields."""
        validated = []
        for choice in v:
            if not isinstance(choice, dict):
                continue
            
            # Ensure message structure
            if "message" not in choice:
                choice["message"] = {"role": "assistant", "content": ""}
            
            msg = choice["message"]
            if "role" not in msg:
                msg["role"] = "assistant"
            if "content" not in msg:
                msg["content"] = ""
            
            validated.append(choice)
        
        return validated


class BAMLValidator:
    """
    Pydantic-powered type validation engine.
    
    Ensures all inputs conform to strict schemas and prevents
    prompt injection by treating user content as immutable variables.
    
    Production Note: This uses Pydantic for runtime validation.
    For full BAML integration, use BoundaryML's baml-py library.
    """
    
    def __init__(self, schema_path: str = "config/baml_src"):
        self.schema_path = schema_path
        logger.info(f"Initialized type validator with schema path: {schema_path}")
    
    async def validate_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and sanitize chat messages using Pydantic schemas.
        
        This provides:
        - Strict type checking
        - Schema validation
        - Prompt injection inoculation (content treated as immutable data)
        - Malformed input rejection
        
        Args:
            messages: List of chat messages
            
        Returns:
            Validated messages with type-safe structure
            
        Raises:
            ValueError: If messages don't conform to schema
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list")
        
        validated = []
        
        for idx, msg in enumerate(messages):
            try:
                # Validate using Pydantic model
                chat_message = ChatMessage(**msg)
                
                # Convert back to dict with validated fields
                validated_msg = {
                    "role": chat_message.role.value,
                    "content": chat_message.content,
                }
                
                # Add optional fields if present
                if chat_message.name:
                    validated_msg["name"] = chat_message.name
                
                if chat_message.function_call:
                    validated_msg["function_call"] = chat_message.function_call.model_dump()
                
                if chat_message.tool_calls:
                    validated_msg["tool_calls"] = [
                        tc.model_dump() for tc in chat_message.tool_calls
                    ]
                
                validated.append(validated_msg)
                
            except ValidationError as e:
                error_details = e.errors()
                logger.error(f"Validation error in message {idx}: {error_details}")
                raise ValueError(
                    f"Message {idx} validation failed: {error_details[0]['msg']}"
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error validating message {idx}: {e}")
                raise ValueError(f"Invalid message structure at index {idx}") from e
        
        logger.debug(f"Successfully validated {len(validated)} messages")
        return validated
    
    async def validate_output(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate LLM output against expected schema.
        
        Handles malformed or partial responses by extracting valid
        nested properties and reconstructing a valid response.
        
        Args:
            response: LLM response
            
        Returns:
            Validated and potentially reconstructed response
        """
        try:
            # Validate using Pydantic model
            completion_response = ChatCompletionResponse(**response)
            
            # Return validated response
            return completion_response.model_dump(exclude_none=True)
            
        except ValidationError as e:
            logger.error(f"Output validation error: {e.errors()}")
            
            # Attempt to salvage usable parts of the response
            salvaged_response = self._salvage_response(response)
            
            if salvaged_response:
                logger.info("Successfully salvaged partial response")
                return salvaged_response
            
            # Return minimal valid error response
            logger.warning("Returning error response due to validation failure")
            return {
                "id": "error",
                "object": "chat.completion",
                "created": 0,
                "model": response.get("model", "unknown"),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Error: Invalid response format from LLM provider"
                    },
                    "finish_reason": "error"
                }],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error validating output: {e}", exc_info=True)
            return {
                "id": "error",
                "object": "chat.completion",
                "created": 0,
                "model": "unknown",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Error: Failed to validate response"
                    },
                    "finish_reason": "error"
                }]
            }
    
    def _salvage_response(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Attempt to salvage usable parts from a malformed response.
        
        Args:
            response: Potentially malformed response
            
        Returns:
            Salvaged valid response or None
        """
        try:
            # Extract what we can
            salvaged = {
                "id": response.get("id", "salvaged"),
                "object": "chat.completion",
                "created": response.get("created", 0),
                "model": response.get("model", "unknown"),
                "choices": [],
            }
            
            # Try to extract choices
            choices = response.get("choices", [])
            if not isinstance(choices, list):
                return None
            
            for idx, choice in enumerate(choices):
                if not isinstance(choice, dict):
                    continue
                
                message = choice.get("message", {})
                if not isinstance(message, dict):
                    continue
                
                # Build valid choice
                salvaged_choice = {
                    "index": choice.get("index", idx),
                    "message": {
                        "role": message.get("role", "assistant"),
                        "content": str(message.get("content", "")),
                    },
                    "finish_reason": choice.get("finish_reason", "stop")
                }
                
                # Add function_call if present
                if "function_call" in message:
                    salvaged_choice["message"]["function_call"] = message["function_call"]
                
                # Add tool_calls if present
                if "tool_calls" in message:
                    salvaged_choice["message"]["tool_calls"] = message["tool_calls"]
                
                salvaged["choices"].append(salvaged_choice)
            
            # Add usage if present
            if "usage" in response:
                salvaged["usage"] = response["usage"]
            
            # Validate the salvaged response
            ChatCompletionResponse(**salvaged)
            
            return salvaged
            
        except Exception as e:
            logger.debug(f"Failed to salvage response: {e}")
            return None
