# Chatbot

A Python-based chatbot project designed for easy customization, integration, and experimentation with conversational AI and knowledge graphs. This repository is ideal for developers, researchers, and enthusiasts interested in building, extending, or learning from chatbot architectures.

## Features

- **Conversational AI:** Implements a chatbot capable of interacting with users in natural language.
- **Knowledge Graph Integration:** Includes tools for building and querying knowledge graphs (`kg_builder`, `neo4j_schema.py`).
- **Web Scraping:** Scripts for scraping and embedding data (`scrape_mosdac_crawl4ai_full.py`, `chunk_and_embed.py`).
- **Web Interface:** Basic HTML interface (`webai.html`) for user interaction.
- **Modular Codebase:** Separated logic for chatbot, app server, and data processing.

## Project Structure

| File/Folder                        | Description                                        |
|-------------------------------------|----------------------------------------------------|
| `app.py`                           | Main application entry point (likely Flask/FastAPI)|
| `chatbot.py`                       | Core chatbot logic and conversation handling       |
| `kg_builder/`                      | Knowledge graph building utilities                 |
| `neo4j_schema.py`                  | Neo4j schema definition for graph database         |
| `chunk_and_embed.py`               | Text chunking and embedding for LLMs               |
| `scrape_mosdac_crawl4ai_full.py`   | Web scraping and data collection script            |
| `webai.html`                       | Simple web UI for interacting with the chatbot     |
| `requirements.txt`                 | Python dependencies                                |
| `.gitignore`                       | Files and folders to be ignored by git             |

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- (Optional) Neo4j for knowledge graph features

### Installation

1. **Clone the repository**
    ```
    git clone https://github.com/shreyash1234566/chatbot.git
    cd chatbot
    ```

2. **Install dependencies**
    ```
    pip install -r requirements.txt
    ```

3. **(Optional) Set up Neo4j**
    - Install Neo4j Community Edition or use a cloud instance.
    - Configure connection details in `neo4j_schema.py` if needed.

### Running the Application

