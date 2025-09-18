> - 's' : screenshot
> - 'q' or 'esc' : quit
> - 가로 crop 방식
>   - 사용자가 config 내 horizontal_crop 직접 설정
>   - config 내 카메라 당 시야각(desired_view_angle)을 설정하면, 가로 최대화각(fov)을 기반으로 crop 영역 계산 (horizontal_crop은 주석처리)
> - 세로 crop 방식
>   - 사용자가 config 내 vertical_crop 직접 설정
>   - `_auto_calculate_vertical_crop`이 모든 프레임에서 유효한 최소 영역을 찾아 크롭 범위를 계산
> - calibration :
>   - angle : 선택한 수평선의 x1, y1, x2, y2로 arctan 계산
>     - 좌상단이 원점이므로, 우상향이 음수
>     - 회전보정에 쓰이는 함수에서는 반시계방향 각도가 양수
>     - 우상향 line일 경우 시계방향으로 보정해주기 위해 음수의 보정 각도값이 들어가야 함.
>     - 계산 angle -> 보정 시 angle  (config 에 angle 이 들어감)
>   - offset : (선택한 수평선의 y 평균값) - (y축 중심) 
>     - 선택한 수평선 > y축 중심 : 음수
>     - 좌상단 원점 기준으로 이동 변환 
>     - 중심보다 선택한 선이 위에 있을 경우 아래방향으로 이동변환해주기 위해 양수의 보정 offset값이 들어가야 함.
>     - 계산 offset -> 보정 시 -offset  (config 에는 offset 이 들어감)