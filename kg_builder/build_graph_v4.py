import os
import json
import re
from neo4j import GraphDatabase
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic.v1 import BaseModel, Field
from typing import List

# --- Configuration ---
URI = "neo4j://localhost:7687"
USER = "neo4j"
PASSWORD = "test1234" # Your Neo4j password
METADATA_FILE = os.path.join('..', 'mosdac_crawl_all', 'parsed_html_metadata.json')

# --- Pydantic Models for LLM Output ---
class Node(BaseModel):
    id: str = Field(description="A unique name for the entity (e.g., 'INSAT-3DR', 'Sea Surface Temperature'). This will be standardized to uppercase.")
    label: str = Field(description="The primary type of the entity (e.g., 'Satellite', 'DataProduct'). Should be in PascalCase.")

class Edge(BaseModel):
    source_node_id: str = Field(description="The unique name of the source entity.")
    target_node_id: str = Field(description="The unique name of the target entity.")
    type: str = Field(description="The type of relationship (e.g., 'CARRIES', 'MONITORS'). Should be in SCREAMING_SNAKE_CASE.")
    
class GraphDocument(BaseModel):
    nodes: List[Node] = Field(description="A list of all nodes in the graph.")
    edges: List[Edge] = Field(description="A list of all relationships between nodes.")

class AutomatedKnowledgeGraphBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.llm = ChatOllama(model="llama3", temperature=0, format="json")
        self.parser = JsonOutputParser(pydantic_object=GraphDocument)
        print("✅ Connection to Neo4j and local LLM established.")

    def close(self):
        self.driver.close()
        print("✅ Neo4j connection closed.")

    def run_cypher_query(self, query, parameters=None):
        with self.driver.session(database="neo4j") as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def clear_database(self):
        print("\n--- Clearing Database ---")
        self.run_cypher_query("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared.")

    def _standardize_id(self, text: str) -> str:
        return text.strip().upper()

    def seed_known_entities(self):
        print("\n--- Seeding Known Entities ---")
        known_entities = [
            {"id": "INSAT-3DR", "label": "Satellite"}, {"id": "INSAT-3D", "label": "Satellite"},
            {"id": "KALPANA-1", "label": "Satellite"}, {"id": "OCEANSAT-2", "label": "Satellite"},
            {"id": "SCATSAT-1", "label": "Satellite"}, {"id": "MEGHA-TROPIQUES", "label": "Satellite"},
            {"id": "IMAGER", "label": "Sensor"}, {"id": "SOUNDER", "label": "Sensor"},
            {"id": "OCM", "label": "Sensor"}, {"id": "SCATTEROMETER", "label": "Sensor"},
            {"id": "ISRO", "label": "Organization"}, {"id": "MOSDAC", "label": "Organization"},
        ]
        
        query = """
        UNWIND $entities AS entity_data
        MERGE (n {id: entity_data.id})
        ON CREATE SET n.created_at = timestamp()
        WITH n, entity_data
        CALL apoc.create.addLabels(n, [entity_data.label]) YIELD node
        RETURN count(node) AS created_nodes
        """
        self.run_cypher_query(query, parameters={'entities': known_entities})
        print(f"✅ Seeded {len(known_entities)} known entities.")
        
    def discover_graph_from_text(self, text_content: str, page_title: str) -> GraphDocument:
        prompt = ChatPromptTemplate.from_template(
            """
You are an expert knowledge graph engineer analyzing documents from MOSDAC.
From the text below, extract all relevant entities and the relationships between them.

**Instructions:**
1.  **Entities:** Identify key concepts like satellites, sensors, data products, organizations, etc.
    - `id`: Use the proper name of the entity (e.g., "INSAT-3DR").
    - `label`: Assign a general type in PascalCase (e.g., "Satellite").
2.  **Relationships:** Describe how entities connect.
    - Use the `id` of the source and target entities.
    - `type`: Use a verb phrase in SCREAMING_SNAKE_CASE (e.g., "CARRIES_SENSOR").

Return a single, valid JSON object.

**JSON Schema:** {json_schema}
**Context from Page Title:** "{page_title}"
**Text to Analyze:** "{text}"
            """
        )
        chain = prompt | self.llm | self.parser
        try:
            result = chain.invoke({
                "text": text_content[:4000], "page_title": page_title,
                "json_schema": self.parser.get_format_instructions()
            })
            return GraphDocument.parse_obj(result)
        except Exception as e:
            print(f"  > LLM or Parser Error: {e}")
            return GraphDocument(nodes=[], edges=[])

    def build_graph_from_document(self, doc):
        title = doc.get('title', '')
        text = doc.get('text_preview', '')
        filename = doc['file']
        print(f"\nProcessing: {title} ({filename})")
        if not text:
            print("  > Skipping: No text content.")
            return

        self.run_cypher_query("MERGE (p:Page {filename: $filename}) SET p.title = $title",
                              {"filename": filename, "title": title})
        graph_doc = self.discover_graph_from_text(text, title)
        if not graph_doc.nodes:
            print("  > Skipping: LLM did not extract any graph data.")
            return
        print(f"  > LLM Extracted: {len(graph_doc.nodes)} nodes and {len(graph_doc.edges)} edges.")

        for node in graph_doc.nodes:
            sanitized_id = self._standardize_id(node.id)
            sanitized_label = re.sub(r'[^a-zA-Z0-9]', '', node.label) # Sanitize label
            if not sanitized_label: continue
            
            query = f"""
            MERGE (n:{sanitized_label} {{id: $id}})
            WITH n
            MATCH (p:Page {{filename: $filename}})
            MERGE (p)-[:MENTIONS]->(n)
            """
            self.run_cypher_query(query, {"id": sanitized_id, "filename": filename})
            
        for edge in graph_doc.edges:
            source_id_std = self._standardize_id(edge.source_node_id)
            # --- THIS IS THE FIX ---
            target_id_std = self._standardize_id(edge.target_node_id) 
            
            sanitized_rel_type = re.sub(r'[^a-zA-Z0-9_]', '', edge.type.upper())
            if not sanitized_rel_type: continue
            
            query = f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            MERGE (source)-[r:{sanitized_rel_type}]->(target)
            """
            self.run_cypher_query(query, {"source_id": source_id_std, "target_id": target_id_std})

    def generate_summary(self):
        print("\n--- Knowledge Graph Summary ---")
        try:
            node_counts = self.run_cypher_query("MATCH (n) WHERE NOT n:Page RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC")
            print("Node Types:")
            for record in node_counts: print(f"  - {record['label']}: {record['count']}")
            rel_counts = self.run_cypher_query("MATCH ()-[r]->() WHERE NOT type(r) = 'MENTIONS' RETURN type(r) AS type, count(r) AS count ORDER BY count DESC")
            print("\nRelationship Types:")
            for record in rel_counts: print(f"  - {record['type']}: {record['count']}")
        except Exception as e:
            print(f"Could not generate summary: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    builder = AutomatedKnowledgeGraphBuilder(URI, USER, PASSWORD)
    builder.clear_database()
    try:
        builder.seed_known_entities()
    except Exception as e:
        print(f"⚠️ Could not seed entities. Ensure APOC plugin is installed. Error: {e}")
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            documents = json.load(f)
    except FileNotFoundError:
        print(f"Error: Metadata file not found at {METADATA_FILE}")
        documents = []
    for doc in documents[:5]:
        builder.build_graph_from_document(doc)
    builder.generate_summary()
    builder.close()