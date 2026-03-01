## Calibration Flow (보정 흐름)

1. 사용자 인터페이스를 통해 수평선 선택
   - 사용자는 각 카메라 프레임에서 수평선을 선택하여 기준 수평선을 지정함.
   - 선택된 수평선의 좌표를 기반으로 보정 각도와 오프셋 계산함.
2. 보정 각도 및 오프셋 계산
   - 보정 각도: 선택된 수평선의 기울기를 arctan으로 계산하여 보정 각도 도출
   - 보정 오프셋: 선택된 수평선의 y 평균값과 프레임의 y축 중심값의 차이를 계산하여 보정 오프셋 도출
3. config.yaml에 보정 값 반영
   - 계산된 보정 각도와 오프셋 값을 config.yaml의 해당 카메라 설정에 업데이트하여 저장
4. 보정된 설정으로 파노라마 정렬
   - config.yaml에 저장된 보정 각도와 오프셋을 기반으로 각 카메라 프레임을 정렬하여 파노라마 영상 생성


## 사용자 인터페이스 설명
- 마우스 클릭 : 수평선 선택 (각 카메라 프레임에서 수평선을 선택)
- 's' : screenshot
- 'q' or 'esc' : quit
 
## crop 방식 설명
- 가로 crop 방식
  - 사용자가 config 내 horizontal_crop 직접 설정
  - config 내 카메라 당 시야각(desired_view_angle)을 설정하면, 가로 최대화각(fov)을 기반으로 crop 영역 계산 (horizontal_crop은 주석처리)
- 세로 crop 방식
  - 사용자가 config 내 vertical_crop 직접 설정
  - `_auto_calculate_vertical_crop`이 모든 프레임에서 유효한 최소 영역을 찾아 크롭 범위를 계산
- calibration :
  - angle : 선택한 수평선의 x1, y1, x2, y2로 arctan 계산
    - 좌상단이 원점이므로, 우상향이 음수
    - 회전보정에 쓰이는 함수에서는 반시계방향 각도가 양수
    - 우상향 line일 경우 시계방향으로 보정해주기 위해 음수의 보정 각도값이 들어가야 함.
    - 계산 angle -> 보정 시 angle  (config 에 angle 이 들어감)
  - offset : (선택한 수평선의 y 평균값) - (y축 중심) 
    - 선택한 수평선 > y축 중심 : 음수
    - 좌상단 원점 기준으로 이동 변환 
    - 중심보다 선택한 선이 위에 있을 경우 아래방향으로 이동변환해주기 위해 양수의 보정 offset값이 들어가야 함.
    - 계산 offset -> 보정 시 -offset  (config 에는 offset 이 들어감)