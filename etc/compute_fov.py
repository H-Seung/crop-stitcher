import math

def estimate_fov(visible_width_cm, distance_cm):
    fov_rad = 2 * math.atan((visible_width_cm / 2) / distance_cm)
    fov_deg = math.degrees(fov_rad)
    return fov_deg

# 벽 중심을 정면으로 바라봐야 함.
# 예: 카메라에서 100cm 떨어진 벽에 화면 왼쪽 ~ 오른쪽 끝을 표시하고,
# 폭 사이의 거리가 80cm 일 때
visible_width_cm = 230 # 화면에 보이는 최대 가로 폭 (cm)
distance_cm = 109 # 카메라에서 벽까지 거리 (cm)
estimated_fov = estimate_fov(visible_width_cm, distance_cm)
print(f"Estimated Horizontal FOV: {estimated_fov:.2f} degrees")