# 기존 코드 기반 SOLID 리팩토링 디렉토리 구조

## SOLID 원칙 적용:

- SRP: 각 클래스가 하나의 책임만 담당
- OCP: 인터페이스를 통해 확장에 열려있음
- LSP: 모든 구현체가 인터페이스와 호환됨
- ISP: 필요한 메서드만 포함한 세분화된 인터페이스
- DIP: 구체적 구현이 아닌 추상화에 의존

## 기존 파일들
```
panorama_project/
├── config.yaml                      # [기존] 설정 파일
├── librectrl.so                     # [기존] 외부 라이브러리
├── rectrl.py                        # [기존] 카메라 제어 라이브러리  
├── calibration2.py                  # [기존] 캘리브레이션 스크립트
└── panorama.py                      # [기존] 메인 코드 (리팩토링 대상)
```

## 리팩토링 후 구조
```
panorama_project/
├── main.py                          # [새파일] 진입점 (기존 panorama.py의 main() 분리)
├── config.yaml                      # [기존] 설정 파일
├── librectrl.so                     # [기존] 외부 라이브러리
├── rectrl.py                        # [기존] 카메라 제어 라이브러리
├── calibration2.py                  # [기존] 캘리브레이션 스크립트
│
└── panorama/                        # [새폴더] 기존 panorama.py 내용을 SOLID 원칙으로 분리
    ├── __init__.py                  # 패키지 정의
    │
    ├── interfaces.py                # [분리] 모든 추상 클래스들
    ├── data_models.py               # [분리] CameraFrame 데이터 클래스
    │
    ├── config_manager.py            # [분리] YamlConfigProvider (기존 _load_config)
    ├── camera_capture.py            # [분리] CameraCapture 클래스
    ├── frame_processing.py          # [분리] GPU 프레임 처리 + 크롭 계산
    ├── stitching.py                 # [분리] PanoramaStitcher 클래스  
    ├── display_manager.py           # [분리] 디스플레이 관리 로직
    └── panorama_viewer.py           # [분리] PanoramaViewer 클래스 (메인 조율)
    
```

## 각 파일의 내용 분리 근거

### 1. `panorama/interfaces.py`
```python
# 기존 코드에 있던 추상적 개념들을 인터페이스로 정의
# - FrameProvider (CameraCapture가 구현)  
# - FrameProcessor (PanoramaStitcher.crop_and_align 기능)
# - FrameStitcher (PanoramaStitcher.stitch_frames 기능)
# - ConfigProvider (PanoramaViewer._load_config 기능)
# - DisplayManager (PanoramaViewer의 디스플레이 로직)
```

### 2. `panorama/data_models.py`
```python
# 기존 코드의 CameraFrame 데이터 클래스만 분리
```

### 3. `panorama/config_manager.py` 
```python
# 기존 PanoramaViewer._load_config() 메서드를 별도 클래스로 분리
```

### 4. `panorama/camera_capture.py`
```python  
# 기존 CameraCapture 클래스 그대로 (인터페이스 구현하도록 수정)
```

### 5. `panorama/frame_processing.py`
```python
# 기존 PanoramaStitcher의 다음 기능들을 분리:
# - _calc_crop() 메서드 -> CropCalculator 클래스
# - crop_and_align() 메서드 -> GPUFrameProcessor 클래스  
# - _compute_crop_pixels_from_fov() 메서드
```

### 6. `panorama/stitching.py`
```python
# 기존 PanoramaStitcher의 stitch_frames() 메서드를 별도 클래스로 분리
```

### 7. `panorama/display_manager.py`
```python
# 기존 PanoramaViewer.run() 메서드의 디스플레이 관련 로직들을 분리:
# - cv2.namedWindow, cv2.imshow 관련 코드
# - 윈도우 크기 조정 로직
# - 키 입력 처리
# - FPS 표시 로직
```

### 8. `panorama/panorama_viewer.py`
```python
# 기존 PanoramaViewer 클래스에서 비즈니스 로직만 남기고
# 각종 구체적인 구현체들은 의존성 주입으로 받도록 수정
# + PanoramaViewerFactory 클래스 포함
# 기존 PanoramaViewer.__init__()에서 하던 객체 생성을 Factory에서 담당
```

### 9. `main.py`
```python
# 기존 panorama.py의 main() 함수와 if __name__ == '__main__' 부분만
```

## 리팩토링 원칙

### ✅ 유지되는 것들
- 모든 기존 기능과 로직
- 기존 설정 파일 (config.yaml) 형식
- 기존 외부 라이브러리 의존성
- 기존 성능과 동작 방식

### ✅ 변경되는 것들  
- 파일 구조: 단일 파일 → 여러 파일로 분리
- 클래스 설계: 강결합 → 느슨한 결합 (인터페이스 기반)
- 객체 생성: 직접 생성 → 팩토리 패턴
- 책임 분리: 한 클래스가 여러 책임 → 각 클래스가 단일 책임

### ❌ 추가하지 않는 것들
- 새로운 기능이나 알고리즘
- 기존에 없던 설정 옵션들
- 추가적인 외부 라이브러리
- 기존에 없던 로깅, 테스트, 문서화 기능
