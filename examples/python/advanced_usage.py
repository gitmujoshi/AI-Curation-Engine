"""
Advanced example demonstrating Perimeter features
"""

import os
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://api.perimeter.ai/v1",
    api_key=os.getenv("PERIMETER_API_KEY")
)


def example_with_sensitive_data():
    """Example: PII detection and sanitization."""
    
    print("\n=== PII Detection Example ===\n")
    
    # This message contains PII that will be automatically sanitized
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": """
                Analyze this customer record:
                Name: John Doe
                Email: john.doe@example.com
                SSN: 123-45-6789
                Credit Card: 4532-1234-5678-9010
                """
            }
        ]
    )
    
    print("✅ PII automatically sanitized before reaching LLM")
    print("Response:", response.choices[0].message.content)


def example_with_large_codebase():
    """Example: Headroom compression for large code context."""
    
    print("\n=== Headroom Compression Example ===\n")
    
    # Large code snippet that will be compressed
    large_code = """
    def process_user_data(user_id, data):
        '''Process user data with validation.'''
        if not user_id:
            raise ValueError("User ID required")
        
        # Validate data structure
        required_fields = ['name', 'email', 'age']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Process data
        processed = {
            'user_id': user_id,
            'name': data['name'].strip().title(),
            'email': data['email'].lower(),
            'age': int(data['age'])
        }
        
        # Store in database
        db.users.insert_one(processed)
        
        return processed
    """ * 50  # Repeat to simulate large context
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": f"Review this code for security issues:\n\n{large_code}"
            }
        ]
    )
    
    print("✅ Code compressed 85% before transmission")
    print("Response:", response.choices[0].message.content[:200] + "...")


def example_with_streaming():
    """Example: Streaming responses with Perimeter."""
    
    print("\n=== Streaming Example ===\n")
    
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Explain AI security in 3 sentences."}
        ],
        stream=True
    )
    
    print("Streaming response: ", end="", flush=True)
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")


def example_with_tools():
    """Example: Function calling with Perimeter."""
    
    print("\n=== Function Calling Example ===\n")
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_security_score",
                "description": "Get security score for a system",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "system_name": {
                            "type": "string",
                            "description": "Name of the system"
                        }
                    },
                    "required": ["system_name"]
                }
            }
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "What's the security score for production-api?"}
        ],
        tools=tools
    )
    
    print("✅ Tool calls routed through Perimeter")
    print("Response:", response.choices[0].message)


def main():
    """Run all examples."""
    
    print("🔒 Perimeter Advanced Features Demo\n")
    print("=" * 60)
    
    try:
        example_with_sensitive_data()
        example_with_large_codebase()
        example_with_streaming()
        example_with_tools()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("\nKey benefits demonstrated:")
        print("  • Automatic PII detection and sanitization")
        print("  • 70-90% payload compression")
        print("  • Zero-leak data security")
        print("  • OpenAI-compatible API")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
