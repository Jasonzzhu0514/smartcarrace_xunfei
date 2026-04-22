import torch
import cv2
import numpy as np

# 加载YOLOv5模型
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)  # 使用yolov5s模型
model.eval()

# 设置摄像头（或换成图片路径）
cap = cv2.VideoCapture(0)  # 0为默认摄像头；换成路径可处理视频或图片

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("读取帧失败")
        break

    # 推理
    results = model(frame)

    # 解析结果并渲染
    annotated_frame = np.squeeze(results.render())  # 将预测结果绘制在图像上

    # 显示图像
    cv2.imshow("YOLOv5 Detection", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
