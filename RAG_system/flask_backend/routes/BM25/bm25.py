from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
import math
import jieba
import Stemmer  # PyStemmer for english stemmer extraction
import re  # english text preprocessing
import json  # save and load as json format
import pickle  # save and load as pickle
import os
from .stopwords import (
    STOPWORDS_EN_PLUS,
    STOPWORDS_CHINESE,
    STOPWORDS_ZH_TW
)

from .detect_language import tokenizer_detect_language

jieba.set_dictionary(os.path.join(os.path.dirname(__file__), 'dict.txt.big'))
#jieba.set_dictionary('dict.txt.big')

# abstract class
class AbstractBM25(ABC):
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75, stopwords: tuple = ()):
        """
        abstract class for core BM25 function
        
        Args:
            corpus: list of strings, from document sets
            k1: usually 1.2 to 2.0, parameter of term frequency saturation(TF)
            b: usually 0 to 1, parameter of length normalization
            stopwords: tuple, from stopwords
        Raises:
            ValueError: if corpus is empty
        """
        if not corpus:
            raise ValueError("Corpus cannot be empty")
        self.corpus: List[str] = corpus
        self.k1: float = k1
        self.b: float = b
        self.stopwords: set = set(stopwords)  # transform to set for performance
        self.doc_count: int = len(corpus)

        # doc after tokenize, implement by sub classes
        self.tokenized_corpus: List[List[str]] = self._tokenize_corpus()

        # calculate length of each doc (number of WORDS)
        self.doc_lengths: List[int] = [len(tokens) for tokens in self.tokenized_corpus]

        # calculate average doc length
        self.avg_doc_length: float = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0

        # DF, TF
        self.df: Dict[str, int] = {}  # data frequency
        self.tf: List[Dict[str, int]] = []  # term frequency
        self._build_index()

    @abstractmethod
    def _tokenize(self, text: str) -> List[str]:
        """abstract method, tokenize given text"""
        pass

    def _tokenize_corpus(self) -> List[List[str]]:
        """tokenize the whole given doc"""
        return [self._tokenize(doc) for doc in self.corpus]

    def _build_index(self):
        """build TF, DF index"""
        for doc_id, tokens in enumerate(self.tokenized_corpus):
            term_freq = {}
            for term in tokens:
                term_freq[term] = term_freq.get(term, 0) + 1
            self.tf.append(term_freq)
            for term in set(tokens):
                self.df[term] = self.df.get(term, 0) + 1

    def _score(self, query_tokens: List[str], doc_id: int) -> float:
        """
        query and calculate BM25 score
        """
        score = 0.0
        doc_len = self.doc_lengths[doc_id]

        for term in query_tokens:
            if term not in self.df:
                continue

            idf = math.log((self.doc_count - self.df[term] + 0.5) /
                          (self.df[term] + 0.5) + 1.0)

            term_freq = self.tf[doc_id].get(term, 0)
            tf_part = term_freq * (self.k1 + 1) / \
                     (term_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length))

            score += idf * tf_part

        return score

    def search(self, query: str, top_k: int = 5) -> List[tuple]:
        """
        lauch search and return sorted result
        """
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query_tokens = self._tokenize(query)
        #print(query_tokens)
        scores = [(doc_id, self._score(query_tokens, doc_id))
                 for doc_id in range(self.doc_count)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def save(self, filepath: str):
        """
        save BM25 index as json or pickle
        
        Args:
            filepath: save Path
        Raises:
            ValueError: if file extension not support
        """
        lang_mapping = {
            EnglishBM25: 'english',
            ChineseBM25: 'chinese',
            MixedLanguageBM25: 'mixlanguage',
        }
        lang = lang_mapping.get(type(self), 'unknown')
        if lang == 'unknown':
            raise ValueError("Try loading from unknown language type")

        data = {
            'df': self.df,
            'tf': self.tf,
            'k1': self.k1,
            'b': self.b,
            #'language': 'english' if isinstance(self, EnglishBM25) else 'chinese',
            'language': lang,
            'stopwords': list(self.stopwords)
        }
        if filepath.endswith('.json'):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        elif filepath.endswith('.pkl'):
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
        else:
            raise ValueError("Unsupported file extension. Use .json or .pkl.")

    @classmethod
    def load(cls, filepath: str, corpus: List[str]):
        """
        load BM25 index from json or pickle
        
        Args:
            filepath: index file Path
            corpus: original doc set
        Returns:
            BM25 instance
        Raises:
            ValueError: if file extension or language not support
        """
        if filepath.endswith('.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif filepath.endswith('.pkl'):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
        else:
            raise ValueError("Unsupported file extension. Use .json or .pkl.")

        language = data['language']
        if language == 'english':
            bm25_cls = EnglishBM25
        elif language == 'chinese':
            bm25_cls = ChineseBM25
        elif language == 'mixlanguage':
            bm25_cls = MixedLanguageBM25
        else:
            raise ValueError("Unsupported language in saved data.")

        stopwords = tuple(data['stopwords'])
        bm25 = bm25_cls(corpus, data['k1'], data['b'], stopwords)
        bm25.df = data['df']
        bm25.tf = data['tf']
        bm25.doc_lengths = [sum(tf_doc.values()) for tf_doc in bm25.tf]
        bm25.avg_doc_length = sum(bm25.doc_lengths) / len(bm25.doc_lengths) if bm25.doc_lengths else 0
        return bm25
    
# EnglishBM25 implementation (with stemmer and stopwords)
class EnglishBM25(AbstractBM25):
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75, stopwords: tuple = STOPWORDS_EN_PLUS):
        """
        EnglishBM25 implementation
        """
        self.stemmer = Stemmer.Stemmer('english')  # init stemmer
        super().__init__(corpus, k1, b, stopwords)

    def _tokenize(self, text: str) -> List[str]:
        """English tokenize: preprocessing + PyStemmer + stopwords filter"""
        text = text.lower()
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
        tokens = text.split()
        return [self.stemmer.stemWord(token) for token in tokens if token and token not in self.stopwords]

# ChineseBM25 implementation (with jieba and stopwords)
class ChineseBM25(AbstractBM25):
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75, stopwords: tuple = STOPWORDS_CHINESE+STOPWORDS_ZH_TW):
        """
        ChineseBM25 implementation
        """
        super().__init__(corpus, k1, b, stopwords)

    def _tokenize(self, text: str) -> List[str]:
        """Chinese tokenize: jieba + stopwords filter"""
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', '', text)
        #tokens = jieba.cut(text)
        tokens = jieba.cut_for_search(text)
        return [token for token in tokens if token and token not in self.stopwords]
    
# MixedChineseBM25 implementation for slighty more compatative with english and chinese
class MixedChineseBM25(AbstractBM25):
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75, stopwords: tuple = STOPWORDS_EN_PLUS+STOPWORDS_CHINESE+STOPWORDS_ZH_TW):
        """
        MixedChineseBM25 implementation
        """
        self.stemmer = Stemmer.Stemmer('english')  # init stemmer
        super().__init__(corpus, k1, b, stopwords)

    def _tokenize(self, text: str) -> List[str]:
        """Mix tokenize: jieba + PyStemmer and stopwords filter"""
        # tokenize as chinese
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text) # preserve numbers and white space
        seg_list = jieba.cut_for_search(text)
        tokenized_text = [token for token in seg_list if not re.search(r'[\s]', token)]

        # english processing
        for i, token in enumerate(tokenized_text):
            tokenized_text[i] = tokenized_text[i].lower()
        #tokenized_text = [self.stemmer.stemWord(token) for token in tokenized_text if token and token not in self.stopwords]
        return [self.stemmer.stemWord(token) for token in tokenized_text if token and token not in self.stopwords]

# Mixure implementation
class MixedLanguageBM25(AbstractBM25):
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75, stopwords_en: tuple = STOPWORDS_EN_PLUS, stopwords_cn: tuple = STOPWORDS_CHINESE+STOPWORDS_ZH_TW):
        """
        Mixure implementation, detect language and use seperate tokenizer and stopwords
        """
        self.english_bm25 = EnglishBM25(corpus, k1, b, stopwords_en)
        self.mixedchinese_bm25 = MixedChineseBM25(corpus, k1, b, stopwords_en + stopwords_cn)
        super().__init__(corpus, k1, b, stopwords_en + stopwords_cn)

    def _tokenize(self, text: str) -> List[str]:
        """choose tokenizer base on detected language"""
        language = tokenizer_detect_language(text)
        if language == 'en':
            return self.english_bm25._tokenize(text)
        else:
            return self.mixedchinese_bm25._tokenize(text)


def create_bm25(corpus: List[str],
                language: str = 'mixed', 
                k1: float = 1.5,
                b: float = 0.75,
                stopwords: tuple = None):
    """
    function to create a BM25
    
    Args:
        corpus: doc set
        language: language type ('english' or 'chinese')
        k1: control term frequency saturation
        b: control doc length normalization
        stopwords: stopword filter
    """
    language = language.lower()
    if language in ['english', 'en']:
        stopwords = stopwords if stopwords is not None else STOPWORDS_EN_PLUS
        return EnglishBM25(corpus, k1, b, stopwords)
    elif language in ['chinese', 'cn']:
        stopwords = stopwords if stopwords is not None else STOPWORDS_CHINESE+STOPWORDS_ZH_TW
        return ChineseBM25(corpus, k1, b, stopwords)
    elif language in ['mixed']:
        stopwords_en = stopwords if stopwords is not None else STOPWORDS_EN_PLUS
        stopwords_cn = stopwords if stopwords is not None else STOPWORDS_CHINESE+STOPWORDS_ZH_TW
        return MixedLanguageBM25(corpus, k1, b, stopwords_en, stopwords_cn)
    else:
        raise ValueError("Unsupported language. Please choose 'english/en', 'chinese/cn', or 'mixed'.")
    
def load_bm25(filepath: str, corpus: List[str]):
    """
    load bm25 index
    
    Args:
        filepath: index file Path (json or pickle)
        corpus: original doc set
    Returns:
        BM25 instance
    """
    return AbstractBM25.load(filepath, corpus)

# general search function
def bm25_search(corpus: List[str], query: str, 
                language: str = 'mixed', top_k: int = 5,
                k1: float = 1.5, 
                b: float = 0.75, 
                stopwords: tuple = None) -> List[Tuple[int, float, str]]:
    """
    launch BM25 search
    """
    bm25 = create_bm25(corpus, language, k1, b, stopwords)
    results = bm25.search(query, top_k)
    return [(doc_id, score, corpus[doc_id]) for doc_id, score in results]
