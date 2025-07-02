from typing import List, Dict
import re


def detect_language(text: str) -> str:
    """
    detect doc main language

    Args:
        text (str): input doc

    Return:
        str: 'zh' if there's more chinese, 'en' if there's more english
    """
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # count english words
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))

    # if chinese > english, process as chinese
    return 'zh' if chinese_chars > english_words * 2 else 'en'

def tokenizer_detect_language(text: str) -> str:
    """
    jieba could compatable with english tokenizing(blankspace)
    so this funcion only detects if there's chinese in doc

    Args:
        text (str): input text

    Returns:
        str: 'zh' if there's chinese, 'en' if there's no chinese char
    """
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

    # if contain chinese, process as chinese
    return 'zh' if chinese_chars > 0 else 'en'
