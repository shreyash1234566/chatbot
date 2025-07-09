# app.py - Your new API server

from flask import Flask, request, jsonify
from flask_cors import CORS
# This line assumes your chatbot class is in the 'chatbot.py' file
from chatbot import Neo4jCypherChatbot

# --- SETUP ---
app = Flask(__name__)
# This is crucial to allow your webai.html to talk to this server
CORS(app)  

# --- CHATBOT INITIALIZATION ---
# Initialize the chatbot once when the server starts.
# This is much more efficient than creating it for every question.
try:
    # IMPORTANT: Update these credentials if they are different for you
    chatbot = Neo4jCypherChatbot(
        neo4j_uri="neo4j://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="test1234"
    )
    print("✅ Chatbot initialized and connected to Neo4j.")
except Exception as e:
    chatbot = None
    print(f"❌ CRITICAL: Failed to initialize chatbot on startup. Error: {e}")

# --- API ENDPOINTS (The URLs your website will call) ---

@app.route('/connect', methods=['POST'])
def connect():
    """
    Endpoint to check the connection status.
    This just confirms the chatbot was initialized correctly.
    """
    if chatbot:
        return jsonify({
            "status": "success", 
            "message": "Chatbot is connected and ready."
        })
    else:
        return jsonify({
            "status": "error", 
            "message": "Backend server couldn't connect to Neo4j. Check the server logs."
        }), 500

@app.route('/ask', methods=['POST'])
def ask_question_endpoint():
    """
    The main endpoint to process a user's question.
    It expects a JSON payload like: {"question": "your question here"}
    """
    if not chatbot:
        return jsonify({"answer": "Chatbot is not available. Please check the server."}), 503

    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"answer": "No question provided."}), 400

    try:
        # Use your chatbot's main method! This is where the magic happens.
        response = chatbot.ask_question(question)
        
        # The response from your chatbot is already a dictionary,
        # so we can return it directly as JSON.
        return jsonify(response)
        
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({"answer": f"An error occurred: {e}"}), 500

@app.route('/schema', methods=['GET'])
def get_schema_endpoint():
    """
    Endpoint to get the database schema.
    """
    if not chatbot:
        return jsonify({"error": "Chatbot is not available."}), 503
    
    try:
        schema_data = chatbot.get_database_schema()
        return jsonify(schema_data)
    except Exception as e:
        print(f"Error getting schema: {e}")
        return jsonify({"error": "Failed to retrieve schema."}), 500

# To run the server
if __name__ == '__main__':
    # We run on port 5001 to avoid conflicts with other services
    app.run(host='0.0.0.0', port=5001, debug=True)