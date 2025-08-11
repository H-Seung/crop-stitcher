#!/usr/bin/env python
# coding=utf8

import cv2

# 카메라 장치 번호
CAM_LEFT = 5
CAM_RIGHT = 0

# 해상도 설정
frame_width = 1280
frame_height = 720

# 두 영상을 나란히 배치할 캔버스 생성 (좌우 합쳐서)
canvas_width = frame_width * 2
canvas_height = frame_height

# 캡처 장치 초기화
cap_left = cv2.VideoCapture(f"/dev/video{CAM_LEFT}", cv2.CAP_V4L2)
cap_right = cv2.VideoCapture(f"/dev/video{CAM_RIGHT}", cv2.CAP_V4L2)

# 창 설정
cv2.namedWindow("Camera View", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera View", canvas_width // 2, canvas_height // 2)

frame_count = 0

while True:
    ret_left, frame_left = cap_left.read()
    ret_right, frame_right = cap_right.read()

    if not (ret_left and ret_right):
        print("카메라 프레임 수신 실패")
        continue

    # 리사이즈 (필요시), 그리고 좌우 합치기
    frame_left = cv2.resize(frame_left, (frame_width, frame_height))
    frame_right = cv2.resize(frame_right, (frame_width, frame_height))

    # 겹치는 픽셀 수
    overlap = 200

    # 프레임 크롭
    frame_left = frame_left[:, :frame_width - overlap]
    frame_right = frame_right[:, overlap:]

    combined = cv2.hconcat([frame_left, frame_right])

    cv2.imshow("Camera View", combined)

    key = cv2.waitKey(1)
    if key == 27:  # ESC 키로 종료
        break

    print(f"Frame {frame_count}")
    frame_count += 1

# 자원 해제
cap_left.release()
cap_right.release()
cv2.destroyAllWindows()
