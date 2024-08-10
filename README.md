# Web Search Agent with FastAPI and Streaming

This project implements a web search agent using FastAPI, featuring real-time streaming of responses. It combines the power of the Groq language model with web search capabilities to provide informative and up-to-date responses to user queries.

## Features

- **Web Search Integration**: Utilizes the Serper API to perform web searches based on user queries.
- **Advanced Content Extraction**: Uses Trafilatura for efficient and accurate extraction of main content from web pages.
- **Real-time Streaming**: Implements FastAPI's streaming response to provide real-time updates as the agent processes the query and searches the web.
- **Groq Language Model**: Leverages the Groq API for natural language understanding and generation.
- **Error Handling**: Robust error handling for search and parsing operations, ensuring graceful degradation in case of issues.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Python 3.7+
- FastAPI
- Uvicorn
- aiohttp
- Groq Python client
- Trafilatura
- python-dotenv

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/LikhithV02/Web-Search-Agent-with-FastAPI-and-Streaming.git
   cd web-search-agent
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the FastAPI server:
   ```
   uvicorn app:app
   ```

2. The server will start on `http://localhost:8000`. You can now send POST requests to the `/chat-stream` endpoint.

3. To use the web search agent, send a POST request to `http://localhost:8000/chat-stream` with a JSON body containing the query:
   ```json
   {
     "query": "What are the latest developments in AI?"
   }
   ```

4. The response will be streamed in real-time, providing updates as the agent searches the web and processes the information.

## API Endpoints

- `POST /chat-stream`: Accepts a query and returns a streamed response containing web search results and AI-generated content.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Groq](https://groq.com/)
- [Trafilatura](https://github.com/adbar/trafilatura)
- [Serper API](https://serper.dev/)