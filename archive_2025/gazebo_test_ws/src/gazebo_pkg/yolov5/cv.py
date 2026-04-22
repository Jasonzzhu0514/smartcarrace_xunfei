import cv2

# 1. 读取图片（替换为你的图片路径）
image_path = "cola.jpg"  # 修改为实际路径
image = cv2.imread(image_path)

# 2. 检查图片是否加载成功
if image is None:
    print(f"错误：无法加载图片，请检查路径 -> {image_path}")
else:
    # 3. 显示图片信息
    height, width, channels = image.shape
    print(f"图片尺寸：宽度={width}px, 高度={height}px, 通道数={channels}")

    # 4. 显示图片窗口
    cv2.imshow("Image Viewer", image)
    print("按任意键关闭窗口...")
    
    # 5. 等待按键关闭窗口
    cv2.waitKey(0)
    cv2.destroyAllWindows()
