# Perimeter API Reference

## Base URL

**SaaS**: `https://api.perimeter.ai/v1`  
**Enterprise**: `https://your-domain.com/v1`

## Authentication

All requests require an API key passed in the header:

```
X-Perimeter-API-Key: pmtr_live_your_api_key
```

## OpenAI-Compatible Endpoints

### Chat Completions

**POST** `/v1/chat/completions`

Create a chat completion with Perimeter security.

#### Request Body

```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

#### Response

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

#### Additional Response Headers

- `X-Perimeter-Tokens-Saved`: Number of tokens saved by compression
- `X-Perimeter-Compression-Ratio`: Compression ratio (0-1)
- `X-Process-Time`: Total processing time in seconds

## Perimeter-Specific Endpoints

### Retrieve Cached Context

**POST** `/v1/tool/headroom_retrieve`

Retrieve cached content by hash (called by LLM via tool).

#### Request Body

```json
{
  "hash": "a1b2c3d4e5f67890"
}
```

#### Response

```json
{
  "hash": "a1b2c3d4e5f67890",
  "content": "Original cached content...",
  "retrieved_at": 1677652288
}
```

## Health & Monitoring

### Health Check

**GET** `/health`

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "gateway": "operational",
    "redis": "operational",
    "baml_engine": "operational",
    "headroom": "operational"
  }
}
```

### Readiness Check

**GET** `/health/ready`

Kubernetes/Cloud Run readiness probe.

#### Response

```json
{
  "status": "ready",
  "checks": {
    "redis": "connected",
    "database": "connected"
  }
}
```

### Liveness Check

**GET** `/health/live`

Kubernetes/Cloud Run liveness probe.

#### Response

```json
{
  "status": "alive"
}
```

### Metrics

**GET** `/metrics`

Prometheus metrics endpoint.

#### Response

```
# HELP perimeter_requests_total Total number of requests
# TYPE perimeter_requests_total counter
perimeter_requests_total{method="POST",endpoint="/v1/chat/completions",status="200"} 1234

# HELP perimeter_request_duration_seconds Request duration in seconds
# TYPE perimeter_request_duration_seconds histogram
perimeter_request_duration_seconds_bucket{method="POST",endpoint="/v1/chat/completions",le="0.005"} 1000
...
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input or prompt injection detected |
| 401 | Unauthorized - Missing or invalid API key |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Processing error |
| 502 | Bad Gateway - LLM provider error |
| 503 | Service Unavailable - System overloaded |

### Error Response Format

```json
{
  "error": "Invalid API key",
  "detail": "The provided API key is not valid",
  "code": "INVALID_API_KEY"
}
```

## Rate Limits

- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1,000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers included in all responses:
- `X-RateLimit-Limit`: Total allowed requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Timestamp when limit resets

## Supported Models

### OpenAI Models
- `gpt-4`
- `gpt-4-turbo`
- `gpt-3.5-turbo`
- `o1-preview`
- `o1-mini`

### Anthropic Models
- `claude-3-5-sonnet-20241022`
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`

## SDK Examples

### Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.perimeter.ai/v1",
    api_key="pmtr_live_your_api_key"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### TypeScript

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://api.perimeter.ai/v1',
  apiKey: 'pmtr_live_your_api_key',
});

const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'user', content: 'Hello!' }
  ],
});

console.log(response.choices[0].message.content);
```

### cURL

```bash
curl https://api.perimeter.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Perimeter-API-Key: pmtr_live_your_api_key" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```
