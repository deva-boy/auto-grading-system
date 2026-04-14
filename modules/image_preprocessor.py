import cv2
import numpy as np

class ImagePreprocessor:
    """试卷图像预处理模块"""

    def __init__(self, blur_kernel: tuple = (5, 5)):
        self.blur_kernel = blur_kernel

    def rotate_90_no_crop(self, image: np.ndarray) -> np.ndarray:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """对整张彩色图像进行二值化预处理（灰度+高斯模糊+自适应阈值+形态学闭运算）"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, self.blur_kernel, 0)
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            15, 10
        )
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        return cleaned

    def preprocess_from_file(self, file_path: str):
        """读取图片，旋转，返回旋转后的原图和二值化后的整图"""
        raw_data = np.fromfile(file_path, dtype=np.uint8)
        image = cv2.imdecode(raw_data, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"无法读取图片：{file_path}")
        rotated_img = self.rotate_90_no_crop(image)
        # processed_img = self.preprocess(rotated_img)
        return rotated_img

    def preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        """
        对单个答题区域（已正立的彩色图像）进行二值化预处理。
        参数 roi: 彩色 BGR 图像 (numpy array)
        返回: 二值化后的图像（前景白，背景黑）
        """
        # 如果输入已经是单通道灰度图，直接使用；否则转换
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
        gray = cv2.GaussianBlur(gray, self.blur_kernel, 0)
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            15, 10
        )
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        return cleaned

if __name__ == "__main__":
    from modules.yolo_detection import detect_and_extract_questions
    preprocessor = ImagePreprocessor()

    rois = detect_and_extract_questions(
        r"C:\Users\32601\.openclaw\workspace\.worktrees\auto-grading\auto-grading-system\data\raw\paper_1.png",
        expand_left=1500, expand_bottom=975)

    max_w, max_h = 800, 600
    for label, roi_color in rois:
        roi_binary = preprocessor.preprocess_roi(roi_color)
        h, w = roi_binary.shape[:2]
        # 计算缩放比例（保证窗口不超过 max_w x max_h，且不放大）
        scale = min(max_w / w, max_h / h, 1.0)
        new_w, new_h = int(w * scale), int(h * scale)
        # 创建可调整大小的窗口，并设置显示尺寸
        win_name = f"{label}_binary"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, new_w, new_h)
        cv2.imshow(win_name, roi_binary)
    cv2.waitKey(0)