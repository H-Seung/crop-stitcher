import cv2
from rectrl import *

DISPLAY_TIME = 2  # 각 카메라당 미리보기 시간 (초)

RECTRL_Open()
RECTRL_EnableMasterSyncMode(True, CAM3)
RECTRL_Close()

for i in range(6):
    path = f"/dev/video{i}"
    cap = cv2.VideoCapture(path, cv2.CAP_V4L)

    if not cap.isOpened():
        print(f"[{i}] ❌ {path} : open failed")
        continue

    ret, frame = cap.read()
    if ret:
        print(f"[{i}] ✅ {path} : Frame shape = {frame.shape}")
    else:
        print(f"[{i}] ⚠️ {path} : Opened but no fqrame")
        cap.release()
        continue

    # 영상 미리보기
    start_time = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"[{i}] ⚠️ {path} : frame read failed during preview")
            break

        cv2.imshow(f'Camera {i} Preview', frame)

        # 'q'를 누르면 즉시 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

        if time.time() - start_time > DISPLAY_TIME:
            break

    cap.release()
    cv2.destroyAllWindows()
