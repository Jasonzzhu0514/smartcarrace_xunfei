import websocket
import json
from threading import Thread
import rospy
import time

target = None

def on_message(ws, message):
    global target
    data = json.loads(message)
    if "msg" in data:
        qr_data = data['msg']
        target = qr_data["data"]
        # print(qr_data["data"])

def on_error(ws, error):
    print(f"[WebSocket Error]: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    subscribe_message = {
        "op": "subscribe",
        "topic": "/qrcode_result"  # 修改为实际需要订阅的ROS话题（例如/imu）
    }
    ws.send(json.dumps(subscribe_message))
    print("Subscribed to /qrcode_result")

def start_websocket():
    # websocket.enableTrace(True)  # 启用调试日志（可选）
    ws_url = "ws://192.168.31.177:9090"

    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

if __name__ == "__main__":
    print("ws_thread init")
    ws_thread = Thread(target=start_websocket)
    ws_thread.start()
    print("main init")

    while not rospy.is_shutdown() and target is None: #等待仿真结果
        print("waiting...")
        time.sleep(0.1)
        print(target)

    print("result={}".format(target))

