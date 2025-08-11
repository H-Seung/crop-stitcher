from ctypes import *
import time

# CAM ID
(CAM0, CAM1, CAM2, CAM3, CAM4, CAM5, CAM_ALL) = (1, 2, 3, 4, 5, 6, 255)

# TEST PATTERN TYPES
(NO_PATTERN, SOLID_COLOR, VERTIAL_COLOR_BARS, FADE_TO_GRAY_COLOR_BARS) = (0, 1, 2, 3)

# CAMERA PROPERTIES
(BRIGHTNESS, SHUTTER, AGC, AWB_MODE, AWB_MANUAL_CTEMP, 
 AWB_MANUAL_RGAIN, AWB_MANUAL_BGAIN, COLOR_GAIN, COLOR_TONE, DNR, 
 SHARPNESS, MIRROR, FLIP, SHADING_MODE, SHADING_WEIGHT,
 SHADING_DET, REF_FRAMERATE) = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17)

rectrl = cdll.LoadLibrary("./librectrl.so")
rectrl.RECTRL_Open.argtypes = []
rectrl.RECTRL_Close.argtypes = []
rectrl.RECTRL_Set.argtypes = [c_int32, c_int32, c_int32]
rectrl.RECTRL_SetTestPattern.argtypes = [c_int32, c_int32]
rectrl.RECTRL_GetSensorStatus.argtypes = [c_int32, POINTER(c_int32)]
rectrl.RECTRL_GetSensorTemperature.argtypes = [c_int32, POINTER(c_double)]
rectrl.RECTRL_EnableMasterSyncMode.argtypes = [c_int8, c_int32]
rectrl.RECTRL_SetSyncDelay.argtypes = [c_int32]
rectrl.RECTRL_SensorRead.argtypes = [c_int32, c_uint16, POINTER(c_uint16)]
rectrl.RECTRL_SensorWrite.argtypes = [c_int32, c_uint16, c_uint16]
rectrl.RECTRL_GetBridgeboardFirmwareVersion.argtypes = [POINTER(c_int32)]
rectrl.RECTRL_GetCameraFirmwareVersion.argtypes = [c_int32, POINTER(c_int32)]
rectrl.RECTRL_GetSerialNumber.argtypes = [c_int32, c_char_p]
rectrl.RECTRL_WriteCalibrationData.argtypes = [c_int32, c_char_p, c_int32]
rectrl.RECTRL_ReadCalibrationData.argtypes = [c_int32, c_char_p, c_int32]

# rename function
RECTRL_Open = rectrl.RECTRL_Open
RECTRL_Close = rectrl.RECTRL_Close
RECTRL_Set = rectrl.RECTRL_Set
RECTRL_SetTestPattern = rectrl.RECTRL_SetTestPattern
RECTRL_GetSensorStatus = rectrl.RECTRL_GetSensorStatus
RECTRL_GetSensorTemperature = rectrl.RECTRL_GetSensorTemperature
RECTRL_EnableMasterSyncMode = rectrl.RECTRL_EnableMasterSyncMode
RECTRL_SetSyncDelay = rectrl.RECTRL_SetSyncDelay
RECTRL_SensorRead = rectrl.RECTRL_SensorRead
RECTRL_SensorWrite = rectrl.RECTRL_SensorWrite
RECTRL_GetBridgeboardFirmwareVersion = rectrl.RECTRL_GetBridgeboardFirmwareVersion
RECTRL_GetCameraFirmwareVersion = rectrl.RECTRL_GetCameraFirmwareVersion
RECTRL_GetSerialNumber = rectrl.RECTRL_GetSerialNumber
RECTRL_WriteCalibrationData = rectrl.RECTRL_WriteCalibrationData
RECTRL_ReadCalibrationData = rectrl.RECTRL_ReadCalibrationData
