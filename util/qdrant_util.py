from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct
from util.docling_util import get_embeddings
import uuid

class qdrant_DBConnector:
    def __init__(self, collection_name, recreate=False):#, embedding_fn):
        self.qdrant_client = QdrantClient("http://localhost:6333")

        self.collection_name = collection_name
        all_collections = self.qdrant_client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in all_collections)

        # create collection
        if recreate == True or not collection_exists:
            self.collection = self.qdrant_client.recreate_collection(
                collection_name = collection_name,
                vectors_config = models.VectorParams(
                    distance = models.Distance.COSINE,
                    size=len(get_embeddings("你好"))),
                optimizers_config = models.OptimizersConfigDiff(memmap_threshold=20000),
                hnsw_config = models.HnswConfigDiff(on_disk=True, m=16, ef_construct=100)
            )
        
        
        '''
        # embed models
        self.embedding_fn = embedding_fn
        qdrant_client.set_model(self.embedding_fn)
        '''

    ''' WARNING: NO CHECK ON EQUAL LENGTH YET'''
    def upsert_vector(self, vectors, data):
        # insert 'points' to qdrant by vector, 
        # payload with original text and metadata
        for i, vector in enumerate(vectors):
            """ WARNING: SHOULD CHECK DIMENSION==EMBEDDING_DIMENSION INSTEAD"""
            if len(vector) == 0:
                continue
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=str(uuid.uuid4()),
                                    #id=i,
                                    vector=vectors[i],
                                    payload={"text": data.text[i],
                                             "metadata": data.metadata[i]})]
                                    
            )

        print("upsert finish")

    def retrieved_all(self):
        count_points = self.qdrant_client.count(
            collection_name=self.collection_name,
            exact=True,
        )

        result = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            limit=count_points.count,
        )[0]
        """result = self.qdrant_client.retrieve(
            collection_name=self.collection_name,
            ids=list(range(0, count_points.count)),
        )"""
        return result
    
    def retrieved_from_kb(self, kb_name):
        count_points = self.qdrant_client.count(
            count_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.kb_name",
                        match=models.MatchValue(value=kb_name)
                    )
                ]
            ),
            collection_name=self.collection_name,
            exact=True
        )

        result = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.kb_name",
                        match=models.MatchValue(value=kb_name)
                    ),
                ]
            ),
            limit=count_points.count,
            with_payload=True,
        )[0]
        return result

    def vector_search(self, vector, top_k):
        # vector search qdrant DB
        result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=top_k,
            append_payload=True,
        )
        return result
    
    def vector_search_json(self, vector, top_k):
        # vector search qdrant DB with json format output
        result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=top_k,
            append_payload=True,
        )
        vector_result_json = {
            f"chunk_{item.id}": {
                "text": item.payload['text'],
                "metadata": item.payload['metadata'],
                "rank": index,
                "score": item.score
            }
            for index, item in enumerate(result)
        }

        return vector_result_json
    
    def vector_search_json_with_kb_name(self, kb_name, vector, top_k):
        # vector search qdrant DB with json format output
        result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.kb_name",
                        match=models.MatchValue(value=kb_name)
                    ),
                ]
            ),
            limit=top_k,
            append_payload=True,
        )
        vector_result_json = {
            f"chunk_{item.id}": {
                "text": item.payload['text'],
                "metadata": item.payload['metadata'],
                "rank": index,
                "score": item.score
            }
            for index, item in enumerate(result)
        }

        return vector_result_json
    
class DataObject:
    def __init__(self, text, metadata):
        self.text = text
        self.metadata = metadata if metadata else [{} for _ in range(len(text))]