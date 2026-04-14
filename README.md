# 自动批阅试卷系统

纯后端自动批阅试卷系统，输入学生试卷图片和标准答案 DOC 文件，输出带有红色批注和分数的批阅结果图片。

## 功能特性

- ✅ 图像预处理（灰度化 + 二值化 + 去噪）
- ✅ 试卷结构识别（大题/小题分割）
- ✅ PaddleOCR 文字识别
- ✅ DOCX 标准答案解析
- ✅ 文心一言 AI 智能评分
- ✅ 红色批注叠加输出

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# Windows
copy .env.example .env

# 编辑 .env 填入文心一言 API Key
# QIANFAN_API_KEY=your_api_key_here
# QIANFAN_SECRET_KEY=your_secret_key_here
```

### 3. 生成示例文件（可选）

```bash
python generate_samples.py
```

### 4. 启动服务

**Windows:**
```bash
start.bat
```

**手动启动:**
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 5. 访问 API 文档

浏览器打开：http://127.0.0.1:8000/docs

## API 使用

### 批阅试卷

```bash
# cURL
curl -X POST http://127.0.0.1:8000/api/grade ^
  -F "paper_image=@samples/sample_paper.jpg" ^
  -F "answer_doc=@samples/sample_answer.docx" ^
  -o result.json

# PowerShell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/grade" `
  -Method Post `
  -InFile "samples/sample_paper.jpg" `
  -Form @{ paper_image = Get-Item "samples/sample_paper.jpg"; answer_doc = Get-Item "samples/sample_answer.docx" }
$response | ConvertTo-Json
```

### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

## 运行测试

```bash
# Windows
run_tests.bat

# 手动运行
pytest tests/ -v
```

## 项目结构

```
auto-grading-system/
├── main.py                 # FastAPI 入口
├── config.py               # 配置管理
├── requirements.txt        # 依赖列表
├── start.bat              # Windows 启动脚本
├── run_tests.bat          # Windows 测试脚本
├── generate_samples.py    # 示例文件生成器
├── modules/
│   ├── __init__.py
│   ├── image_preprocessor.py    # 图像预处理
│   ├── paper_segmenter.py       # 试卷分割
│   ├── ocr_engine.py            # OCR 识别
│   ├── doc_parser.py            # DOC 解析
│   ├── grading_engine.py        # 评分引擎
│   └── annotation_renderer.py   # 批注渲染
├── tests/                 # 测试用例
├── samples/               # 示例文件
│   ├── sample_paper.jpg
│   ├── sample_answer.docx
│   └── README.md
└── docs/
    └── api.md             # API 文档
```

## 技术栈

- **Web 框架**: FastAPI
- **图像处理**: OpenCV
- **OCR**: PaddleOCR
- **DOC 解析**: python-docx
- **图片渲染**: Pillow
- **AI 评分**: 文心一言 (qianfan SDK)

## 注意事项

1. 首次使用需配置文心一言 API Key
2. 图片建议分辨率不低于 1000x1000
3. DOC 文件必须是 .docx 格式
4. 单张试卷处理时间约 10-30 秒

## 许可证

MIT License

## 功能特性

- ✅ 图像预处理（灰度化 + 二值化）
- ✅ 试卷结构识别（大题/小题）
- ✅ PaddleOCR 文字提取
- ✅ 标准答案 DOCX 解析
- ✅ 文心一言 AI 评分
- ✅ 红色批注叠加

## 系统要求

- Python 3.8+
- Windows/Linux/Mac
- 文心一言 API Key
