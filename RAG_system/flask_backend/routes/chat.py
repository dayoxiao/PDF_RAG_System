print("載入 chat_bp")

from flask import Blueprint, jsonify, request

import ollama

from .util.qdrant_util import qdrant_DBConnector
from .util.ollama_util import *

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        query = data.get('query')
        model_id = data.get('model')
        collection_name = data.get('collection')
        kb_name = data.get('kbName')  # 獲取知識庫名稱
        
        if not query or not model_id or not collection_name:
            return jsonify({'error': '缺少必要參數'}), 400
        
        # 連接到Qdrant
        vector_db = qdrant_DBConnector(collection_name)

        reranked_result = reranker(query, hybrid_retriever_with_kbname(vector_db, kb_name, query, 20), threshold=0.45)
        #reranked_result = reranker(query, hybrid_retriever(vector_db, query, 20), threshold=0.45)
        
        # 格式化檢索結果
        formatted_docs = []
        for i, (score, text, meta) in enumerate(reranked_result):
            formatted_docs.append({
                'text': text,
                'score': float(score),
                'source': f"文檔{i+1}，{meta.get('filename')}",  
                'page': meta.get("page_ref"),
                'image_ref': meta.get("image_ref"),
                'table_ref': meta.get('table_ref')
            })
        
        # 構建提示
        # Job instruction
        instruction = """
        你是台灣國泰集團的聊天機器人秘書，專門為用戶提供公司內外文件內容的解析和答疑，
        你的任務是根據你獲得的「參考文件」，對「用戶問題」段落的問題進行回答。

        請務必根據「參考文件」中的具體資訊作答，並注意以下要求：
        1. 若某些文件內容對回答無幫助，可以忽略，不採用。
        2. 若文件內容對回答有幫助，不要忽略任何一絲細節。
        3. 回答應簡潔、明確，避免冗長，僅提取關鍵資訊。
        4. 若參考文件無法提供答案，請直接回答「我無法根據現有資料回答這個問題」，並不要自行補充。

        嚴格使用繁體中文，避免英文或簡體中文。
        """

        # RAG retrieved documents
        rag_docs = format_rag_output(reranked_result)

        # Prompt template
        prompt = f"""
        # 任務
        {instruction}

        # 參考文件
        {rag_docs}

        # 用戶問題
        {query}
        """

        answer = get_completion(prompt, model_id)
        
        return jsonify({
            'answer': answer,
            'sources': formatted_docs
        })
    except Exception as e:
        return jsonify({'error': f'處理聊天請求時出錯: {str(e)}'}), 500
