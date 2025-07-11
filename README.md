# 本地 RAG 知識引擎 (Local RAG Knowledge Engine)

## 專案概述

這是一個基於檢索增強生成 (Retrieval-Augmented Generation, RAG) 的本地化文件智能問答系統。系統支援處理 PDF 文檔，OCR，提取及註解表格和圖片內容，並將分塊過後的內文存入向量資料庫進行後續智能檢索和問答。  
使用docling框架解析文件，測試時embedding使用BGE-M3，reranker使用bge-reranker-v2-m3，問答大模型為deepseek:7b。

### 主要功能

- **多格式文檔處理**: 支援 PDF 文檔上傳和解析
- **智能內容提取**: 自動提取文字、表格結構和圖片內容
- **OCR 文字識別**: 可選的 OCR 功能，支援中文文字識別
- **向量化檢索**: 使用 Qdrant 向量資料庫進行語義檢索
- **混合檢索**: 結合 BM25 和向量檢索的混合檢索策略
- **知識庫管理**: 支援多個知識庫的創建和管理
- **智能問答**: 基於檢索結果的智能問答功能
- **模型選擇**: 支援多種 LLM 模型選擇 (Ollama)

## 系統架構
切換到`RAG_system/`看最終版本的完整系統

### 前端 (Frontend)
- **技術棧**: React 18 + Ant Design
- **位置**: `rag_deployment/`
- **主要組件**:
  - `FileUploadComponent`: 文件上傳和處理
  - `ChatInterfaceComponent`: 聊天介面
  - `ModelSelectionComponent`: ollama模型選擇管理
  - `QdrantConnectionComponent`: 資料庫連接管理
  - `SystemStatusComponent`: 系統狀態監控

### 後端 (Backend)
- **技術棧**: Flask + Python
- **位置**: `flask_backend/`
- **主要模組**:
  - `app.py`: 主應用程式入口
  - `routes/`: API 路由模組
    - `upload.py`: 文件上傳及處理
    - `chat.py`: 資料抓取與聊天回答功能
    - `collections.py`: 獲取Qdrant集合資料
    - `collectionStatus.py`: 各集合狀態統計
    - `models.py`: ollama模型資料獲取
    - `knowledgeBases.py`: 知識庫管理
    - `knowledgeBasesDoc.py`: 知識庫文檔管理 (獲取特定知識庫的文件列表)
    - `docRemove.py`: 文檔刪除
    - `status.py`: 系統狀態
    - `staticFiles.py`: 靜態文件服務 (提供 figure_storage 目錄下的圖片文件)
  - `util/`: 工具模組
    - `qdrant_util.py`: Qdrant collection連接及相關操作
    - `ollama_util.py`: 聊天回答相關操作，包括混合檢索及ollama回覆
    - `docling_util.py`: docling相關，文件提取操作
    - `text_splitter.py`: RecursiveTextSplitter, docling分切chunk大於1024 token時的rechunk方法
  - `BM25/`: BM25 檢索模組
    - `bm25.py`: 多語言 BM25 檢索實現 (英文、中文、混合語言)
    - `detect_language.py`: 語言檢測功能，自動識別文檔主要語言
    - `stopwords.py`: 預設多語言停用詞庫 (英文、簡體中文、繁體中文)
    - `dict.txt.big`: 中文詞典文件用於分詞

## 技術特色

### 文檔處理
- **Docling**: 使用 Docling 框架進行 PDF 文檔解析
- **PyPdfium**: 高品質 PDF 渲染和處理
- **RapidOCR**: 中文 OCR 文字識別
- **混合分塊**: 結合語義和結構的智能文本分塊

### 向量檢索
- **Qdrant**: 高性能向量數據庫
- **BGE-M3**: 多語言嵌入模型
- **混合檢索**: BM25 + 向量檢索的組合策略
- **重排序**: 基於相關性的結果重排序

### BM25 檢索
- **多語言支援**: 支援英文、中文、混合語言檢索
- **語言檢測**: 自動檢測文檔主要語言並選擇相應處理策略
- **智能分詞**: 英文使用 PyStemmer，中文使用 jieba 分詞
- **停用詞過濾**: 內建多語言停用詞庫，提升檢索精度
- **參數調優**: 支援 k1 和 b 參數調整，優化檢索效果
- **索引持久化**: 支援 JSON 和 Pickle 格式保存/載入索引

### 語言模型
- **Ollama**: 本地化 LLM 部署
- **多模型支援**: 支援多種開源模型
- **提示工程**: 針對國泰集團業務的專業提示設計

## 安裝指南

### 系統需求
測試時環境為
- Python 3.10
- Node.js 16+
- Docker (未測試)

### 後端安裝

1. **進入後端目錄**
```bash
cd flask_backend
```

2. **安裝依賴**
```bash
pip install -r requirements.txt
```

3. **設定.env檔（如果要使用圖片摘要功能）**
```
OPENAI_API_KEY = "My_api_key"
```

### 前端安裝

1. **進入前端目錄**
```bash
cd rag_deployment
```

2. **安裝依賴**
```bash
npm install
npm run build
```

## 使用指南

### 啟動系統

1. **啟動後端服務**
```bash
cd flask_backend
python app.py
```
後端服務將在 `http://localhost:5050` 運行

2. **啟動前端服務**
```bash
cd rag_deployment
serve -s build
```
前端服務將在 `http://localhost:3000` 運行

### 基本操作流程

1. **連接 Qdrant 數據庫**
   - 在左側面板選擇集合
   - 確保數據庫連接正常

2. **選擇語言模型**
   - 在模型選擇區域選擇可用的 Ollama 模型
   - 確保模型已正確載入

3. **上傳文檔**
   - 選擇要上傳的 PDF 文檔
   - 配置處理選項 (OCR、圖片摘要)
   - 選擇目標知識庫或輸入新名字創建
   - 點擊上傳開始處理

4. **開始問答**
   - 在聊天介面輸入問題
   - 系統將基於知識庫內上傳的文檔進行智能回答
   - 查看檢索到的相關文檔片段

### 進階功能

#### 知識庫管理
- 創建多個知識庫來組織不同類型的文檔
- 支援知識庫的刪除和更新

#### 文檔處理選項
- **OCR 處理**: 啟用後可識別圖片中的文字
- **圖片摘要**: 生成圖片內容的摘要（利於擷取流程圖等重要資訊）
- **表格結構**: 自動提取和保留表格的結構信息

#### 系統監控
- 實時監控 CPU 和記憶體使用情況
- 查看錯誤信息

## API 文檔

### 主要端點

#### 文件上傳
```
POST /api/upload - 上傳 PDF 文件並寫入向量資料庫

請求格式：
Content-Type: multipart/form-data

參數：
- file: PDF 文件
- collection: 集合名稱
- kb_name: 知識庫名稱
- do_ocr: 是否啟用 OCR (true/false)
- do_image_summary: 是否生成圖片摘要 (true/false)

回應格式：
{
  "success": true/false,
  "message": "訊息",
  ...
}
```

#### 聊天問答
```
POST /api/chat - 基於知識庫進行智能問答

請求格式：
Content-Type: application/json
{
  "query": "用戶問題",
  "model": "模型名稱",
  "collection": "集合名稱",
  "kbName": "知識庫名稱"
}

回應格式：
{
  "answer": "回答內容",
  "sources": [
    {
      "text": "相關片段",
      "score": 分數,
      "source": "來源描述",
      ...
    },
    ...
  ]
}
```

#### 模型管理
```
GET /api/models - 取得 Ollama 服務上可用的模型列表

請求格式：
無需 body

回應格式：
[
  {
    "id": "模型ID",
    "name": "模型名稱",
    "size": "模型大小",
    "description": "描述",
    "tags": ["general"],
    "loaded": true/false
  },
  ...
]
```

#### 集合管理
```
GET /api/collections - 取得 Qdrant 上所有集合的列表

請求格式：
無需 body

回應格式：
[
  {
    "name": "集合名稱",
    "description": "描述",
    "vectorCount": 向量數量,
    "vectorDimension": 向量維度
  },
  ...
]
```

#### 集合狀態統計
```
GET /api/collectionStatus/{collection_name} - 取得集合統計資訊

請求格式：
無需 body

回應格式：
{
  "vectorCount": 向量數量,
  "vectorDimension": 向量維度,
  "segmentCount": 段數量,
  "indexType": 索引類型,
  "diskUsage": "磁碟使用量 (MB)",
  "created": "創建時間",
  "lastModified": "最後修改時間"
}
```

#### 知識庫管理
```
GET /api/knowledgeBases/{collection_name} - 取得指定集合下的知識庫名稱列表

請求格式：
無需 body

回應格式：
{
  "knowledge_bases": ["知識庫1", "知識庫2", ...]
}
```

#### 知識庫文檔管理
```
POST /api/knowledgeBasesDoc - 取得特定知識庫的文件列表

請求格式：
Content-Type: application/json
{
  "collection": "集合名稱",
  "kb_name": "知識庫名稱"
}

回應格式：
[
  {
    "filename": "文件名稱",
    "file_id": "文件ID",
    "kb_name": "知識庫名稱"
  },
  ...
]
```

#### 文件刪除
```
POST /api/delete - 刪除指定文件（同時從 Qdrant 及檔案系統移除）

請求格式：
Content-Type: application/json
{
  "document_id": "文件ID",
  "filename": "原始檔名",
  "kb_name": "知識庫名稱",
  "collection": "Qdrant集合名稱"
}

回應格式：
{
  "success": true/false,
  "message": "訊息",
  "details": {
    "file_deleted": true/false,
    "vectors_deleted": true/false,
    "vectors_count": 數量
  },
  ...
}
```

#### 系統狀態
```
GET /api/status - 查詢系統 CPU、記憶體等即時狀態

請求格式：
無需 body

回應格式：
{
  "status": "idle|processing|error",
  "message": "系統訊息",
  "cpuUsage": 百分比,
  "memoryUsage": 百分比,
  "lastUpdated": "ISO 時間字串"
}
```

#### 靜態文件服務
```
GET /api/figure_storage/{filename} - 取得 figure_storage 目錄下的圖片文件

請求格式：
無需 body

回應：
圖片二進位內容（image/png 等）
```

## 部署選項

### 本地部署
- 如上述

### Docker 部署
- 使用提供的 Dockerfile 進行容器化部署
- 未測試

## 開發指南

### 程式碼結構
```
RAG_system/
├── flask_backend/          # 後端服務
│   ├── app.py             # 主應用程式
│   ├── routes/            # API 路由
│   ├── util/              # 工具模組
│   ├── uploads/           # 上傳文件存儲
│   └── figure_storage/    # 圖片存儲
└── rag_deployment/        # 前端應用
    ├── src/
    │   ├── components/    # React 組件
    │   ├── App.js         # 主應用組件
    │   └── api.js         # API 調用
    └── public/            # 靜態資源
```
---

**版本**: 1.0.0  
**最後更新**: 2025年  
**維護者**: dayoxiao
