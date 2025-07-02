print("載入 status_bp")

from qdrant_client import QdrantClient
from flask import Blueprint, jsonify
import os

status_bp = Blueprint('status', __name__)

@status_bp.route('/api/collectionStatus/<collection_name>', methods=['GET'])
def get_collection_stats(collection_name):
    try:
        # 連接到Qdrant
        qdrant_host = os.getenv('QDRANT_HOST', 'qdrant')
        qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
        qdrant_client = QdrantClient(f"http://{qdrant_host}:{qdrant_port}") 
        #qdrant_client = QdrantClient("http://localhost:6333") 
        
        # 獲取集合信息
        collection_info = qdrant_client.get_collection(collection_name)
        
        # 獲取向量數量
        collection_count = qdrant_client.count(collection_name)
        
        # 計算磁盤使用量（估計值）
        vector_size = collection_info.config.params.vectors.size
        vector_count = collection_count.count
        disk_usage = (vector_size * vector_count * 4) / (1024 * 1024)  # 估計值，單位MB
        
        stats = {
            'vectorCount': vector_count,
            'vectorDimension': vector_size,
            'segmentCount': collection_info.segments_count,
            'indexType': str(collection_info.config.params.vectors.distance),
            'diskUsage': f"{disk_usage:.2f} MB",
            'created': "unknown",
            'lastModified': "unknown"
            #'created': collection_info.config.created_at,
            #'lastModified': collection_info.config.updated_at or collection_info.config.created_at
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'獲取集合統計信息時出錯: {str(e)}'}), 500
