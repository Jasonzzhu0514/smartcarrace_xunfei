#!/bin/bash

DEVICE="/dev/video0"

echo "正在检测占用摄像头 ($DEVICE) 的进程..."

PIDS=$(fuser $DEVICE 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "摄像头未被占用。"
else
    echo "以下进程正在占用 $DEVICE：$PIDS"
    for pid in $PIDS; do
        PROC_NAME=$(ps -p $pid -o comm=)
        echo "正在终止进程 $pid ($PROC_NAME)..."
        sudo kill -9 $pid
    done
    echo "已释放摄像头资源。"
fi


echo "正在重载 uvcvideo 驱动..."
sudo modprobe -r uvcvideo
sudo modprobe uvcvideo
echo "驱动已重载。"
