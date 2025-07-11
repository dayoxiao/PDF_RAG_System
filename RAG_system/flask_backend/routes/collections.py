print("載入 collections_bp")

from qdrant_client import QdrantClient
from flask import Blueprint, jsonify
import os

collections_bp = Blueprint('collections', __name__)

@collections_bp.route('/api/collections', methods=['GET'])
def get_collections():
    try:
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
        
        # 獲取集合列表
        collections_response = qdrant_client.get_collections()
        
        # 格式化響應
        formatted_collections = []
        for collection in collections_response.collections:
            collection_name = collection.name
            
            # 獲取集合信息
            collection_info = qdrant_client.get_collection(collection_name)
            
            # 獲取向量數量
            collection_count = qdrant_client.count(collection_name)
            
            formatted_collections.append({
                'name': collection_name,
                'description': f"{collection_name} 集合",
                'vectorCount': collection_count.count,
                'vectorDimension': collection_info.config.params.vectors.size,
                #'created': collection_info.config.created_at
            })
        
        return jsonify(formatted_collections)
    except Exception as e:
        return jsonify({'error': f'獲取集合列表時出錯: {str(e)}'}), 500
