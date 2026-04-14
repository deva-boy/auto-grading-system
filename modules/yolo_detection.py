from ultralytics import YOLO
import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "../train_yolov8n/weights/best.pt")
model = YOLO(model_path)

def detect_and_extract_questions(image_path,
                                 expand_left=1500, expand_right=0,
                                 expand_top=0, expand_bottom=975,
                                 conf_threshold=0.6,
                                 max_boxes=2,
                                 sort_by_area=True) -> list:
    """
    检测大题区域并提取，支持过滤多余检测框。
    返回：list of (label, roi_corrected, (x1, y1, x2, y2))
        其中 (x1,y1,x2,y2) 是原图中未扩展的检测框坐标（整数）。
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"无法读取图像: {image_path}")

    h, w = img.shape[:2]
    results = model(img)
    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        print("未检测到大题框")
        return []

    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()

    valid = confs >= conf_threshold
    xyxy = xyxy[valid]
    confs = confs[valid]

    if len(xyxy) == 0:
        print("没有高于置信度阈值的检测框")
        return []

    areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])

    if sort_by_area:
        idx_sorted = areas.argsort()[::-1][:max_boxes]
        xyxy = xyxy[idx_sorted]
    else:
        xyxy = xyxy[:max_boxes]

    # 按 y1 排序（从上到下）
    xyxy = xyxy[xyxy[:, 1].argsort()]

    question_rois = []
    for i, (x1, y1, x2, y2) in enumerate(xyxy):
        # 原始框（未经扩展）
        orig_box = (int(x1), int(y1), int(x2), int(y2))
        # 扩展并裁剪
        x1_exp = max(0, int(x1) - expand_left)
        y1_exp = max(0, int(y1) - expand_top)
        x2_exp = min(w, int(x2) + expand_right)
        y2_exp = min(h, int(y2) + expand_bottom)
        roi = img[y1_exp:y2_exp, x1_exp:x2_exp]
        roi_corrected = cv2.rotate(roi, cv2.ROTATE_90_COUNTERCLOCKWISE)
        question_rois.append((f"Q{i+1}", roi_corrected, orig_box))

    if len(question_rois) < max_boxes:
        print(f"警告：只检测到 {len(question_rois)} 个大题，预期 {max_boxes} 个。")

    return question_rois

if __name__ == "__main__":
    rois = detect_and_extract_questions(
        r"C:\Users\32601\.openclaw\workspace\.worktrees\auto-grading\auto-grading-system\data\raw\paper_2.png",
        expand_left=1500, expand_bottom=975,
        conf_threshold=0.6, max_boxes=2, sort_by_area=True
    )
    for name, roi_img in rois:
        cv2.namedWindow(name, cv2.WINDOW_NORMAL)
        h, w = roi_img.shape[:2]
        max_width, max_height = 800, 600
        scale = min(max_width / w, max_height / h, 1.0)
        new_w, new_h = int(w * scale), int(h * scale)
        cv2.resizeWindow(name, new_w, new_h)
        cv2.imshow(name, roi_img)
    cv2.waitKey(0)