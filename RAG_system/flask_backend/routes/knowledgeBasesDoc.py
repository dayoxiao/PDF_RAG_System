print("載入 docKB_bp")

from qdrant_client import QdrantClient, models
from flask import Blueprint, jsonify, request
import os

docKB_bp = Blueprint('knowledgeBasesDoc', __name__)

@docKB_bp.route('/api/knowledgeBasesDoc', methods=['POST'])
def get_kbdocs():
    try:
        data = request.get_json()
        collection_name = data.get('collection')
        kb_name = data.get('kb_name')

        file_list = []
        file_id = []

        # 連接到Qdrant
        import socket
        try:
            socket.gethostbyname('qdrant')
            # 如果在 Docker 環境中，使用 qdrant 主機名
            qdrant_host = os.getenv('QDRANT_HOST', 'qdrant')
        except socket.gaierror:
            # 如果在本地開發環境中，使用 localhost
            qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        
        qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
        qdrant_client = QdrantClient(f"http://{qdrant_host}:{qdrant_port}") 
        #qdrant_client = QdrantClient("http://localhost:6333") 

        hit_result = qdrant_client.facet(
            collection_name = collection_name,
            key = "metadata.filename",
            facet_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.kb_name",
                        match=models.MatchValue(value=kb_name)
                    ),
                ]
            ),
            limit = 1000
        )

        for hit in hit_result.hits:
            if hit.value not in file_list:
                file_list.append(hit.value.rsplit('_', 1)[0])
                file_id.append(hit.value.rsplit('.', 1)[0].rsplit('_', 1)[-1])

        file_dict = [
            {
                'filename': fname,
                'file_id': fid,
                'kb_name': kb_name
            }
            for fname, fid in zip(file_list, file_id)
        ]
        
        return jsonify(file_dict)
    except Exception as e:
        return jsonify({'error': f'獲取知識庫檔案列表時出錯: {str(e)}'}), 500
