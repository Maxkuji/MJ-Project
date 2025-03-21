import requests
import os
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime

# ตั้งค่า GPIO สำหรับ LED สีแดง
LED_RED_PIN = 2
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_RED_PIN, GPIO.OUT)
GPIO.output(LED_RED_PIN, GPIO.HIGH)

# ตัวแปรควบคุมการกระพริบ LED สีแดง
stop_blink_red = False
#wifi_check_interval = 120  # เช็คทุก 5 นาที
wifi_event = threading.Event()

# ฟังก์ชันควบคุม LED สีแดง
def led_red_on():
    global stop_blink_red
    stop_blink_red = True  # หยุดกระพริบ
    GPIO.output(LED_RED_PIN, GPIO.HIGH)

def led_red_off():
    GPIO.output(LED_RED_PIN, GPIO.LOW)

def led_red_blink():
    global stop_blink_red
    stop_blink_red = False
    threading.Thread(target=_blink_red).start()

def _blink_red():
    global stop_blink_red
    while not stop_blink_red:
        GPIO.output(LED_RED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        time.sleep(1)

# ฟังก์ชันตรวจสอบ Wi-Fi
def is_connected():
    try:
        requests.get("http://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

# ฟังก์ชันตรวจสอบ Wi-Fi ด้วย Event-based Mechanism
def check_wifi_connection():
    global stop_blink_red
    last_status = None  # เก็บสถานะ Wi-Fi ล่าสุด

    while True:
        response = os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")
        current_status = (response == 0)  # True = connected, False = disconnected

        if current_status != last_status:  # เช็คเฉพาะเมื่อสถานะเปลี่ยนแปลง
            if current_status:
                stop_blink_red = True
                led_red_on()
                print("✅ Wi-Fi connected, LED red ON")
            else:
                stop_blink_red = False  # รีเซ็ตให้ LED กระพริบเมื่อ Wi-Fi หลุด
                led_red_blink()
                print("❌ Wi-Fi not connected, LED red BLINK")

            last_status = current_status  # อัปเดตสถานะล่าสุด
        
        time.sleep(5)  # เช็ค Wi-Fi ทุก 5 วินาที


# เรียกเช็ค Wi-Fi เมื่อมีการส่งข้อมูล
def trigger_wifi_check():
    wifi_event.set()
    wifi_event.clear()

# ฟังก์ชันส่ง QR Code ไปที่เซิร์ฟเวอร์
def send_qr_data_to_server(qr_data, description, id_mc="7523", id_cam="Cam03", timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    url = "https://bunnam.com/projects/mjrqr/pp-insert.php"
    data = {
        'id_mc': id_mc,
        'id_cam': id_cam,
        'qr_code_data': qr_data,
        'description': description,
        'timestamp': timestamp,
    }

    trigger_wifi_check()

    if not is_connected():
        print("Wi-Fi not connected. Data not sent.")
        return

    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Data sent successfully:", response.text)
        else:
            print(f"Failed to send data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send data: {e}")

# เริ่มต้นเธรดตรวจสอบ Wi-Fi
threading.Thread(target=check_wifi_connection, daemon=True).start()
