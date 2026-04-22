import cv2
import numpy as np

import qrcode
import barcode
from pyzbar.pyzbar import decode

# 视频捕获，传入参数摄像头ID, 0：默认第一个摄像头
cap = cv2.VideoCapture(0)

# 判断摄像头是否正常打开
if cap.isOpened():
    print('Camera Opened.')
else:
    print('Camera Open error.')

# 处理流程
while True:
    ret, frame = cap.read()
    if ret == False:
        # 读取帧失败
        break
    
    # 图像处理
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 二维码条形码识别
    codes = decode(frame_gray)

    # 输出识别结果
    for barcode in codes:
        # print(barcode.type)
        # print(barcode.data)
        # print(barcode.quality)
        # print(barcode.orientation)
        # print(barcode.rect)
        # print(barcode.polygon)
        


        # 绘制矩形边框
        # x,y,w,h = barcode.rect
        # cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 1)
        rect = barcode.rect
        # cv2.rectangle(frame, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (0, 0, 255), 2)

        # 绘制多边形框
        pts = np.array(barcode.polygon, np.int32)
        cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

        # 绘制识别结果
        text = barcode.data.decode('utf-8')
        print(text)
        cv2.putText(frame, text, (rect.left, rect.top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
    
    k = cv2.waitKey(30)&0xFF
    if k == 27:
        break
    else:
        # cv2.imshow('gray', frame_gray)
        cv2.imshow('frame', frame)


cap.release()
cv2.destroyAllWindows()
