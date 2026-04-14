import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)


# 服务配置
HOST = os.getenv("GRADING_HOST", "127.0.0.1")
PORT = int(os.getenv("GRADING_PORT", "8000"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT", "5"))

# OCR 配置
OCR_LANG = "ch"
OCR_USE_GPU = os.getenv("OCR_USE_GPU", "False").lower() == "true"

# 批注样式
ANNOTATION_COLOR = (0, 0, 255)  # 红色 RGB
SUB_QUESTION_FONT_SIZE = 16
BIG_QUESTION_FONT_SIZE = 20
FONT_PATH = os.getenv("FONT_PATH", "C:/Windows/Fonts/simsun.ttc")  # 宋体

# 临时文件目录
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")