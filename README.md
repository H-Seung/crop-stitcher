# crop-stitcher

---
![Python](https://img.shields.io/badge/-Python-blue?logo=python&logoColor=white)


**crop-stitcher**는 다음을 포함하는 멀티 카메라 실시간 파노라마 시스템입니다.

- 실시간 카메라 스트리밍
- 사용자 인터랙션 기반 캘리브레이션
- 변환 행렬 기반 영상 정합
- 실시간 파노라마 출력

##  시스템 아키텍처 개요
```
Camera Input → Calibration → Perspective Transform → Stitching → Panorama Viewer
| CameraCapture |      →      | FrameProcessing |
(Multi-Camera Frame Input)   (Preprocess / Calibration)
                                     |
                                     v
                              | CropStitching |
                              (Crop & Align Frames)
                                     |
                                     v
                              | PanoramaViewer |
                              (Display / Screenshot)

```

### 주요 클래스 역할

### `CameraCapture`
- 다중 카메라 동시 프레임 획득
- 카메라 스트림 관리
- 프레임 동기화 처리


### `FrameProcessing`
- 왜곡 보정 (Undistortion)
- 수평 보정 (Roll correction)
- 좌표 변환
- Perspective / Homography 적용

캘리브레이션 결과값을 기반으로 각 카메라 프레임을 정렬 가능한 상태로 변환합니다.


### `CropStitching`
- 변환된 각 프레임을 파노라마 좌표계로 매핑
- 겹침 영역 정렬
- 최종 파노라마 이미지 생성


### `PanoramaViewer`
- 실시간 파노라마 화면 출력
- 디버그 모드 지원
- 스크린샷 저장 기능


### `PanoramaFactory`
- 시스템 전체 구성 객체 생성
- 모듈 간 의존성 주입
- 설정 파일(config.yaml) 기반 초기화

---

## 실행 흐름
1. **초기 설정**: `config.yaml` 파일에서 카메라 개수, 입력 해상도, 초기 오프셋 및 기타 파라미터를 정의합니다.
2. **캘리브레이션**: 사용자가 선택한 수평선과 캘리브레이션 절차를 통해 각 카메라의 왜곡 보정 및 수평 보정 파라미터를 계산하여 config.yaml에 업데이트합니다.
3. **프레임 캡처**: `CameraCapture` 클래스가 각 카메라에서 실시간으로 프레임을 획득합니다.
3. **왜곡 및 수평 보정**: 획득한 프레임에 대해 `FrameProcessing` 클래스가 카메라 왜곡 및 수평 보정을 수행합니다. (config.yaml의 angle과 offset 값 사용)
5. **크롭 영역 계산**: 수평 보정된 프레임에서 가로 및 세로 크롭 영역을 계산합니다. (config.yaml의 horizontal_crop, vertical_crop)
6. **파노라마 매핑**: `CropStitching` 클래스가 각 프레임을 파노라마 좌표계로 매핑하고 겹침 영역을 정렬합니다.
7. **실시간 출력**: `PanoramaViewer` 클래스가 병합된 파노라마 영상을 실시간으로 디스플레이합니다.
---

## 주요 기능

### 1️⃣ 실시간 다중 카메라 입력
- 다중 카메라 동시 스트리밍 처리
- 프레임 동기화 관리
- FPS 관리 및 최적화 구조 포함

### 2️⃣ 정밀 캘리브레이션 시스템
- 카메라 왜곡 보정
- 수평 정렬(horizon alignment)
- 카메라 간 위치 보정
- 수동 / 자동 설정 파일 지원 (`config.yaml`)


### 3️⃣ 변환 및 정합
- Homography 기반 투영 변환
- 파노라마 평면 좌표계 매핑
- 카메라 간 겹침 영역 정렬

### 4️⃣ 실시간 파노라마 출력
- 병합 영상 디스플레이
- 스크린샷 저장 기능
- 디버그 모드 지원

---

## 주요 디렉토리 구조
```
.
├── main.py
├── config.yaml
├── panorama/
│ ├── camera_capture.py
│ ├── crop_stitching.py
│ ├── transformation_utils.py
│ ├── panorama_viewer.py
│ └── ...
├── calibration/
│ ├── calibration2.py
│ └── test_images/
└── requirements.txt
```


---

## 설치 방법

### 1. Python 3.10 설치


### 2. 가상 환경 생성

```bash
python -m venv venv
```

### 3. 가상 환경 활성화

**Windows**

```bash
venv\Scripts\activate
```

**Mac / Linux**

```bash
source venv/bin/activate
```

### 4. 의존성 설치

```bash
pip install -r requirements.txt
```

---

## 실행 방법

```bash
python main.py
```
필요한 카메라 설정 및 보정 파라미터는 config.yaml을 통해 조정합니다.

---

### 설정 파일 (config.yaml)

`config.yaml` 파일을 통해 시스템 동작을 제어합니다.

주요 설정 항목은 다음과 같습니다:

- 카메라 개수
- 입력 해상도
- 각 카메라별 수직/수평 오프셋
- 변환 행렬 (Homography / Perspective)
- 캘리브레이션 값
- 디버그 모드 활성화 여부

캘리브레이션을 통해 계산된 값들은 이 설정 파일에 반영되며,  
파노라마 정합 품질은 설정 정확도에 직접적인 영향을 받습니다.

---

### Calibration 문서

캘리브레이션 절차 및 보정 방식은  
👉 `calibration/` 폴더 및 별도로 작성된 Calibration README를 참고하세요.

본 시스템은 캘리브레이션 정확도에 따라  
최종 파노라마 결과의 정렬 품질이 결정됩니다.

---

###  설계 의도

이 프로젝트는 단순 이미지 스티칭 도구가 아니라,  
다음과 같은 시스템 설계를 목표로 합니다:

- 멀티 카메라 기반 파노라마 시스템 설계
- 실시간 영상 처리 구조
- 모듈화된 파노라마 파이프라인
- 확장 가능한 구조 (N-Camera 대응)

구조적으로 확장성과 유지보수를 고려하여 설계되었습니다.