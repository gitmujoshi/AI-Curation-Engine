import OpenAI from 'openai';

// Initialize Perimeter client
const client = new OpenAI({
  baseURL: 'https://api.perimeter.ai/v1',
  apiKey: process.env.PERIMETER_API_KEY,
});

async function main() {
  console.log('🔒 Perimeter AI Security Gateway - TypeScript SDK Example\n');

  try {
    // Create chat completion
    const response = await client.chat.completions.create({
      model: 'gpt-4',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful AI assistant.',
        },
        {
          role: 'user',
          content: 'What are the key benefits of using an AI security gateway?',
        },
      ],
      temperature: 0.7,
      max_tokens: 500,
    });

    // Print response
    console.log('Assistant:', response.choices[0].message.content);
    console.log(`\nTokens used: ${response.usage?.total_tokens}`);

    console.log('\n✅ Request processed with Perimeter security:');
    console.log('   - PII Detection: Enabled');
    console.log('   - Prompt Injection Detection: Enabled');
    console.log('   - Headroom Compression: Enabled');
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

main();
