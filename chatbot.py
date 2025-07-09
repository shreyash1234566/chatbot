import os
import json
import re
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
import streamlit as st
from datetime import datetime

class Neo4jCypherChatbot:
    """
    A chatbot that converts natural language questions to Cypher queries
    using Neo4j's text2cypher API and returns human-readable answers.
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """Initialize the chatbot with Neo4j connection."""
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password)
        )
        
        # Initialize local LLM for answer generation
        self.llm = ChatOllama(model="llama3", temperature=0.3)
        
        # Neo4j Text2Cypher API endpoint
        self.text2cypher_url = "https://api.neo4j.com/v1/text2cypher"
        
        # Cache for schema information
        self.schema_cache = None
        self.schema_timestamp = None
        
        print("✅ Neo4j Cypher Chatbot initialized successfully!")
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j connection closed.")
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Get the current database schema for better query generation."""
        current_time = datetime.now()
        
        # Cache schema for 5 minutes to avoid repeated queries
        if (self.schema_cache is None or 
            self.schema_timestamp is None or 
            (current_time - self.schema_timestamp).seconds > 300):
            
            with self.driver.session() as session:
                # Get node labels and their counts
                node_query = """
                MATCH (n) 
                WHERE NOT n:Page 
                RETURN labels(n)[0] AS label, count(n) AS count 
                ORDER BY count DESC
                """
                
                # Get relationship types and their counts
                rel_query = """
                MATCH ()-[r]->() 
                WHERE NOT type(r) = 'MENTIONS' 
                RETURN type(r) AS type, count(r) AS count 
                ORDER BY count DESC
                """
                
                # Get sample nodes with properties
                sample_query = """
                MATCH (n) 
                WHERE NOT n:Page 
                RETURN labels(n)[0] AS label, keys(n) AS properties, n.id AS sample_id
                LIMIT 20
                """
                
                nodes = session.run(node_query).data()
                relationships = session.run(rel_query).data()
                samples = session.run(sample_query).data()
                
                self.schema_cache = {
                    "nodes": nodes,
                    "relationships": relationships,
                    "samples": samples
                }
                self.schema_timestamp = current_time
        
        return self.schema_cache
    
    def generate_cypher_with_text2cypher(self, question: str) -> str:
        """
        Generate Cypher query using Neo4j's text2cypher API.
        Note: This is a placeholder for the actual API call.
        You'll need to implement the actual API integration.
        """
        # For now, we'll use a local approach with LLM
        # In production, you would call the actual Neo4j text2cypher API
        return self.generate_cypher_with_local_llm(question)
    
    def generate_cypher_with_local_llm(self, question: str) -> str:
        """Generate Cypher query using local LLM with schema context."""
        schema = self.get_database_schema()
        
        # Create schema description
        schema_desc = self._format_schema_for_prompt(schema)
        
        prompt = ChatPromptTemplate.from_template(
            """
You are an expert Neo4j Cypher query generator for a scientific knowledge graph about satellites and remote sensing data.

**Database Schema:**
{schema}

**Instructions:**
1. Generate a Cypher query that answers the user's question
2. Use MATCH patterns to find relevant nodes and relationships
3. Return meaningful data that answers the question
4. Use LIMIT to avoid overwhelming results (max 20 results)
5. Handle case-insensitive searches using toLower() when needed
6. Focus on entities like Satellites, Sensors, DataProducts, Organizations

**User Question:** {question}

**Generate only the Cypher query without any explanation:**
            """
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            cypher_query = chain.invoke({
                "question": question,
                "schema": schema_desc
            })
            
            # Clean the query
            cypher_query = self._clean_cypher_query(cypher_query)
            return cypher_query
            
        except Exception as e:
            print(f"Error generating Cypher: {e}")
            return self._get_fallback_query(question)
    
    def _format_schema_for_prompt(self, schema: Dict[str, Any]) -> str:
        """Format schema information for the LLM prompt."""
        schema_parts = []
        
        # Node types
        if schema.get("nodes"):
            schema_parts.append("**Node Types:**")
            for node in schema["nodes"][:10]:  # Limit to top 10
                schema_parts.append(f"- {node['label']}: {node['count']} nodes")
        
        # Relationship types
        if schema.get("relationships"):
            schema_parts.append("\n**Relationship Types:**")
            for rel in schema["relationships"][:10]:  # Limit to top 10
                schema_parts.append(f"- {rel['type']}: {rel['count']} relationships")
        
        # Sample properties
        if schema.get("samples"):
            schema_parts.append("\n**Sample Node Properties:**")
            property_examples = {}
            for sample in schema["samples"][:5]:
                label = sample["label"]
                if label not in property_examples:
                    property_examples[label] = sample["properties"]
            
            for label, props in property_examples.items():
                schema_parts.append(f"- {label}: {', '.join(props)}")
        
        return "\n".join(schema_parts)
    
    def _clean_cypher_query(self, query: str) -> str:
        """Clean and validate the generated Cypher query."""
        # Remove markdown formatting
        query = re.sub(r'```cypher\n?', '', query)
        query = re.sub(r'```\n?', '', query)
        
        # Remove extra whitespace
        query = query.strip()
        
        # Ensure query ends with semicolon (optional but good practice)
        if not query.endswith(';'):
            query += ';'
        
        return query
    
    def _get_fallback_query(self, question: str) -> str:
        """Provide a fallback query when LLM fails."""
        # Simple keyword-based fallback
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['satellite', 'satellites']):
            return "MATCH (s:Satellite) RETURN s.id AS satellite, labels(s) AS type LIMIT 10;"
        
        elif any(word in question_lower for word in ['sensor', 'sensors']):
            return "MATCH (s:Sensor) RETURN s.id AS sensor, labels(s) AS type LIMIT 10;"
        
        elif any(word in question_lower for word in ['relationship', 'connection', 'related']):
            return "MATCH (n)-[r]->(m) WHERE NOT n:Page AND NOT m:Page RETURN n.id AS source, type(r) AS relationship, m.id AS target LIMIT 20;"
        
        else:
            return "MATCH (n) WHERE NOT n:Page RETURN labels(n)[0] AS type, n.id AS entity LIMIT 20;"
    
    def execute_cypher_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute the Cypher query and return results."""
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query)
                return [dict(record) for record in result]
        
        except Exception as e:
            print(f"Error executing Cypher query: {e}")
            print(f"Query: {cypher_query}")
            return []
    
    def generate_natural_language_answer(self, question: str, cypher_query: str, results: List[Dict[str, Any]]) -> str:
        """Convert query results to natural language answer."""
        if not results:
            return "I couldn't find any relevant information in the knowledge graph to answer your question."
        
        # Format results for the LLM
        results_text = self._format_results_for_llm(results)
        
        prompt = ChatPromptTemplate.from_template(
            """
You are a helpful assistant that explains scientific data from a satellite and remote sensing knowledge graph.

**User Question:** {question}

**Database Query Used:** {cypher_query}

**Query Results:** {results}

**Instructions:**
1. Provide a clear, natural language answer to the user's question
2. Use the query results to support your answer
3. Explain technical terms if needed
4. Be concise but informative
5. If the results are incomplete, mention it
6. Format the response in a user-friendly way

**Answer:**
            """
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            answer = chain.invoke({
                "question": question,
                "cypher_query": cypher_query,
                "results": results_text
            })
            return answer.strip()
            
        except Exception as e:
            print(f"Error generating natural language answer: {e}")
            return self._format_fallback_answer(results)
    
    def _format_results_for_llm(self, results: List[Dict[str, Any]]) -> str:
        """Format query results for the LLM prompt."""
        if not results:
            return "No results found."
        
        # Convert results to readable format
        formatted_results = []
        for i, result in enumerate(results[:15]):  # Limit to 15 results
            result_parts = []
            for key, value in result.items():
                if value is not None:
                    result_parts.append(f"{key}: {value}")
            
            if result_parts:
                formatted_results.append(f"Result {i+1}: {', '.join(result_parts)}")
        
        return "\n".join(formatted_results)
    
    def _format_fallback_answer(self, results: List[Dict[str, Any]]) -> str:
        """Provide a fallback answer when LLM fails."""
        if not results:
            return "I couldn't find any relevant information in the knowledge graph."
        
        answer_parts = ["Here's what I found:"]
        
        for i, result in enumerate(results[:10]):  # Limit to 10 results
            result_parts = []
            for key, value in result.items():
                if value is not None:
                    result_parts.append(f"{key}: {value}")
            
            if result_parts:
                answer_parts.append(f"• {', '.join(result_parts)}")
        
        if len(results) > 10:
            answer_parts.append(f"... and {len(results) - 10} more results.")
        
        return "\n".join(answer_parts)
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Main method to process a question and return a comprehensive answer.
        """
        print(f"\n🤖 Processing question: {question}")
        
        # Step 1: Generate Cypher query
        print("📝 Generating Cypher query...")
        cypher_query = self.generate_cypher_with_text2cypher(question)
        print(f"Generated query: {cypher_query}")
        
        # Step 2: Execute query
        print("🔍 Executing query...")
        results = self.execute_cypher_query(cypher_query)
        print(f"Found {len(results)} results")
        
        # Step 3: Generate natural language answer
        print("💬 Generating natural language answer...")
        answer = self.generate_natural_language_answer(question, cypher_query, results)
        
        return {
            "question": question,
            "cypher_query": cypher_query,
            "results": results,
            "answer": answer,
            "result_count": len(results)
        }

# Streamlit Web Interface
def create_streamlit_interface():
    """Create a Streamlit web interface for the chatbot."""
    st.set_page_config(
        page_title="Neo4j Knowledge Graph Chatbot",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Neo4j Knowledge Graph Chatbot")
    st.markdown("Ask questions about satellites, sensors, and remote sensing data!")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Neo4j connection settings
    neo4j_uri = st.sidebar.text_input("Neo4j URI", value="neo4j://localhost:7687")
    neo4j_user = st.sidebar.text_input("Neo4j Username", value="neo4j")
    neo4j_password = st.sidebar.text_input("Neo4j Password", type="password", value="test1234")
    
    # Initialize chatbot
    if st.sidebar.button("Connect to Database"):
        try:
            chatbot = Neo4jCypherChatbot(neo4j_uri, neo4j_user, neo4j_password)
            st.session_state.chatbot = chatbot
            st.sidebar.success("✅ Connected to Neo4j!")
        except Exception as e:
            st.sidebar.error(f"❌ Connection failed: {e}")
    
    # Main chat interface
    if 'chatbot' in st.session_state:
        chatbot = st.session_state.chatbot
        
        # Sample questions
        st.subheader("💡 Sample Questions")
        sample_questions = [
            "What satellites are in the knowledge graph?",
            "Which sensors are carried by INSAT-3DR?",
            "What data products are available?",
            "How are satellites and sensors related?",
            "What organizations are mentioned?"
        ]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(sample_questions[0]):
                st.session_state.current_question = sample_questions[0]
            if st.button(sample_questions[1]):
                st.session_state.current_question = sample_questions[1]
        
        with col2:
            if st.button(sample_questions[2]):
                st.session_state.current_question = sample_questions[2]
            if st.button(sample_questions[3]):
                st.session_state.current_question = sample_questions[3]
        
        with col3:
            if st.button(sample_questions[4]):
                st.session_state.current_question = sample_questions[4]
        
        # Question input
        question = st.text_input(
            "Ask your question:",
            value=st.session_state.get('current_question', ''),
            placeholder="e.g., What satellites carry ocean monitoring sensors?"
        )
        
        if st.button("🔍 Ask Question") and question:
            with st.spinner("Processing your question..."):
                try:
                    response = chatbot.ask_question(question)
                    
                    # Display answer
                    st.subheader("💬 Answer")
                    st.write(response["answer"])
                    
                    # Show details in expander
                    with st.expander("🔧 Technical Details"):
                        st.subheader("Generated Cypher Query")
                        st.code(response["cypher_query"], language="cypher")
                        
                        st.subheader(f"Query Results ({response['result_count']} found)")
                        if response["results"]:
                            st.json(response["results"])
                        else:
                            st.write("No results found.")
                
                except Exception as e:
                    st.error(f"❌ Error processing question: {e}")
        
        # Database schema viewer
        with st.expander("📊 Database Schema"):
            if st.button("Refresh Schema"):
                schema = chatbot.get_database_schema()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Node Types")
                    if schema.get("nodes"):
                        for node in schema["nodes"]:
                            st.write(f"• **{node['label']}**: {node['count']} nodes")
                
                with col2:
                    st.subheader("Relationship Types")
                    if schema.get("relationships"):
                        for rel in schema["relationships"]:
                            st.write(f"• **{rel['type']}**: {rel['count']} relationships")
    
    else:
        st.info("👈 Please connect to your Neo4j database using the sidebar.")

# Command Line Interface
def create_cli_interface():
    """Create a command-line interface for the chatbot."""
    print("\n🚀 Neo4j Knowledge Graph Chatbot")
    print("=" * 50)
    
    # Configuration
    neo4j_uri = input("Neo4j URI (default: neo4j://localhost:7687): ").strip() or "neo4j://localhost:7687"
    neo4j_user = input("Neo4j Username (default: neo4j): ").strip() or "neo4j"
    neo4j_password = input("Neo4j Password: ").strip() or "test1234"
    
    try:
        chatbot = Neo4jCypherChatbot(neo4j_uri, neo4j_user, neo4j_password)
        print("\n✅ Connected to Neo4j successfully!")
        
        print("\nYou can now ask questions about your knowledge graph.")
        print("Type 'quit' to exit, 'schema' to view database schema, or 'help' for sample questions.\n")
        
        while True:
            question = input("🤖 Ask a question: ").strip()
            
            if question.lower() == 'quit':
                break
            elif question.lower() == 'schema':
                schema = chatbot.get_database_schema()
                print("\n📊 Database Schema:")
                print("Node Types:")
                for node in schema.get("nodes", []):
                    print(f"  • {node['label']}: {node['count']} nodes")
                print("\nRelationship Types:")
                for rel in schema.get("relationships", []):
                    print(f"  • {rel['type']}: {rel['count']} relationships")
                print()
                continue
            elif question.lower() == 'help':
                print("\n💡 Sample Questions:")
                sample_questions = [
                    "What satellites are in the knowledge graph?",
                    "Which sensors are carried by INSAT-3DR?",
                    "What data products are available?",
                    "How are satellites and sensors related?",
                    "What organizations are mentioned?"
                ]
                for i, q in enumerate(sample_questions, 1):
                    print(f"  {i}. {q}")
                print()
                continue
            elif not question:
                continue
            
            try:
                response = chatbot.ask_question(question)
                print(f"\n💬 Answer: {response['answer']}")
                print(f"\n🔍 Found {response['result_count']} results")
                
                # Optionally show technical details
                show_details = input("\nShow technical details? (y/N): ").strip().lower()
                if show_details == 'y':
                    print(f"\n📝 Cypher Query:\n{response['cypher_query']}")
                    if response['results']:
                        print("\n📊 Raw Results:")
                        for i, result in enumerate(response['results'][:5], 1):
                            print(f"  {i}. {result}")
                        if len(response['results']) > 5:
                            print(f"  ... and {len(response['results']) - 5} more results")
                
                print("\n" + "="*50)
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
        
        chatbot.close()
        print("\nGoodbye! 👋")
        
    except Exception as e:
        print(f"\n❌ Failed to connect to Neo4j: {e}")

if __name__ == "__main__":
    import sys
    
    # Check if running in Streamlit
    if len(sys.argv) > 1 and sys.argv[1] == "streamlit":
        create_streamlit_interface()
    else:
        create_cli_interface()