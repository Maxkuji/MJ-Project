import threading
import time
from datetime import datetime
from gpiozero import LED
from camera_controller import start_camera, draw_barcodes, capture_barcodes
from server_communication import send_qr_data_to_server, led_red_on, led_red_off, led_red_blink
import Shutdown_button  # นำเข้า Shutdown_button.py


# ตั้งค่า GPIO สำหรับ LED สีเขียว
led_green = LED(27)

# ตัวแปรเก็บ QR Code ที่ตรวจพบล่าสุด
active_qr_codes = {}

# รัน Shutdown_button เป็นเธรด
shutdown_thread = threading.Thread(target=Shutdown_button.monitor_buttons, daemon=True)
shutdown_thread.start()

def log_qr_data(qr_data, timestamp, remove=False):
    global active_qr_codes
    formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    if remove:
        if qr_data in active_qr_codes:
            send_qr_data_to_server(qr_data, "removed")
            print(f"{qr_data} removed at {formatted_time}")
            del active_qr_codes[qr_data]
            led_green.off()
    else:
        if qr_data not in active_qr_codes:
            send_qr_data_to_server(qr_data, "detected")
            print(f"{qr_data} detected at {formatted_time}")
            led_green.on()

        active_qr_codes[qr_data] = timestamp

if __name__ == "__main__":
    try:
        picam2 = start_camera(lambda req: draw_barcodes(req, log_qr_data))

        while True:
            capture_barcodes(picam2)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Stopping program...")
    finally:
        led_green.off()
    if picam2:
        picam2.stop()
