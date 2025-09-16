import os
import cv2
import numpy as np
import yaml
import time
from typing import Optional


# 초기 config 파일 불러오기
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
display_width = config['display']['resolution']['width']
display_height = config['display']['resolution']['height']


def make_edge_lines(frame: np.ndarray) -> np.ndarray:
    edges = cv2.Canny(frame, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180,  # shape: (N, 1, 4), N개 직선
                            150,  # 직선 후보로 인정되기 위한 최소 누적값
                            minLineLength=120,  # 해당 px 이상이어야 직선으로 인정
                            maxLineGap=30)  # 선 간격이 해당 px 이하일 경우 같은 선으로 간주
    return lines

def preprocess_for_edge_lines(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_eq = cv2.equalizeHist(gray)
    gray_bright = cv2.add(gray_eq, 80)
    blurred = cv2.GaussianBlur(gray_bright, (5, 5), 0)
    return blurred

def roi(frame, width_ratio, height_ratio):
    h, w = frame.shape
    roi_w = int(w * width_ratio)
    roi_h = int(h * height_ratio)
    roi_x_start = (w - roi_w) // 2
    roi_y_start = (h - roi_h) // 2
    roi_frame = frame[roi_y_start:roi_y_start + roi_h, roi_x_start:roi_x_start + roi_w]
    print("w, h : ", w, h, "| roi_w, roi_h : ", roi_w, roi_h, "| roi_x_start, roi_y_start : ", roi_x_start, roi_y_start)
    return roi_frame, roi_x_start, roi_y_start

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
    cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(winname, int(display_width*0.8), int(display_height*0.8))
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
                print(f"(select_horizontal_line) 선택된 선: {selected_line}")

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

def compute_angle_from_line(line, roi_y_start: int, roi_x_start: int):
    """
    단일 수평선으로부터 회전각과 수직 오프셋 계산
    line: ROI 기준 좌표 -> 원본 기준으로 보정 필요
    ref_y: 원본 프레임의 수직 기준선
    roi_y_start: ROI의 시작 y값 (원본 프레임 기준)
    """
    x1, y1, x2, y2 = line
    # ROI 좌표를 원본 기준으로 환산
    x1_full, y1_full = x1 + roi_x_start, y1 + roi_y_start
    x2_full, y2_full = x2 + roi_x_start, y2 + roi_y_start
    print("(compute_angle_from_line) --> x1, y1, x2, y2 | x1_full, y1_full, x2_full, y2_full : ", x1, y1, x2, y2, " | ", x1_full, y1_full, x2_full, y2_full)

    angle = np.degrees(np.arctan2(y2_full - y1_full, x2_full - x1_full)) # 우상향(반시계): -, 우하향 : + (좌상단이 원점)
    return angle

def compute_offset_from_line(line, ref_y, roi_y_start: int, roi_x_start: int):
    x1, y1, x2, y2 = line
    # ROI 좌표를 원본 기준으로 환산
    x1_full, y1_full = x1 + roi_x_start, y1 + roi_y_start
    x2_full, y2_full = x2 + roi_x_start, y2 + roi_y_start
    print("(compute_offset_from_line) --> x1, y1, x2, y2 | x1_full, y1_full, x2_full, y2_full : ", x1, y1, x2, y2, " | ", x1_full, y1_full, x2_full, y2_full)

    y_avg = int((y1_full + y2_full) / 2)
    offset = ref_y - y_avg
    return offset


def calibrate_all_cameras(config_path='config.yaml', no_config_write=0):
    os.makedirs("debug_images", exist_ok=True)

    # resolution 초기화
    if config['camera'].get('resolution', None) is not None:
        resolution = (config['camera']['resolution']['height'],
                      config['camera']['resolution']['width'])
    else:
        resolution = None

    updated_rotation = {}
    updated_offset = {}
    visual_rows = []
    resolution_updated = False

    for i, dev in enumerate(config['camera']['device_paths']):
        print(f"=================== cam{i} 시작 ===================")
        cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
        if resolution is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print(f"[WARN] 프레임 캡처 실패: {dev}")
            continue

        # resolution 최초 한번 config에 업데이트
        if not resolution_updated:
            actual_resolution = frame.shape[:2]
            if resolution is None:
                resolution = actual_resolution
                if 'resolution' not in config['camera']:
                    config['camera']['resolution'] = {}
                config['camera']['resolution']['height'] = resolution[0]
                config['camera']['resolution']['width'] = resolution[1]
                print("resolution: ", resolution)
            else:
                if resolution != actual_resolution:
                    print(f"[INFO] 설정된 해상도 {resolution}와 실제 해상도 {actual_resolution}가 다릅니다. 실제 해상도로 업데이트합니다.")
                    resolution = (config['camera']['resolution']['height'],
                                  config['camera']['resolution']['width'])

            ref_y = resolution[0] // 2
            resolution_updated = True

        blurred = preprocess_for_edge_lines(frame)
        roi_frame, roi_x_start, roi_y_start = roi(blurred, 1, 0.7)  # 관심영역 설정
        lines = make_edge_lines(roi_frame)
        roi_color = cv2.cvtColor(roi_frame, cv2.COLOR_GRAY2BGR)

        # 회전 보정
        selected_line = select_horizontal_line(roi_color, lines, cam_id=i)
        if selected_line is None:
            print(f"[WARN] 사용자 입력 없음: angle 기본값 사용")
            angle = 0.0
        else:
            angle = compute_angle_from_line(selected_line, roi_y_start, roi_x_start)
            print("=> angle : ", angle)
        M = cv2.getRotationMatrix2D((frame.shape[1] // 2, frame.shape[0] // 2), angle, 1.0)  # 반시계 방향 : +
        print(": M : ", M)
        rotated = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))

        # 회전된 frame 에서 다시 위 전처리
        blurred = preprocess_for_edge_lines(rotated)
        roi_frame, roi_x_start, roi_y_start = roi(blurred, 1, 0.7)  # 관심영역 설정
        lines = make_edge_lines(roi_frame)
        roi_color = cv2.cvtColor(roi_frame, cv2.COLOR_GRAY2BGR)

        # 수직 보정
        selected_line = select_horizontal_line(roi_color, lines, cam_id=i)
        if selected_line is None:
            print(f"[WARN] 사용자 입력 없음: offset 기본값 사용")
            offset = 0
        else:
            offset = compute_offset_from_line(selected_line, ref_y, roi_y_start, roi_x_start)
            print("=> offset : ", offset)
        M = np.float32([[1, 0, 0], [0, 1, offset]])
        y_shift = cv2.warpAffine(rotated, M, (rotated.shape[1], rotated.shape[0]))

        x1, y1, x2, y2 = selected_line
        y_avg = int((y1 + y2) / 2)

        frame_vis = frame.copy()
        y_shift_vis = y_shift.copy()
        cv2.line(frame_vis, (0, ref_y), (frame.shape[1], ref_y), (0, 255, 0), 1)
        cv2.line(frame_vis, (0, y_avg), (frame.shape[1], y_avg), (0, 0, 255), 1)
        cv2.circle(frame_vis, (x1,y1), 5, (255, 255, 0), -1)
        cv2.circle(frame_vis, (x2,y2), 5, (255, 0, 0), -1)
        cv2.line(y_shift_vis, (0, ref_y), (frame.shape[1], ref_y), (0, 255, 0), 1)
        cv2.line(y_shift_vis, (0, y_avg), (frame.shape[1], y_avg), (0, 0, 255), 1)

        text = f"Current Camera {i} | Rotation: {angle:.2f}deg | Offset: {offset}px"
        cv2.putText(frame_vis, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame_vis, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        visual_rows.append(np.hstack([frame_vis, y_shift_vis]))

        print(f"[cam{i}] 회전: {angle:.2f}, 수직 offset: {offset}")
        print("==================================================")

        updated_rotation[f"cam{i}"] = float(round(angle, 2)) # 회전 보정값
        updated_offset[f"cam{i}"] = int(-offset) # 수직 이동 보정값

    if visual_rows:
        full_vis = np.vstack(visual_rows)
        filename = f"debug_images/calibration_result_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, full_vis)
        print(f"[INFO] 캘리브레이션 시각화 결과 저장: {filename}")

    config['calibration']['rotation_correction'] = updated_rotation
    config['calibration']['vertical_offset'] = updated_offset

    if no_config_write == 0:
        base, ext = os.path.splitext(config_path)  # 확장자 분리
        filename = f"{base}_{time.strftime('%Y%m%d_%H%M%S')}{ext}"
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        print(f"[INFO] {filename}으로 보정값 업데이트 완료")


def debug_with_img(cam_cnt=6):
    os.makedirs("debug_images", exist_ok=True)
    resolution = None
    visual_rows = []
    img_path = ["test_images/horizon_-3.jpg",
                "test_images/horizon_-3.jpg",
                "test_images/horizon_0.jpg",
                "test_images/horizon_0.jpg",
                "test_images/horizon_5.jpg",
                "test_images/horizon_5.jpg",
                ]
    # img_path = ["test_images/P1000166.jpg",
    #             "test_images/P1000167.jpg",
    #             "test_images/P1000168.jpg",
    #             "test_images/P1000169.jpg",
    #             "test_images/P1000170.jpg",
    #             "test_images/P1000172.jpg",
    #             ]

    if len(img_path) != cam_cnt:
        print("img_path 와 cam_cnt 불일치")

    for i, p in enumerate(img_path):
        print(f"=================== cam{i} 시작 ===================")
        frame = cv2.imread(p)
        if resolution is None: # 최초 한번 실행
            resolution = frame.shape[:2]
            print("resolution: ", resolution)
            ref_y = resolution[0] // 2

        blurred = preprocess_for_edge_lines(frame)
        roi_frame, roi_x_start, roi_y_start = roi(blurred, 1, 0.7) # 관심영역 설정
        lines = make_edge_lines(roi_frame)
        roi_color = cv2.cvtColor(roi_frame, cv2.COLOR_GRAY2BGR)

        # 회전 보정
        selected_line = select_horizontal_line(roi_color, lines, cam_id=i)
        if selected_line is None:
            print(f"[WARN] 사용자 입력 없음: angle 기본값 사용")
            angle = 0.0
        else:
            angle = compute_angle_from_line(selected_line, roi_y_start, roi_x_start)
            print("=> angle : ", angle)
        M = cv2.getRotationMatrix2D((frame.shape[1] // 2, frame.shape[0] // 2), angle, 1.0) # 반시계 방향 : +
        print(": M : ", M)
        rotated = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))

        # 회전된 frame 에서 다시 위 전처리
        blurred = preprocess_for_edge_lines(rotated)
        roi_frame, roi_x_start, roi_y_start = roi(blurred, 1, 0.7) # 관심영역 설정
        lines = make_edge_lines(roi_frame)
        roi_color = cv2.cvtColor(roi_frame, cv2.COLOR_GRAY2BGR)

        # 수직 보정
        selected_line = select_horizontal_line(roi_color, lines, cam_id=i)
        if selected_line is None:
            print(f"[WARN] 사용자 입력 없음: offset 기본값 사용")
            offset = 0
        else:
            offset = compute_offset_from_line(selected_line, ref_y, roi_y_start, roi_x_start)
            print("=> offset : ", offset)
        M = np.float32([[1, 0, 0], [0, 1, offset]])
        y_shift = cv2.warpAffine(rotated, M, (rotated.shape[1], rotated.shape[0]))

        x1, y1, x2, y2 = selected_line
        y_avg = int((y1 + y2) / 2)

        frame_vis = frame.copy()
        y_shift_vis = y_shift.copy()
        cv2.line(frame_vis, (0, ref_y), (frame.shape[1], ref_y), (0, 255, 0), 1)
        cv2.line(frame_vis, (0, y_avg), (frame.shape[1], y_avg), (0, 0, 255), 1)
        cv2.circle(frame_vis, (x1,y1), 5, (255, 255, 0), -1)
        cv2.circle(frame_vis, (x2,y2), 5, (255, 0, 0), -1)
        cv2.line(y_shift_vis, (0, ref_y), (frame.shape[1], ref_y), (0, 255, 0), 1)
        cv2.line(y_shift_vis, (0, y_avg), (frame.shape[1], y_avg), (0, 0, 255), 1)

        text = f"Current Camera {i} | Rotation: {angle:.2f}deg | Offset: {offset}px"
        cv2.putText(frame_vis, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame_vis, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        visual_rows.append(np.hstack([frame_vis, y_shift_vis]))

        print(f"[cam{i}] 회전: {angle:.2f}, 수직 offset: {offset}")
        print("==================================================")

    if visual_rows:
        full_vis = np.vstack(visual_rows)
        winname = "frame vs. rotated"
        cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(winname, int(display_width * 0.8), int(display_height * 0.8))
        cv2.imshow(winname, full_vis)
        print("")
        cv2.waitKey(0)
        cv2.destroyWindow(winname)
        filename = f"debug_images/calibration_debug_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, full_vis)
        print(f"[INFO] 캘리브레이션 debug 시각화 결과 저장: {filename}")


if __name__ == '__main__':
    test = 1
    if test == 0:
        calibrate_all_cameras()
    elif test == 1:
        debug_with_img(cam_cnt=6)
    elif test == 2:
        calibrate_all_cameras(no_config_write=1)


