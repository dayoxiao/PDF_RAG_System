import axios from 'axios';

// API基礎URL，根據實際部署環境修改
const API_BASE_URL = process.env.REACT_APP_API_URL
  ? `${process.env.REACT_APP_API_URL}/api/`
  : 'http://localhost:5050/api/';
//const API_BASE_URL = 'http://127.0.0.1:5050/api/';

// PDF文檔上傳API
export const uploadPdfDocument = async (file, collection, kbName, doOcr = false, doImageSummary = false) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('collection', collection);
  formData.append('kb_name', kbName);
  formData.append('do_ocr', doOcr.toString());
  formData.append('do_image_summary', doImageSummary.toString());
  
  try {
    const response = await axios.post(`${API_BASE_URL}upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading document:', error);
    throw error;
  }
};

// 獲取Ollama模型列表API
export const getOllamaModels = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}models`);
    return response.data;
  } catch (error) {
    console.error('Error fetching models:', error);
    throw error;
  }
};

// 獲取Qdrant集合列表API
export const getQdrantCollections = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}collections`);
    return response.data;
  } catch (error) {
    console.error('Error fetching collections:', error);
    throw error;
  }
};

// 獲取集合統計信息API
export const getCollectionStats = async (collectionName) => {
  try {
    const response = await axios.get(`${API_BASE_URL}collectionStatus/${collectionName}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching collection stats:', error);
    throw error;
  }
};

// 聊天問答API
export const chatWithRag = async (query, modelId, collectionName, kbName) => {
  try {
    const response = await axios.post(`${API_BASE_URL}chat`, {
      query,
      model: modelId,
      collection: collectionName,
      kbName: kbName
    });
    return response.data;
  } catch (error) {
    console.error('Error in chat:', error);
    throw error;
  }
};

// 刪除文檔API
export const deleteDocument = async (documentId, filename, kbName, collectionName) => {
  try {
    const response = await axios.post(`${API_BASE_URL}delete`, {
      document_id: documentId,
      filename: filename,
      kb_name: kbName,
      collection: collectionName,
    });
    return response.data;
  } catch (error) {
    console.error(`Error deleting document ${documentId}:`, error);
    throw error;
  }
};

// 獲取系統狀態API
export const getSystemStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}status`);
    return response.data;
  } catch (error) {
    console.error('Error fetching system status:', error);
    throw error;
  }
};

// 獲取知識庫列表API
export const getKnowledgeBases = async (collectionName) => {
  try {
    const response = await axios.get(`${API_BASE_URL}knowledgeBases/${collectionName}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching knowledge bases for collection ${collectionName}:`, error);
    throw error;
  }
};

// 獲取知識庫文件列表API
export const getKnowledgeBaseDocuments = async (collectionName, kbName) => {
  try {
    const response = await axios.post(`${API_BASE_URL}knowledgeBasesDoc`, {
      collection: collectionName,
      kb_name: kbName,
    });
    return response.data;
  } catch (error) {
    console.error(`Error fetching documents for knowledge base ${kbName} in collection ${collectionName}:`, error);
    throw error;
  }
};
