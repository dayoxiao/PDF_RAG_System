print("載入 models_bp")

from flask import Blueprint, jsonify
import ollama
import os

models_bp = Blueprint('models', __name__)

@models_bp.route('/api/models', methods=['GET'])
def get_models():
    try:
        ollama_host = os.getenv('OLLAMA_HOST', 'ollama')
        ollama_port = int(os.getenv('OLLAMA_PORT', 11434))
        base_url = f"http://{ollama_host}:{ollama_port}"
        client = ollama.Client(host=base_url)
        models_response = client.list()
        
        formatted_models = [{
            'id': m.get('model'),
            'name': m.get('model').split(':')[0].capitalize(),
            #'size': m.get('size', 'Unknown'),
            'size': m.get('model').split(':')[1],
            'description': f"{m.get('model')} 模型",
            'tags': ['general'],
            'loaded': True
        } for m in models_response.get('models', [])]

        return jsonify(formatted_models)
    except Exception as e:
        return jsonify({'error': f'獲取模型列表時出錯: {str(e)}'}), 500