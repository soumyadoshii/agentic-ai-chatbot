from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from trainapp import user_input
from dotenv import load_dotenv

# Load environment variables explicitly
load_dotenv()

app = Flask(__name__)
CORS(app)  

@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        # 1. Strict Input Validation
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400
            
        user_question = data.get('question')
        if not user_question:
            return jsonify({'error': 'The "question" field is required'}), 400
            
        # Default to empty list if no history provided, ensure it's a list
        chat_history = data.get('chat_history', [])
        if not isinstance(chat_history, list):
            return jsonify({'error': '"chat_history" must be a list'}), 400
        
        # 2. Process Request through your AI Logic
        response = user_input(user_question, chat_history)  
        
        # 3. Return Successful Response
        return jsonify({'response': response}), 200
        
    except Exception as e:
        # Catch any unexpected RAG/LLM errors so the server doesn't crash
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500

if __name__ == '__main__':
    # 4. Safe fallbacks so the app boots even if .env is missing
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 17191))
    
    app.run(debug=True, host=host, port=port)