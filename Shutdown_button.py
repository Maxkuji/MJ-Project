import RPi.GPIO as GPIO
import time
import os
import subprocess

# กำหนดหมายเลขขา GPIO
BUTTON_SHUTDOWN = 3   # ปุ่มปิดเครื่อง
BUTTON_WIFI = 24      # ปุ่มเปิด WiFi-Connect
LED_WHITE_PIN = 17

# เวลากดค้างสำหรับแต่ละฟังก์ชัน
HOLD_TIME_SHUTDOWN = 5  # วินาที (ปิดเครื่อง)
HOLD_TIME_WIFI = 8      # วินาที (เปิด WiFi-Connect)

# ตั้งค่า GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_SHUTDOWN, GPIO.IN)
GPIO.setup(BUTTON_WIFI, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_WHITE_PIN, GPIO.OUT)
GPIO.output(LED_WHITE_PIN, GPIO.HIGH)

def run_wifi_connect():
    print("Starting WiFi-Connect...")
    subprocess.run(["sudo", "wifi-connect"], check=True)

def monitor_buttons():
    try:
        while True:
            # ตรวจจับปุ่มปิดเครื่อง
            if GPIO.input(BUTTON_SHUTDOWN) == GPIO.LOW:
                start_time = time.time()
                while GPIO.input(BUTTON_SHUTDOWN) == GPIO.LOW:
                    if time.time() - start_time >= HOLD_TIME_SHUTDOWN:
                        print("Shutting down...")
                        GPIO.output(LED_WHITE_PIN, GPIO.LOW)
                        os.system("sudo shutdown now")
                        return
                    time.sleep(0.1)

            # ตรวจจับปุ่ม WiFi-Connect
            if GPIO.input(BUTTON_WIFI) == GPIO.LOW:
                start_time = time.time()
                while GPIO.input(BUTTON_WIFI) == GPIO.LOW:
                    if time.time() - start_time >= HOLD_TIME_WIFI:
                        print("Button held for WiFi-Connect. Starting...")
                        run_wifi_connect()
                        time.sleep(1)  # ป้องกันการกดซ้ำ
                        break  # ออกจาก loop เพียงครั้งเดียว
                    time.sleep(0.1)

            time.sleep(0.1)

    except KeyboardInterrupt:
        GPIO.output(LED_WHITE_PIN, GPIO.LOW)
        GPIO.cleanup()

def main():
    monitor_buttons()

if __name__ == "__main__":
    main()
