print("載入 kb_bp")

from qdrant_client import QdrantClient
from flask import Blueprint, jsonify
import os

kb_bp = Blueprint('knowledgeBases', __name__)

@kb_bp.route('/api/knowledgeBases/<collection_name>', methods=['GET'])
def get_kbs(collection_name):
    try:
        kb_name_list = {"knowledge_bases":[]}
        # 連接到Qdrant
        qdrant_host = os.getenv('QDRANT_HOST', 'qdrant')
        qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
        qdrant_client = QdrantClient(f"http://{qdrant_host}:{qdrant_port}") 
        #qdrant_client = QdrantClient("http://localhost:6333") 

        hit_result = qdrant_client.facet(
            collection_name = collection_name,
            key = "metadata.kb_name",
            limit = 1000
        )

        for hit in hit_result.hits:
            if hit.value not in kb_name_list['knowledge_bases']:
                kb_name_list['knowledge_bases'].append(hit.value)
        
        return jsonify(kb_name_list)
    except Exception as e:
        return jsonify({'error': f'獲取collection知識庫列表時出錯: {str(e)}'}), 500
