import cv2
import numpy as np
import re
from pyzbar.pyzbar import decode, ZBarSymbol
from datetime import datetime, timedelta
from picamera2 import MappedArray, Picamera2, Preview
from libcamera import controls, Transform

barcodes = []
last_detected_time = {}
last_removed_time = {}
min_time_interval = timedelta(seconds=0)  # Minimum time interval between detections

colour = (255, 0, 0)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 2
thickness = 4

def start_camera(draw_callback):
    try:
        picam2 = Picamera2()
        picam2.start_preview(Preview.QTGL)

        # Lower the resolution to speed up the processing
        config = picam2.create_preview_configuration(main={"size": (640, 480)}, transform=Transform(hflip=False, vflip=False))
        picam2.configure(config)
        picam2.post_callback = draw_callback
        picam2.start()

        #Experiment with different LensPosition values to get the best focus
        
        picam2.set_controls({
            "AfMode": controls.AfModeEnum.Continuous, #Hybrid
            #"AfTrigger": controls.AfTriggerEnum.Start,
            "LensPosition": 2.0 , # Adjust this value for best focus
            #"AeEnable": False,  # Disable auto exposure
            #"ExposureTime": 10000,  # Set exposure time (in microseconds), adjust as needed
            #"AnalogueGain": 8.0  # Set gain, adjust as needed
        })
    
        return picam2
    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะเริ่มต้นกล้อง : {e}")
        return None     

        
def draw_barcodes(request, log_qr_data):
    global barcodes, last_detected_time, last_removed_time
    with MappedArray(request, "main") as m:
        current_barcodes = set()
        for b in barcodes:
            if b.polygon and len(b.polygon) > 0:
                point = [(int(p.x),int(p.y)) for p in b.polygon]
                cv2.polylines(m.array, [np.array(point, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=4)
                x = min([p.x for p in b.polygon])
                y = min([p.y for p in b.polygon]) - 30
                cv2.putText(m.array, b.data.decode('utf-8'), (x, y), font, scale, colour, thickness)
                qr_data = b.data.decode('utf-8')
                current_barcodes.add(qr_data)

        current_time = datetime.now()

        # Detect new barcodes
        for barcode in current_barcodes:
            if barcode not in last_detected_time or (current_time - last_detected_time[barcode]) > min_time_interval:
                last_detected_time[barcode] = current_time
                log_qr_data(barcode, current_time)

        # Detect lost barcodes
        for barcode in list(last_detected_time.keys()):
            if barcode not in current_barcodes and (current_time - last_removed_time.get(barcode, datetime.min)) > min_time_interval:
                last_removed_time[barcode] = current_time
                log_qr_data(barcode, current_time, remove=True)
                last_detected_time.pop(barcode)

def capture_barcodes(picam2):
    global barcodes
    try:
        # ดึงภาพจากกล้อง
        image = picam2.capture_array("main")

        # แปลงภาพเป็นขาวดำ
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # ใช้ threshold แบบปรับตัวเพื่อความคมชัดที่ดีกว่า
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
       )

        # ถอดรหัส QR code
        decoded_barcodes = decode(binary, symbols=[ZBarSymbol.QRCODE])
        pattern = re.compile(r"^[A-Z]{2}\d{3}$")
        
        if decoded_barcodes:
            barcodes = [b for b in decoded_barcodes if pattern.match(b.data.decode('utf-8'))]
        else:
            barcodes = []
        
    except Exception as e:
       print(f"เกิดข้อผิดพลาดในการจับภาพ QR code: {e}")


