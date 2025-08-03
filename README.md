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

1. **Start Neo4j Database**  
   Ensure your Neo4j server is running locally (typically on `bolt://localhost:7687`) and credentials are set in `neo4j_schema.py`.

2. **Run the Knowledge Graph Builder**  
   This extracts triplets using an LLM and populates the Neo4j graph.

python kg_builder/build_graph_v4.py

3. **Start the Flask App**

python app.py


4. **Open the Web Interface**  
Visit `http://localhost:5000` in your browser to interact with the chatbot via the `webai.html` interface.

---

## Usage

- **Learning new content**:  
Input domain-specific text into the system via the frontend or directly modify scripts in `kg_builder/` to add large volumes of data.

- **Chatting with KG grounding**:  
Ask questions like:

- **Exploring the graph**:  
Use the Neo4j browser (`http://localhost:7474`) to visually inspect the knowledge graph and run custom Cypher queries.

---

## Technologies Used

- **Python 3.8+**
- **Flask** for backend server
- **HTML + JS** for frontend (in `webai.html`)
- **Ollama** with `sciphi/triplex` for triplet extraction
- **Neo4j** for knowledge graph persistence
- **Cypher** query language for graph queries

---

## Example Use Case: Satellite Weather Systems

This chatbot was tested with domain knowledge around Indian satellite missions and weather forecasting. Example flow:
- Scrape domain-relevant documents using `scrape_mosdac_crawl4ai_full.py`
- Chunk and embed data using `chunk_and_embed.py`
- Extract structured knowledge with `build_graph_v4.py`
- Ask grounded questions through the web UI

---

## Future Work

- Add graph visualizations to the UI
- Enable uploading PDFs or URLs for live KG updates
- Build a “supporting facts” display alongside responses
- Package for local deployment as a research assistant

---

## Contributing

Pull requests and issues are welcome. If you have ideas for improving the UI, integrating new domains, or enhancing LLM usage, feel free to open an issue or PR.

---

## License

This project is open-source and available under the [MIT License](LICENSE).


