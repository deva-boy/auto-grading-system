"""
自动批阅试卷系统核心模块
"""

from .image_preprocessor import ImagePreprocessor
from .paper_segmenter import PaperSegmenter
from .ocr_engine import OCREngine
from .doc_parser import DocParser
from .grading_engine import GradingEngine
from .annotation_renderer import AnnotationRenderer

__all__ = [
    "ImagePreprocessor",
    "PaperSegmenter",
    "OCREngine",
    "DocParser",
    "GradingEngine",
    "AnnotationRenderer",
]
