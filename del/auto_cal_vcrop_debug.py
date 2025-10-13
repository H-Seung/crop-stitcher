def _auto_calculate_vertical_crop(self) -> Tuple[int, int]:
    """
    (config 값 없을 시) 상하 자동 계산 크롭 (샘플 프레임 임시로 하나 캡쳐해 crop 기준 잡음)
    회전 및 정렬 보정이 적용된 각 카메라 프레임들을 처리한 후,
    모든 프레임에서 유효한 최소 영역을 찾아 크롭 범위를 계산
    """
    processed_frames = []

    # 각 카메라별로 샘플 프레임을 캡처하고 실제 전처리 과정을 거침
    for camera_id, dev in enumerate(self.config['camera']['device_paths']):
        cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        ret, frame = cap.read()
        h, w = frame.shape[:2]
        self.logger.info(f"camera_id={camera_id}, h={h}, w={w}")
        cap.release()

        if ret:
            # 실제 전처리 과정 적용 (회전, 오프셋)
            processed_frame = TransformationUtils.apply_cpu_transformations(
                frame, h, w, self.config, camera_id
            )
            if processed_frame is not None:
                processed_frames.append(processed_frame)
            else:
                self.logger.warning(f"카메라 {camera_id} 프레임 처리 실패")
        else:
            self.logger.warning(f"샘플 캡처 실패: {dev}")

    if not processed_frames:
        raise RuntimeError("카메라에서 처리된 프레임을 얻지 못해 크롭 계산 불가")

    # 모든 처리된 프레임에서 유효한(검은색이 아닌) 영역 찾기
    valid_regions = []
    for frame in processed_frames:
        # 그레이스케일로 변환하여 유효 영역 찾기
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 0이 아닌 픽셀들의 위치 찾기
        non_zero_rows = np.where(np.any(gray > 0, axis=1))[0]  # y축으로 내려가면서 하나라도 black이 아닌 행 번호들
        if len(non_zero_rows) > 0:
            valid_top = non_zero_rows[0]
            valid_bottom = non_zero_rows[-1] + 1
            valid_regions.append((valid_top, valid_bottom))

    if not valid_regions:
        # 유효 영역을 찾지 못한 경우 전체 영역 사용
        self.logger.warning("유효 영역을 찾지 못함, 전체 영역 사용")
        return 0, self.resolution[1]

    # 모든 프레임에서 공통으로 유효한 영역 계산
    max_top = max(region[0] for region in valid_regions)
    min_bottom = min(region[1] for region in valid_regions)

    # 안전 마진 추가 (전체 높이의 2%)
    margin = int(self.resolution[1] * 0.02)
    crop_top = max(0, max_top + margin)
    crop_bottom = min(self.resolution[1], min_bottom - margin)

    self.logger.info(f"자동 크롭 범위 (처리된 프레임 기준): top={crop_top}, bottom={crop_bottom}")
    return crop_top, crop_bottom

