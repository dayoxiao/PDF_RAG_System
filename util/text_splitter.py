import re
import pandas as pd

class RecursiveTextSplitter:
    def __init__(self, tokenizer, max_tokens=1024, overlap=100, min_length_ratio=0.7):
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.min_length_ratio = min_length_ratio

        # chinese text splitter
        self.separators = [
            r"(?<=[。！？])",  # 一般斷句
            r"(?<=[；，、])",  # 較弱的斷詞點
            r"(?=\n+)",       # 換行
            r"(?=\s+)",       # 空格
            r""               # fallback：逐字切
        ]

    def tokenize_len(self, text):
        return len(self.tokenizer.tokenize(text))

    def split_text(self, text):
        for sep in self.separators:
            parts = re.split(sep, text)
            parts = [p for p in parts if p.strip() != '']
            chunks = self._recursive_split(parts)
            if all(self.tokenize_len(chunk) <= self.max_tokens + 2 for chunk in chunks):
                return chunks
        # fallback: force token split
        return self._force_split(text)

    def _recursive_split(self, parts):
        chunks = []
        current = ""
        for part in parts:
            if self.tokenize_len(current + part) <= self.max_tokens:
                current += part
            else:
                if current:
                    chunks.append(current)
                current = part
        if current:
            chunks.append(current)
        return self._apply_overlap(chunks)

    def _force_split(self, text):
        tokens = self.tokenizer.tokenize(text)
        total_tokens = len(tokens)
        chunks = []
        start = 0

        while start < total_tokens:
            end = min(start + self.max_tokens, total_tokens)
            chunk_tokens = tokens[start:end]

            # fill to max_token at last chunk
            if end == total_tokens and len(chunk_tokens) < self.max_tokens and start != 0:
                tokens_needed = self.max_tokens - len(chunk_tokens)
                prev_start = max(0, start - tokens_needed)
                chunk_tokens = tokens[prev_start:end]

            chunk_text = self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(chunk_tokens))
            chunks.append(chunk_text)

            if end == total_tokens:
                break
            start = end - self.overlap
        #print("this chunk was force splitted!")
        return chunks
    
    def _apply_overlap(self, chunks):
        result = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                result.append(chunk)
            else:
                prev_chunk = result[-1]
                current_tokens = self.tokenize_len(chunk)

                if i == len(chunks) - 1 and current_tokens < self.max_tokens * self.min_length_ratio:
                    # fill to max_token at last chunk
                    prev_tokens = self.tokenizer.tokenize(prev_chunk)
                    tokens_needed = self.max_tokens - current_tokens
                    extra_overlap_tokens = min(tokens_needed, len(prev_tokens))

                    extra_overlap_text = self.tokenizer.decode(
                        self.tokenizer.convert_tokens_to_ids(prev_tokens[-extra_overlap_tokens:])
                    )
                    result.append(extra_overlap_text + chunk)

                else:
                    # regular fixed token overlap
                    prev_tokens = self.tokenizer.tokenize(prev_chunk)
                    overlap_text = self.tokenizer.decode(
                        self.tokenizer.convert_tokens_to_ids(prev_tokens[-self.overlap:])
                    )
                    result.append(overlap_text + chunk)
        #print(result)
        #for j in result:
        #    print(self.tokenize_len(j))
        return result
    
class DataFrameFormatter:
    def __init__(self, tokenizer, show_index=False, max_tokens=1024):
        self.tokenizer = tokenizer
        self.show_index = show_index
        self.max_tokens = max_tokens

    @staticmethod
    def format_row(series_row, row_index=None, show_index=False):
        output = []
        for key, value in series_row.items():
            if pd.notnull(value) and str(value).strip() != "":
                entry = f"{key} = {value}"
                if show_index:
                    entry += f". {row_index}"
                output.append(entry)
        return ', '.join(output)

    def format_all_rows(self, df: pd.DataFrame):
        return [
            self.format_row(row, idx + 1, self.show_index)
            for idx, row in df.iterrows()
        ]

    def chunk_rows(self, df: pd.DataFrame):
        formatted_rows = self.format_all_rows(df)
        chunks = []
        current_chunk = []
        current_tokens = 0

        for row in formatted_rows:
            row_tokens = len(self.tokenizer.tokenize(row))
            if current_tokens + row_tokens <= self.max_tokens:
                current_chunk.append(row)
                current_tokens += row_tokens
            else:
                # 儲存目前 chunk
                chunks.append('\n'.join(current_chunk))
                # 開始新的 chunk
                current_chunk = [row]
                current_tokens = row_tokens

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks