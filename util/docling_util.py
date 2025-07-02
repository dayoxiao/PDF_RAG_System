import pandas as pd
import ollama
import os
import base64
import re

from typing import Any, Optional
from typing_extensions import override

from openai import OpenAI

from docling_core.transforms.serializer.base import BaseSerializerProvider, SerializationResult, BaseDocSerializer
from docling_core.transforms.serializer.common import create_ser_result
from docling_core.transforms.serializer.markdown import MarkdownPictureSerializer
from docling_core.types.doc.document import PictureClassificationData, PictureDescriptionData, PictureItem, PictureMoleculeData, DoclingDocument
from docling_core.transforms.chunker.hierarchical_chunker import ChunkingSerializerProvider, ChunkingDocSerializer, DocChunk


class AnnotationPictureSerializer(MarkdownPictureSerializer):

    @override
    def serialize(
        self,
        *,
        item: PictureItem,
        doc_serializer: BaseDocSerializer,
        doc: DoclingDocument,
        separator: Optional[str] = None,
        **kwargs: Any,
    ) -> SerializationResult:
        text_parts: list[str] = []

        image_uri = str(item.image.uri)
        doc_name = doc.origin.filename

        image_caption = summarize_image_openai(doc_name, image_uri)
        #image_caption = "aaaa"

        text_parts.append(image_caption)

        text_res = (separator or "\n").join(text_parts)
        text_res = doc_serializer.post_process(text=text_res)
        return create_ser_result(text=text_res, span_source=item)

class ImgAnnotationSerializerProvider(ChunkingSerializerProvider):
    def get_serializer(self, doc: DoclingDocument):
        return ChunkingDocSerializer(
            doc=doc,
            picture_serializer=AnnotationPictureSerializer(),  # configuring a different picture serializer
        )

def extract_meta_from_docling(DocChunk: DocChunk):
    table_ref = []
    image_ref = []
    page_ref = []
    chunk_meta = DocChunk.export_json_dict()

    chunk_file_name = chunk_meta.get("origin", {}).get("filename")

    for it in chunk_meta.get("doc_items"):
        if it.get("label") == "table":
            self_ref = it.get("self_ref")
            table_ref_count = int(self_ref.split("/")[-1]) + 1
            table_ref_name = f"{os.path.splitext(chunk_file_name)[0]}-table-{table_ref_count}.png"
            table_ref.append(table_ref_name)

        elif it.get("label") == "picture":
            self_ref = it.get("self_ref")
            image_ref_count = int(self_ref.split("/")[-1]) + 1
            image_ref_name = f"{os.path.splitext(chunk_file_name)[0]}-picture-{image_ref_count}.png"
            image_ref.append(image_ref_name)

        for provs in it.get("prov"):
            page_no = provs.get("page_no")
            if page_no not in page_ref:
                page_ref.append(page_no)

    chunk_meta_dict = {"filename": chunk_file_name,
                    "table_ref": table_ref,
                    "image_ref": image_ref,
                    "page_ref": page_ref
                    }
    
    return chunk_meta_dict

# OLD FUNCTION CURRENTLY NO USE
class PatchedChunkingSerializerProvider(BaseSerializerProvider):
    def get_serializer(self, doc: DoclingDocument) -> BaseDocSerializer:
        patch_dict = {"include_hyperlinks": False}
        patched_params = ChunkingDocSerializer(doc=doc).params.merge_with_patch(patch_dict)
        PatchedChunkingDocSerializer = ChunkingDocSerializer(doc=doc)
        PatchedChunkingDocSerializer.params = patched_params
        return PatchedChunkingDocSerializer

def extract_tables(list_dl_doc):
    all_tables = []
    for result in list_dl_doc:
        table_filename, _ = os.path.splitext(result.document.origin.filename)

        for table in result.document.tables:
            self_ref = table.self_ref
            table_ref_name = f"{table_filename}-table-{int(self_ref.split('/')[-1]) + 1}.png"
            page_ref_set = [prov.page_no for prov in table.prov]

            table_meta = {
                "filename": table_filename,
                "table_ref": [table_ref_name],
                "page_ref": page_ref_set
            }

            table_df = table.export_to_dataframe()

            # 該表格無特別索引值，且與上一個處理的表格行數相同，則合併
            if (
                all_tables
                and list(table_df.columns) == list(range(len(table_df.columns)))
                and len(all_tables[-1][0].columns) == len(table_df.columns)
            ):
                prev_df, prev_meta = all_tables.pop()
                table_df.columns = list(prev_df.columns)
                table_df = pd.concat([prev_df, table_df], ignore_index=True)

                if prev_meta["filename"] != table_meta["filename"]:
                    print("WARNING!! MERGE OF TABLE FROM DIFFERENT FILENAME")

                table_meta["page_ref"] = sorted(set(prev_meta["page_ref"]).union(table_meta["page_ref"]), key=abs)
                table_meta["table_ref"] = prev_meta["table_ref"] + table_meta["table_ref"]

            all_tables.append([table_df, table_meta])

    return all_tables

# OLD FUNCTION CURRENTLY NO USE
def df_to_text(list_df_tables):
    str_tables_list = []
    for table_ix, table in enumerate(list_df_tables):
        str_table = f"## Table {table_ix}\n {table.to_markdown()}"
        str_tables_list.append(str_table)
    
    return str_tables_list

def get_embeddings(texts, model='bge-m3:latest'):
    embed_response = ollama.embeddings(model=model, prompt=texts)
    embedded_vector = embed_response["embedding"]
    
    return embedded_vector

# OLD FUNCTION CURRENTLY NO USE
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def summarize_image_openai(filename, image_base64, model="gpt-4o"):
    """
    Args:
        image_base64: base64 encoded string。
        model: used openai model name (default gpt-4o)。

    Returns:
        image summary
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("無效的 OPENAI_API_KEY，請確認你的 .env 檔案中有正確設定。")
    
    openai_client = OpenAI(api_key=api_key)

    prompt = (
        f"請仔細閱讀這張來自文檔「{filename}」的圖片內容。綜合檔名和你看到的圖像資訊，完成以下任務：\n"
        "1. 用簡潔清楚的方式摘要圖片的主要內容。\n"
        "2. 若是不含文字的純圖像，則嘗試描述其所含有的元素及可能想表達的概念。\n"
        "3. 擷取圖片中出現的重要概念、重點事項或關鍵字以利後續搜尋。\n"
        "4. 如果是結構化資訊（如表格、流程圖），請嘗試條列或描述其架構，不要私自精簡原來的文字表達。\n"
        "5. 僅回傳內容，不要加入與提示無關的說明。\n"
        "請以繁體中文回答。\n"
        "請注意，回答內容請控制在 1000 個字以內，不要超過 1024 個 token。"
    )

    if not image_base64.startswith("data:image"):
        image_data_url = "data:image/png;base64," + image_base64
    else:
        image_data_url = image_base64

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ],
        max_tokens=1024
    )

    return response.choices[0].message.content

# OLD FUNCTION CURRENTLY NO USE
def replace_image_tag(txt):
    # 找出所有以 replacement_of: 開頭的 <> 內容
    replacement_matches = re.findall(r"<(replacement_of:[^>]+)>", txt)

    # 提取實際路徑（去除 replacement_of: 前綴）
    replacement_paths = [m.replace("replacement_of:", "", 1) for m in replacement_matches]

    # 移除這些特定的 <replacement_of:...>，保留其他 <>
    clean_text = re.sub(r"<replacement_of:[^>]+>", "", txt)

    return clean_text, replacement_paths