import ollama
from routes.BM25 import bm25_search
from sentence_transformers import CrossEncoder
import os

def get_ollama_client():
    # 檢查是否在 Docker 環境中運行
    import socket
    try:
        socket.gethostbyname('ollama')
        # 如果在 Docker 環境中，使用 ollama 主機名
        ollama_host = os.getenv('OLLAMA_HOST', 'ollama')
    except socket.gaierror:
        # 如果在本地開發環境中，使用 localhost
        ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
    
    ollama_port = int(os.getenv('OLLAMA_PORT', 11434))
    base_url = f"http://{ollama_host}:{ollama_port}"
    return ollama.Client(host=base_url)

def get_embeddings(texts, model='bge-m3:latest'):
    client = get_ollama_client()
    embed_response = client.embeddings(model=model, prompt=texts)
    embedded_vector = embed_response["embedding"]
    return embedded_vector

def bm25_retrieval(vector_db_name, query, top_k=3):
    result = vector_db_name.retrieved_all()
    retrieved_text = []
    retrieved_meta =[]
    retrieved_pointID = []
    for point in result:
        retrieved_text.append(point.payload['text'])
        retrieved_meta.append(point.payload['metadata'])
        retrieved_pointID.append(point.id)

    bm25_result = bm25_search(corpus=retrieved_text, query=query, top_k=top_k)
    bm25_result_json = {
        f"chunk_{retrieved_pointID[item[0]]}": {
            "text": item[2],
            "metadata": retrieved_meta[item[0]],
            "rank": index,
            "score": item[1]
        }
        for index, item in enumerate(bm25_result)
    }

    return bm25_result_json

def bm25_retrieval_with_kb_name(vector_db_name, kb_name, query, top_k=3):
    #result = vector_db_name.retrieved_all()
    result = vector_db_name.retrieved_from_kb(kb_name)
    retrieved_text = []
    retrieved_meta =[]
    retrieved_pointID = []
    for point in result:
        retrieved_text.append(point.payload['text'])
        retrieved_meta.append(point.payload['metadata'])
        retrieved_pointID.append(point.id)

    bm25_result = bm25_search(corpus=retrieved_text, query=query, top_k=top_k)
    bm25_result_json = {
        f"chunk_{retrieved_pointID[item[0]]}": {
            "text": item[2],
            "metadata": retrieved_meta[item[0]],
            "rank": index,
            "score": item[1]
        }
        for index, item in enumerate(bm25_result)
    }

    return bm25_result_json

def rrf(ranks, k=1):
    ret = {}
    # recursive through all retrieved method
    for rank in ranks:
        for id, val in rank.items():
            if id not in ret:
                ret[id] = {"score": 0, "text": val["text"], "metadata": val["metadata"]}
            # calculate rrf score
            ret[id]["score"] += 1.0/(k+val["rank"])
    # sort and return according to rrf score
    return dict(sorted(ret.items(), key=lambda item: item[1]["score"], reverse=True))

def get_completion(prompt, model):
    client = get_ollama_client()
    messages = [{"role": "user", "content": prompt}]
    response = client.chat(
        model=model,
        messages=messages
        #stream=True,
        #format="json",
        #options={"temperature":0}
    )
    return response.message.content

def hybrid_retriever(vector_db, query, top_k=3):
    embedded_query = get_embeddings(query)
    result = rrf([vector_db.vector_search_json(embedded_query, top_k), bm25_retrieval(vector_db, query, top_k=top_k)])
    return result

def hybrid_retriever_with_kbname(vector_db, kb_name, query, top_k=3):
    embedded_query = get_embeddings(query)
    result = rrf([vector_db.vector_search_json_with_kb_name(kb_name, embedded_query, top_k), bm25_retrieval_with_kb_name(vector_db, kb_name, query, top_k=top_k)])
    return result

def reranker(query, retrieved_result, rerank_model=CrossEncoder('BAAI/bge-reranker-v2-m3', max_length=1024), threshold=0):
    text_chunks = []
    meta_chunks = []
    for chunk_id, val in retrieved_result.items():
        text_chunks.append(val['text'])
        meta_chunks.append(val['metadata'])
    scores = rerank_model.predict([(query, doc) for doc in text_chunks])
    sorted_list = sorted(zip(scores, text_chunks, meta_chunks), key=lambda x: x[0], reverse=True)
    reranked_result = [chunk for chunk in sorted_list if chunk[0] > threshold]
    if len(reranked_result) < 3:
        reranked_result = sorted_list[:3]
    elif len(reranked_result) > 5:
        reranked_result = reranked_result[:5]

    return reranked_result
    #return [chunk for chunk in sorted_list if chunk[0] > threshold]

def format_rag_output(reranked_list):
    formatted_docs = "\n\n".join([f"Document {i+1}，{chunk[2].get('filename')}:\n{chunk[1]}" for i, chunk in enumerate(reranked_list)])
    return formatted_docs

"""def hybrid_retriever_with_BM25table(vector_db, query, top_k=3):
    embedded_query = get_embeddings(query)
    result = rrf([vector_db.vector_search_json(embedded_query, top_k), bm25_retrieval(query, top_k=top_k), bm25_retrieval(query, vector_db_table, top_k)])
    return result"""
