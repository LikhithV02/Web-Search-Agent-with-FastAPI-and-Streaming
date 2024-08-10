import os
import asyncio
import aiohttp
import json
from trafilatura import extract
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import AsyncGroq
from typing import List, Optional

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize AsyncGroq client
client = AsyncGroq(api_key=os.getenv("api_key"))
MODEL = 'llama3-groq-70b-8192-tool-use-preview'

async def search_and_parse(query):
    """
    Perform a web search and parse the results.
    
    :param query: The search query string
    :return: A list of dictionaries containing url and parsed content or error messages
    """
    # Set up the search API request
    search_url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "gl": "in"
    }
    headers = {
        'X-API-KEY': os.getenv("serper_api_key"),
        'Content-Type': 'application/json'
    }
    
    # Perform the search API request
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(search_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    return [{"error": f"Serper API request failed with status code {response.status}"}]
                search_results = await response.json()
        except Exception as e:
            return [{"error": f"Error during search API request: {str(e)}"}]

    # Extract URLs from search results
    organic_results = search_results.get('organic', [])
    urls = [result['link'] for result in organic_results if 'link' in result]
    # Parse content from each URL
    results = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=10) as page_response:
                    if page_response.status == 200:
                        html_content = await page_response.text()
                        # Used trafilatura to extract main content
                        extracted_text = extract(html_content, include_links=False, include_images=False, include_tables=False)
                        if extracted_text:
                            results.append({'url': url, 'content': extracted_text[:1000]})  # Limit content to 1000 characters
                        else:
                            results.append({'url': url, 'error': "No main content extracted"})
                    else:
                        results.append({'url': url, 'error': f"Failed to retrieve content: HTTP {page_response.status}"})
            except asyncio.TimeoutError:
                results.append({'url': url, 'error': "Request timed out"})
            except aiohttp.ClientError as e:
                results.append({'url': url, 'error': f"Client error: {str(e)}"})
            except Exception as e:
                results.append({'url': url, 'error': f"Unexpected error: {str(e)}"})
    
    return results

async def run_conversation(user_prompt):
    """
    Run a conversation with the Groq model, including web search functionality.
    
    :param user_prompt: The user's input query
    :yield: Chunks of the conversation response
    """
    # Set up the conversation messages
    messages = [
        {
            "role": "system",
            "content": "You are an assistant that can search the web and provide information based on the search results. If there are errors in fetching or parsing web content, acknowledge them and try to provide the best response possible with the available information.ALways use the function if you do not know the answer. The function can be used multiple times until tou find the correct answer."
        },
        {
            "role": "user",
            "content": user_prompt,
        }
    ]
    # Define the search_and_parse tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_and_parse",
                "description": "Search the web and parse content from the results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to use",
                        }
                    },
                    "required": ["query"],
                },
            },
        }
    ]
    
    # Start the conversation stream
    stream = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=8192,
        temperature=0.5,
        top_p=1,
        stream=True
    )

    search_performed = False
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
        elif chunk.choices[0].delta.tool_calls is not None and not search_performed:
            tool_call = chunk.choices[0].delta.tool_calls[0]
            if tool_call.function.name == "search_and_parse":
                search_performed = True
                function_args = json.loads(tool_call.function.arguments)
                yield f"\nSearching the web for: {function_args.get('query')}\n"
                # Perform web search and parsing
                search_results = await search_and_parse(function_args.get("query"))
                for result in search_results:
                    if 'error' in result:
                        yield f"Error for {result.get('url', 'unknown URL')}: {result['error']}\n"
                    else:
                        yield f"Found relevant information from: {result['url']}\n"
                        yield f"Summary: {result['content'][:200]}...\n\n"
                
                # Add search results to messages and generate final response
                messages.append({
                    "role": "function",
                    "name": "search_and_parse",
                    "content": json.dumps(search_results)
                })
                final_stream = await client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=8192,
                    temperature=0.5,
                    top_p=1,
                    stream=True
                )
                yield "\nFinal response incorporating search results:\n"
                async for final_chunk in final_stream:
                    if final_chunk.choices[0].delta.content is not None:
                        yield final_chunk.choices[0].delta.content

async def generate_stream(query: str):
    """
    Generate a stream of responses for a given query.
    
    :param query: The user's input query
    :yield: Chunks of the response stream
    """
    try:
        async for response_chunk in run_conversation(query):
            yield response_chunk
    except Exception as e:
        yield f"An error occurred: {str(e)}"

@app.post("/chat-stream")
async def chat_stream(query: str):
    """
    FastAPI endpoint for streaming chat responses.
    
    :param query: The user's input query
    :return: A StreamingResponse object
    """
    return StreamingResponse(generate_stream(query), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)