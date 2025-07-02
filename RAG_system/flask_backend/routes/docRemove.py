print("載入 delete_bp")

import os
from flask import Blueprint, jsonify, request
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

delete_bp = Blueprint('delete', __name__)

@delete_bp.route('/api/delete', methods=['POST'])
def delete_document():
    """
    刪除文檔API - 同時從文件系統和Qdrant向量數據庫中刪除文檔

    請求JSON格式:
    {
        "document_id": "文檔ID",
        "filename": "原始檔名",
        "kb_name": "知識庫名"
        "collection": "Qdrant集合名稱 (預設為 None)"
    }
    """
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        file_name = data.get('filename')
        kb_name = data.get('kb_name')
        collection_name = data.get('collection', None)

        result = {
            "success": True,
            "message": "文檔已成功刪除",
            "details": {
                "file_deleted": False,
                "vectors_deleted": False,
                "vectors_count": 0
            }
        }

        try:
            qdrant_host = os.getenv('QDRANT_HOST', 'qdrant')
            qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
            qdrant_client = QdrantClient(f"http://{qdrant_host}:{qdrant_port}")
            #qdrant_client = QdrantClient(host="localhost", port=6333)
            collections = qdrant_client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections)

            if not collection_exists:
                return jsonify({
                    "success": False,
                    "error": f"集合 '{collection_name}' 不存在"
                }), 404
            
            vectors_count_before_delete = qdrant_client.count(collection_name).count

            delete_result = qdrant_client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.file_id",
                                match=models.MatchValue(value=document_id),
                            ),
                        ],
                    )
                ),
            )

            vectors_count_after_delete = qdrant_client.count(collection_name).count

            deleted_vectors_count = vectors_count_before_delete - vectors_count_after_delete
            result["details"]["vectors_count"] = deleted_vectors_count
            result["details"]["vectors_deleted"] = deleted_vectors_count > 0

        except UnexpectedResponse as e:
            result["success"] = False
            result["error"] = f"Qdrant API錯誤: {str(e)}"
            result["details"]["vectors_error"] = str(e)
        except Exception as e:
            result["success"] = False
            result["error"] = f"刪除向量時出錯: {str(e)}"
            result["details"]["vectors_error"] = str(e)

        # 如果沒有成功刪除向量
        if not result["details"]["vectors_deleted"]:
            result["success"] = False
            result["message"] = "未刪除任何向量"
            result["error"] = "找不到文檔id指定的向量"
            return jsonify(result), 404
        
        # 刪除檔案
        if file_name:
            base_name = os.path.splitext(file_name)[0]
            actual_filename = f"{base_name}_{document_id}.pdf"
            file_path = os.path.join('uploads', kb_name, actual_filename)

            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    result["details"]["file_deleted"] = True
                    print(f"成功刪除文件：{file_path}")
                    
                    # 檢查知識庫資料夾是否為空，如果是則刪除
                    kb_folder = os.path.join('uploads', kb_name)
                    if os.path.exists(kb_folder) and not os.listdir(kb_folder):
                        try:
                            os.rmdir(kb_folder)
                            print(f"成功刪除空的知識庫資料夾：{kb_folder}")
                        except Exception as e:
                            print(f"刪除知識庫資料夾失敗：{str(e)}")
                except Exception as e:
                    result["details"]["file_error"] = str(e)
                    print(f"刪除文件失敗：{str(e)}")
            else:
                print(f"文件不存在所指定位置：{file_path}")

            # 刪除圖片
            UPLOAD_FOLDER_IMAGE = 'figure_storage'
            for filename in os.listdir(UPLOAD_FOLDER_IMAGE):
                if filename.startswith(f"{base_name}_{document_id}"):
                    file_path = os.path.join(UPLOAD_FOLDER_IMAGE, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"已刪除圖片資料：{file_path}")

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"刪除資料時出錯: {str(e)}"
        }), 500