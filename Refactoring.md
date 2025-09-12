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

### ✅ 변경되는 것들  
- 파일 구조: 단일 파일 → 여러 파일로 분리
- 클래스 설계: 강결합 → 느슨한 결합 (인터페이스 기반)
- 객체 생성: 직접 생성 → 팩토리 패턴
- 책임 분리: 한 클래스가 여러 책임 → 각 클래스가 단일 책임


## **1. Single Responsibility Principle (SRP)**
각 클래스가 하나의 책임만 가지도록 분리:

- `CameraCapture`: 카메라 프레임 캡처만 담당
- `CropCalculator`: 크롭 영역 계산만 담당  
- `GPUFrameProcessor`: 프레임 처리만 담당
- `HorizontalStitcher`: 프레임 스티칭만 담당
- `OpenCVDisplayManager`: 디스플레이 관리만 담당
- `FPSCounter`: FPS 계산 및 표시만 담당
- `PanoramaSystem`: 전체 시스템 조율만 담당

## **2. Open/Closed Principle (OCP)**
확장에는 열려있고 수정에는 닫혀있도록 인터페이스를 정의:

- 새로운 프레임 처리 방식을 추가하려면 `FrameProcessor` 인터페이스를 구현
- 다른 스티칭 알고리즘을 추가하려면 `FrameStitcher` 인터페이스를 구현
- 다른 디스플레이 방식을 추가하려면 `DisplayManager` 인터페이스를 구현

## **3. Liskov Substitution Principle (LSP)**
인터페이스를 구현한 모든 클래스가 기본 인터페이스와 동일하게 동작하도록 설계:

- 모든 `FrameProvider` 구현체는 동일한 방식으로 교체 가능
- 모든 `FrameProcessor` 구현체는 동일한 방식으로 교체 가능

## **4. Interface Segregation Principle (ISP)**
클라이언트가 사용하지 않는 인터페이스에 의존하지 않도록 세분화된 인터페이스를 제공:

- `FrameProvider`, `FrameProcessor`, `FrameStitcher`, `DisplayManager` 등 각각 필요한 메서드만 포함
- 큰 인터페이스 대신 역할별로 분리된 작은 인터페이스들

## **5. Dependency Inversion Principle (DIP)**
고수준 모듈이 저수준 모듈에 의존하지 않고, 둘 다 추상화에 의존:

- `PanoramaSystem`은 구체적인 구현체가 아닌 인터페이스에 의존
- `PanoramaSystemFactory`에서 의존성 주입을 통해 구체적인 객체들을 생성하고 주입

## **주요 개선사항:**

1. **모듈화**: 기능별로 파일을 분리하여 유지보수성 향상
2. **테스트 용이성**: 각 컴포넌트를 독립적으로 테스트 가능
3. **확장성**: 새로운 기능 추가 시 기존 코드 수정 최소화
4. **재사용성**: 각 컴포넌트를 다른 프로젝트에서도 재사용 가능
5. **의존성 관리**: Factory 패턴을 통한 깔끔한 의존성 주입


---
> - 's' : screenshot
> - 'q' or 'esc' : quit
> - 가로 crop 방식
>   - 사용자가 config 내 horizontal_crop 직접 설정
>   - config 내 카메라 당 시야각(desired_view_angle)을 설정하면, 가로 최대화각(fov)을 기반으로 crop 영역 계산 (horizontal_crop은 주석처리)
> - 세로 crop 방식
>   - 사용자가 config 내 vertical_crop 직접 설정
>   - `_auto_calculate_vertical_crop`이 모든 프레임에서 유효한 최소 영역을 찾아 크롭 범위를 계산
> - calibration :
>   - offset : (y축 중심) - (선택한 수평선의 y 평균값)
>     - 선택한 수평선 > y축 중심 : 양수
>     - 좌상단 원점 기준으로 이동 변환 
>     - 중심보다 수평선이 위에 있을 경우 아래방향으로 이동변환해주기 위해 양수의 보정 offset값이 들어가야 함. 
>   - angle : 선택한 수평선의 x1, y1, x2, y2로 arctan 계산
>     - 좌상단이 원점이므로, 우상향이 음수
>     - 회전보정에 쓰이는 함수에서는 반시계방향 각도가 양수
>     - 우상향 line일 경우 우하향 각도로 보정해주기 위해 양수의 보정 각도값이 들어가야 함.


