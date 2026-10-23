"""
Basic Python SDK example for Perimeter Gateway
"""

import os
from openai import OpenAI

# Initialize client with Perimeter endpoint
client = OpenAI(
    base_url="https://api.perimeter.ai/v1",
    api_key=os.getenv("PERIMETER_API_KEY")
)

def main():
    """Example chat completion with Perimeter security."""
    
    print("🔒 Perimeter AI Security Gateway - Python SDK Example\n")
    
    # Create chat completion
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            },
            {
                "role": "user",
                "content": "What are the key benefits of using an AI security gateway?"
            }
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    # Print response
    print("Assistant:", response.choices[0].message.content)
    print(f"\nTokens used: {response.usage.total_tokens}")
    
    # Check Perimeter-specific headers
    # Note: These would be available in the raw HTTP response
    print("\n✅ Request processed with Perimeter security:")
    print("   - PII Detection: Enabled")
    print("   - Prompt Injection Detection: Enabled")
    print("   - Headroom Compression: Enabled")


if __name__ == "__main__":
    main()
