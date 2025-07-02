print("載入 upload_bp")

from flask import Blueprint, jsonify, request
import os
import uuid
from pathlib import Path

from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions, PictureDescriptionApiOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.chunking import HybridChunker
from docling_core.types.doc import PictureItem, TableItem, TextItem
from docling_core.types.doc.labels import DocItemLabel

from huggingface_hub import snapshot_download
from transformers import AutoTokenizer
from .util.docling_util import *
from .util.text_splitter import RecursiveTextSplitter, DataFrameFormatter
from .util.qdrant_util import qdrant_DBConnector, DataObject

upload_bp = Blueprint('upload', __name__)

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
UPLOAD_FOLDER_IMAGE = './figure_storage'
os.makedirs(UPLOAD_FOLDER_IMAGE, exist_ok=True)

@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    # Get collection
    upload_collection = request.form.get('collection')
    if not upload_collection:
        return jsonify({'error': '未提供 collection 名稱'}), 400
    
    # Get KB_name
    kb_name = request.form.get('kb_name')
    if not kb_name:
        return jsonify({'error': '沒有知識庫名部分'}), 400
    if kb_name == '':
        return jsonify({'error': '知識庫名為空'}), 400
    
    # Set Qdrant connection
    vector_db = qdrant_DBConnector(upload_collection, recreate=False)
    new_kb_name, kb_id = vector_db.find_existing_or_create_kb_folder(UPLOAD_FOLDER, kb_name)

    # Convertion settings
    if request.form.get("do_ocr") == "true":
        do_ocr = True 
    else: 
        do_ocr = False
    if request.form.get("do_image_summary") == "true":
        do_image_summary = True 
    else:
        do_image_summary = False
    
    # Get file
    if 'file' not in request.files:
        return jsonify({'error': '沒有文件部分'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '沒有選擇文件'}), 400
    
    if file and file.filename.endswith('.pdf'):
        original_filename = file.filename
        file_ext = os.path.splitext(original_filename)[1]
        basename = os.path.splitext(original_filename)[0]

        # 移除特殊字元但保留中文
        safe_basename = ''.join(c for c in basename if c.isalnum() or '\u4e00' <= c <= '\u9fff')[:30]
        file_id = str(uuid.uuid4())[:8]
        new_filename = f"{safe_basename}_{file_id}{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, new_kb_name, new_filename)
        #print(file_path)
        file.save(file_path)
        
        # 處理PDF文檔
        try:
            # 設置docling處理選項
            if do_ocr:
                # PyPdfium with RapidOCR
                # ----------------------
                # Download RappidOCR models from HuggingFace
                print("Downloading RapidOCR models")
                download_path = snapshot_download(repo_id="SWHL/RapidOCR")

                det_model_path = os.path.join(
                    download_path, "PP-OCRv4", "ch_PP-OCRv4_det_infer.onnx"
                )
                rec_model_path = os.path.join(
                    download_path, "PP-OCRv4", "ch_PP-OCRv4_rec_infer.onnx"
                )
                cls_model_path = os.path.join(
                    download_path, "PP-OCRv3", "ch_ppocr_mobile_v2.0_cls_train.onnx"
                )
                ocr_options = RapidOcrOptions(
                    det_model_path=det_model_path,
                    rec_model_path=rec_model_path,
                    cls_model_path=cls_model_path,
                    #force_full_page_ocr=True
                )

                pipeline_options = PdfPipelineOptions()

                pipeline_options.do_ocr = True
                pipeline_options.do_table_structure = True
                pipeline_options.table_structure_options.do_cell_matching = True
                pipeline_options.table_structure_options.mode = 'accurate'

                pipeline_options.images_scale = 2.0
                pipeline_options.generate_page_images = True
                pipeline_options.generate_picture_images = True

                pipeline_options.ocr_options = ocr_options

                pypdfium_converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options, backend=PyPdfiumDocumentBackend
                        )
                }
                )

            else:
                # PyPdfium without EasyOCR
                # --------------------
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = False
                pipeline_options.do_table_structure = True
                pipeline_options.table_structure_options.do_cell_matching = False
                #pipeline_options.table_structure_options.do_cell_matching = True

                #pipeline_options.table_structure_options.mode = 'accurate'

                pipeline_options.images_scale = 2
                pipeline_options.generate_page_images = True
                pipeline_options.generate_picture_images = True

                pypdfium_converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options, backend=PyPdfiumDocumentBackend
                        )
                    }
                )
            
            # 轉換文檔
            conv_results = pypdfium_converter.convert_all(
                [file_path],
                raises_on_error=True,  # to let conversion run through all and examine results at the end
            )
            conv_results_list = list(conv_results)

            # 提取表格或圖片截圖
            # Save images of figures and tables for later summary reference
            for conv_res in conv_results_list:
                docling_docs = conv_res.document
                doc_filename = conv_res.input.file.stem
                table_counter = 0
                picture_counter = 0
                
                for element, _level in docling_docs.iterate_items():
                    if isinstance(element, TableItem):
                        table_counter += 1
                        table_name = f"{doc_filename}-table-{table_counter}.png"
                        element_image_filename = Path(os.path.join(
                            UPLOAD_FOLDER_IMAGE, table_name
                        ))
                        with element_image_filename.open("wb") as fp:
                            element.get_image(docling_docs).save(fp, "PNG")

                    if isinstance(element, PictureItem):
                        picture_counter += 1
                        picture_name = f"{doc_filename}-picture-{picture_counter}.png"
                        element_image_filename = Path(os.path.join(
                            UPLOAD_FOLDER_IMAGE, picture_name
                        ))
                        with element_image_filename.open("wb") as fp:
                            element.get_image(docling_docs).save(fp, "PNG")
            
            # 創建分塊器
            tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")
            if do_image_summary:
                hybrid_chunker = HybridChunker(
                    tokenizer=tokenizer,
                    max_tokens=8000,
                    serializer_provider=ImgAnnotationSerializerProvider(),
                )
            else:
                hybrid_chunker = HybridChunker(
                    tokenizer=tokenizer,
                    max_tokens=8000,
                    merge_peers=True  # optional, defaults to True
                )
            
            # 分塊
            all_chunks = []
            for conv_res in conv_results_list:
                docling_docs = conv_res.document
                chunk_iter = hybrid_chunker.chunk(dl_doc=docling_docs)
                chunks = list(chunk_iter)
                all_chunks += chunks
            
            # 處理大塊文本
            big_chunk = []
            for i, chunk in enumerate(all_chunks):
                if type(chunk) == tuple:
                    ser_txt = chunk[0]
                else:
                    ser_txt = hybrid_chunker.contextualize(chunk=chunk)
                ser_tokens = len(tokenizer.tokenize(ser_txt))
                if ser_tokens > 1024:
                    #print(f"=== {i} ===")
                    #print(f"chunker.serialize(chunk) ({ser_tokens} tokens):\n{repr(ser_txt)}")
                    #print(f"chunker.serialize(chunk) ({ser_tokens} tokens):\n{ser_txt}")
                    big_chunk.append(chunk)
                    #print()
                else:
                    pass
                
            splitter = RecursiveTextSplitter(tokenizer=tokenizer, max_tokens=1024, overlap=150, min_length_ratio=1)

            rechunked_large_chunks = []

            for i, chunk in enumerate(big_chunk):
                if type(chunk) == tuple:
                    ser_txt = chunk[0]
                else:
                    ser_txt = hybrid_chunker.contextualize(chunk=chunk)
                    
                if splitter.tokenize_len(ser_txt) > splitter.max_tokens:
                    sub_chunks = splitter.split_text(ser_txt)
                    #sub_chunks_meta = {"filename": chunk.meta.origin.filename}
                    sub_chunks_meta = extract_meta_from_docling(chunk.meta)
                    sub_chunks_pair = [(text, sub_chunks_meta) for text in sub_chunks]
                    rechunked_large_chunks.extend(sub_chunks_pair)
                else:
                    rechunked_large_chunks.append(ser_txt)
            
            # 提取表格
            all_tables = extract_tables(conv_results_list)
            table_formatter = DataFrameFormatter(tokenizer=tokenizer, show_index=False, max_tokens=1024)

            table_chunks = []
            for table in all_tables:
                chunks = table_formatter.chunk_rows(table[0])
                chunks_pair = [(text, table[1]) for text in chunks]
                table_chunks.extend(chunks_pair)
            
            # 匯總所有分切的chunk
            all_chunks.extend(rechunked_large_chunks)
            all_chunks.extend(table_chunks)

            # 分割text, metadata
            node_text, node_metadatas = [], []
            for chunk in all_chunks:
                if type(chunk) == tuple:
                    node_text.append(chunk[0])
                    basename, _ = os.path.splitext(chunk[1]["filename"])
                    file_id = basename.split('_')[-1]
                    chunk[1]["file_id"] = file_id
                    chunk[1]["kb_name"] = new_kb_name
                    chunk[1]["kb_id"] = kb_id
                    #node_metadatas.append(json.dumps(meta_dict, indent=4, ensure_ascii=False))
                    node_metadatas.append(chunk[1])
                else:
                    node_text.append(hybrid_chunker.contextualize(chunk=chunk))
                    meta_dict = extract_meta_from_docling(chunk.meta)
                    basename, _ = os.path.splitext(meta_dict.get("filename"))
                    file_id = basename.split('_')[-1]
                    meta_dict["file_id"] = file_id
                    meta_dict["kb_name"] = new_kb_name
                    meta_dict["kb_id"] = kb_id
                    #node_metadatas.append(json.dumps(meta_dict, indent=4, ensure_ascii=False))
                    node_metadatas.append(meta_dict)
            
            # 生成嵌入向量
            embedded_text = []
            for i in node_text:
                embedded_text.append(get_embeddings(i))
            
            # 存儲到Qdrant
            data = DataObject(node_text, node_metadatas)
            #vector_db = qdrant_DBConnector("qdrant_new", recreate=True)
            vector_db.upsert_vector(embedded_text, data)
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'filename': original_filename,
                'kb_name': new_kb_name,
                'do_ocr': do_ocr,
                'do_image_summary': do_image_summary
                #'chunks_count': len(chunks),
                #'tables_count': 0
            })
            
        except Exception as e:
            return jsonify({'error': f'處理文件時出錯: {str(e)}'}), 500
    
    return jsonify({'error': '不支持的文件類型'}), 400