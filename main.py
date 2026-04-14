from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
from modules.image_preprocessor import ImagePreprocessor
from modules.paper_segmenter import PaperSegmenter
from modules.ocr_engine import OCREngine
from modules.doc_parser import DocParser
from modules.json_doc_parser import JSONDocParser
from modules.grading_engine import GradingEngine
from modules.annotation_renderer import AnnotationRenderer
from modules.yolo_detection import detect_and_extract_questions
import config

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

app = FastAPI(
    title="自动批阅试卷系统",
    description="输入试卷图片，输出批阅结果",
    version="1.0.0"
)

# 初始化模块
preprocessor = ImagePreprocessor()
segmenter = PaperSegmenter()
ocr_engine = OCREngine(lang=config.OCR_LANG, use_gpu=config.OCR_USE_GPU)
doc_parser = DocParser()
grading_engine = GradingEngine(use_ai=True)
annotation_renderer = AnnotationRenderer()


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/grade")
async def grade_paper(
    paper_front: UploadFile = File(..., description="学生试卷正面图片"),
    paper_back: UploadFile = File(..., description="学生试卷反面图片"),
):
    """
    批阅双面试卷

    - **paper_front**: 学生试卷正面图片（一、二大题，55分）
    - **paper_back**: 学生试卷反面图片（三、四大题，45分）
    - **enable_ai**: 是否启用 AI 评分主观题

    使用内置的标准答案配置文件进行批阅

    返回批阅后的图片和分数详情
    """
    print(f"收到请求: 正面={paper_front.filename}, 反面={paper_back.filename}")

    # 验证文件类型
    for image in [paper_front, paper_back]:
        content_type = image.content_type or "image/jpeg"
        if not content_type.startswith("image/"):
            print(f"图片类型错误: {content_type}")
            raise HTTPException(400, "请上传图片文件")

    async def extract_text_and_image(file_obj, filename, temp_dir, preprocessor, ocr_engine):
        """保存临时文件、预处理、YOLO检测ROI、OCR提取文本，并返回ROI原始边界框"""
        temp_path = os.path.join(temp_dir, filename)
        with open(temp_path, "wb") as f:
            f.write(await file_obj.read())

        image = preprocessor.preprocess_from_file(temp_path)
        rois_with_bbox = detect_and_extract_questions(temp_path)

        text = ''
        for label, roi_color, bbox in rois_with_bbox:
            roi_binary = preprocessor.preprocess_roi(roi_color)
            result = ocr_engine.extract_text(roi_binary)
            text += "\n" + result['text']

        return image, text, temp_path, rois_with_bbox  # 多返回 rois_with_bbox

    # 保存临时文件
    temp_dir = tempfile.mkdtemp()
    try:
        # 处理正面
        front_image, front_text, front_temp,front_rois  = await extract_text_and_image(
            paper_front, f"front_{paper_front.filename}", temp_dir, preprocessor, ocr_engine
        )
        # 处理背面
        back_image, back_text, back_temp,back_rois = await extract_text_and_image(
            paper_back, f"back_{paper_back.filename}", temp_dir, preprocessor, ocr_engine
        )
        if not front_rois or not back_rois:
            missing_sides = []
            if not front_rois:
                missing_sides.append("正面")
            if not back_rois:
                missing_sides.append("反面")

            error_msg = f"未检测到答题区域：{'、'.join(missing_sides)}，请确保图片清晰且包含完整试卷"
            print(error_msg)

            # 返回 422 状态码（Unprocessable Content）让前端知道需要重试
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "ROI_NOT_DETECTED",
                    "message": error_msg,
                    "missing_sides": missing_sides,
                    "retry": True  # 告诉前端可以重试
                }
            )
        print("========== ocr识别文字完成 ============")

        json_parser = JSONDocParser('answer_config.json')
        standard_answers = json_parser.parse()
        big_questions = standard_answers.get("big_questions", [])

        print("========== AI评分系统开始执行 ============")

        front_grading, front_total = grading_engine.grade_side(big_questions[:2], front_text, start_big_index=1,
                                                grading_engine=grading_engine)

        back_grading, back_total = grading_engine.grade_side(big_questions[2:], back_text, start_big_index=3,
                                              grading_engine=grading_engine)
        print("========== AI评分系统正在合并评分结果 ============")

        grading_result = {**front_grading, **back_grading}

        print("========== 正在渲染分数 ============")
        front_titles = ["一、理解题", "二、分析题"]
        front_scores = [front_grading[f"big_1"]["score"], front_grading[f"big_2"]["score"]]

        front_result = annotation_renderer.render(
            front_image,
            grading_result,
            (50, 50),
            big_question_boxes=[(150,600,800,150)],
            big_question_titles=front_titles,
            big_question_scores=front_scores
        )
        back_titles = ["三设计编程题","四、应用题"]
        back_scores = [front_grading[f"big_1"]["score"], front_grading[f"big_2"]["score"]]
        back_result = annotation_renderer.render(
            back_image,
            grading_result,
            (50, 50),
            big_question_boxes=[(150,150,800,150)],
            big_question_titles=back_titles,
            big_question_scores=back_scores
        )
        print("========== 保存为一张PDF文件 ============")
        # 7. 合并为一张 PDF 文件（正面在前，背面在后）
        pdf_output_path = os.path.join(temp_dir, "result.pdf")
        from PIL import Image

        print("确保两个结果都是 PIL Image 对象")
        if not isinstance(front_result, Image.Image):
            front_result = Image.fromarray(front_result)  # 如果是 numpy 数组
        if not isinstance(back_result, Image.Image):
            back_result = Image.fromarray(back_result)

        print("保存多页 PDF")
        front_result.save(pdf_output_path, save_all=True, append_images=[back_result])

        # 读取 PDF 文件为 base64
        import base64
        with open(pdf_output_path, "rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

        return JSONResponse(
            content={
                "success": True,
                "total_score": front_total + back_total,
                "front_score": front_total,
                "back_score": back_total,
                "front_max_score": 55,
                "back_max_score": 45,
                "scores": grading_result,
                "result_image": pdf_base64,
                "message": "双面试卷批阅完成"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"处理错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"批阅失败：{str(e)}")
    finally:
        print("清理临时文件")
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)