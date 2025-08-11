import os
import cv2
import numpy as np
import yaml
import time
from typing import Optional

def point_line_distance(x1, y1, x2, y2, px, py):
    """점 (px, py)와 선분 (x1, y1)-(x2, y2) 사이의 최소 거리 계산"""
    line_vec = np.array([x2 - x1, y2 - y1])
    p_vec = np.array([px - x1, py - y1])
    line_len_sq = line_vec.dot(line_vec)
    if line_len_sq == 0:
        return np.linalg.norm(p_vec)
    t = max(0, min(1, p_vec.dot(line_vec) / line_len_sq))
    proj = np.array([x1, y1]) + t * line_vec
    return np.linalg.norm(proj - np.array([px, py]))

def select_horizontal_line(frame: np.ndarray, lines, cam_id: int):
    """
    수평선 후보 중 클릭한 위치에 가장 가까운 수평선 1개를 선택하도록 사용자 입력을 받음
    """
    debug_frame = frame.copy()
    horizontal_lines = []
    for x1, y1, x2, y2 in lines[:, 0]:
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) < 10:
            horizontal_lines.append((x1, y1, x2, y2))
            cv2.line(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    selected_line = None
    winname = f"cam{cam_id}_select"
    cv2.imshow(winname, debug_frame)

    def on_mouse(event, x, y, flags, param):
        nonlocal selected_line
        if event == cv2.EVENT_LBUTTONDOWN:
            click_x, click_y = x, y
            min_dist = float('inf')
            selected = None
            for x1, y1, x2, y2 in horizontal_lines:
                dist = point_line_distance(x1, y1, x2, y2, click_x, click_y)
                if dist < min_dist:
                    min_dist = dist
                    selected = (x1, y1, x2, y2)
            if selected:
                selected_line = selected
                print(f"[INFO] 선택된 선: {selected_line}")

                highlight_frame = debug_frame.copy()
                cv2.line(highlight_frame, (selected[0], selected[1]), (selected[2], selected[3]), (0, 0, 255), 3)
                cv2.putText(highlight_frame, "Selected line", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(highlight_frame, "Selected line", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.imshow(winname, highlight_frame)

    cv2.setMouseCallback(winname, on_mouse)
    print("[INFO] 수평선을 선택하세요. 클릭 후 Enter 키를 누르세요.")
    cv2.waitKey(0)
    cv2.destroyWindow(winname)
    return selected_line

def compute_angle_and_offset_from_line(line, ref_y, roi_y_start: int, roi_x_start: int):
    """
    단일 수평선으로부터 회전각과 수직 오프셋 계산
    line: ROI 기준 좌표 -> 원본 기준으로 보정 필요
    ref_y: 원본 프레임의 수직 기준선
    roi_y_start: ROI의 시작 y값 (원본 프레임 기준)
    """
    x1, y1, x2, y2 = line
    # ROI 좌표를 원본 기준으로 환산
    x1_full = x1 + roi_x_start
    x2_full = x2 + roi_x_start
    y1_full = y1 + roi_y_start
    y2_full = y2 + roi_y_start

    # 회전각 및 수직 offset 계산
    angle = np.degrees(np.arctan2(y2_full - y1_full, x2_full - x1_full))
    y_avg = int((y1_full + y2_full) / 2)
    offset = ref_y - y_avg
    return -angle, offset

def calibrate_all_cameras(config_path='config.yaml'):
    os.makedirs("debug_images", exist_ok=True)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    resolution = (config['camera']['resolution']['width'],
                  config['camera']['resolution']['height'])
    ref_y = resolution[1] // 2
    updated_rotation = {}
    updated_offset = {}
    visual_rows = []

    for i, dev in enumerate(config['camera']['device_paths']):
        cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print(f"[WARN] 프레임 캡처 실패: {dev}")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_eq = cv2.equalizeHist(gray)
        blurred = cv2.GaussianBlur(gray_eq, (5, 5), 0)

        h, w = blurred.shape
        roi_h = 240
        roi_w = w * 2 // 3  # 중앙 2/3 영역
        roi_y_start = h // 2 - 50  #
        roi_x_start = (w - roi_w) // 2
        roi = blurred[roi_y_start:roi_y_start+roi_h, roi_x_start:roi_x_start + roi_w]

        edges = cv2.Canny(roi, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180,  # shape: (N, 1, 4), N개 직선
                                150, # 직선 후보로 인정되기 위한 최소 누적값
                                minLineLength=150,  # 해당 px 이상이어야 직선으로 인정
                                maxLineGap=30)  # 선 간격이 해당 px 이하일 경우 같은 선으로 간주

        roi_color = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
        roi_color = cv2.add(roi_color, 100)

        selected_line = select_horizontal_line(roi_color, lines, cam_id=i)
        if selected_line is None:
            print(f"[WARN] 사용자 입력 없음: 기본값 사용 (cam{i})")
            angle, offset = 0.0, 0
        else:
            angle, offset = compute_angle_and_offset_from_line(selected_line, ref_y, roi_y_start, roi_x_start)

        M = cv2.getRotationMatrix2D((frame.shape[1] // 2, frame.shape[0] // 2), -angle, 1.0)
        rotated = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))

        frame_vis = frame.copy()
        rotated_vis = rotated.copy()
        cv2.line(frame_vis, (0, ref_y), (frame.shape[1], ref_y), (0, 0, 255), 2)
        cv2.line(rotated_vis, (0, ref_y), (frame.shape[1], ref_y), (0, 255, 0), 2)

        text = f"Camera {i} | Rotation: {angle:.2f}deg | Offset: {offset}px"
        for img in [frame_vis, rotated_vis]:
            cv2.putText(img, text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(img, text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        visual_rows.append(np.hstack([frame_vis, rotated_vis]))

        print(f"[cam{i}] 회전: {angle:.2f}, 수직 offset: {offset}")
        updated_rotation[f"cam{i}"] = float(round(-angle, 2)) # 회전 보정값
        updated_offset[f"cam{i}"] = int(-offset) # 수직 이동 보정값

    if visual_rows:
        full_vis = np.vstack(visual_rows)
        filename = f"debug_images/calibration_result_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, full_vis)
        print(f"[INFO] 캘리브레이션 시각화 결과 저장: {filename}")

    config['calibration']['rotation_correction'] = updated_rotation
    config['calibration']['vertical_offset'] = updated_offset

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    print("[INFO] config.yaml 보정값 업데이트 완료")

if __name__ == '__main__':
    calibrate_all_cameras()