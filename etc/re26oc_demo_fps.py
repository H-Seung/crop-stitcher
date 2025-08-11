#!/usr/bin/env python
# coding=utf8

import cv2
import time
import subprocess
import os
import signal
from multiprocessing import Pool

from rectrl import *

def draw(dst, image, x, y, w, h):
    resized = cv2.resize(image, (w, h))
    dst[y:y + h, x:x + w] = resized

cap = [None, None, None, None, None, None]

bg = cv2.imread("/home/novitec/Desktop/demo/RobotEye.png")

cv2.namedWindow("demo", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("demo", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

print(bg)
cv2.imshow("demo", bg)
cv2.waitKey(1)

RECTRL_Open()
RECTRL_EnableMasterSyncMode(True, CAM0)
RECTRL_Close()

w = 1280
h = 720

cap[0] = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
cap[1] = cv2.VideoCapture("/dev/video1", cv2.CAP_V4L2)
cap[2] = cv2.VideoCapture("/dev/video2", cv2.CAP_V4L2)
cap[3] = cv2.VideoCapture("/dev/video3", cv2.CAP_V4L2)
cap[4] = cv2.VideoCapture("/dev/video4", cv2.CAP_V4L2)
cap[5] = cv2.VideoCapture("/dev/video5", cv2.CAP_V4L2)

img_num = 0
prev_time = time.time()

pool = Pool(6)

while True:
    start_time = time.time()

    ret0, frame0 = cap[0].read()
    ret1, frame1 = cap[1].read()
    ret2, frame2 = cap[2].read()
    ret3, frame3 = cap[3].read()
    ret4, frame4 = cap[4].read()
    ret5, frame5 = cap[5].read()

    bg_disp = bg.copy()  # 원본 유지

    draw(bg_disp, frame0, 0, 608, w, h)
    draw(bg_disp, frame1, w, 608, w, h)
    draw(bg_disp, frame2, w * 2, 608, w, h)
    draw(bg_disp, frame3, 0, 608 + h, w, h)
    draw(bg_disp, frame4, w, 608 + h, w, h)
    draw(bg_disp, frame5, w * 2, 608 + h, w, h)

    # FPS 계산 및 표시
    current_time = time.time()
    fps = 1.0 / (current_time - prev_time)
    prev_time = current_time
    fps_text = f"FPS: {fps:.2f}"
    cv2.putText(bg_disp, fps_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
                1.5, (0, 255, 0), 3, cv2.LINE_AA)

    cv2.imshow("demo", bg_disp)
    cv2.waitKey(1)

    print(img_num)
    img_num += 1
