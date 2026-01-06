import time
import network
import urequests
import ujson
from lcd import LCD
from machine import Pin, PWM, ADC, SoftSPI
from mfrc522 import MFRC522
import uasyncio as asyncio

# -----------------------------------------------------------
# Konstanter
# -----------------------------------------------------------
SSID = "Markus"
PASSWORD = "123445678"
PC_IP = "10.57.83.218"
API_KEY = "hemmelig_nokkel123"

URL_SEND = f"http://{PC_IP}:5000/send"
URL_GET  = f"http://{PC_IP}:5000/get"
HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}

ALLOWED_UIDS = [
    [61, 145, 51, 4],
    [83, 252, 196, 1],
    [100, 210, 196, 1]
]

FALLBACK_TIMES = [(7,0),(13,0),(18,0)]
last_uid = [100, 210, 196, 1]

# -----------------------------------------------------------
# Globale states / timere
# -----------------------------------------------------------
state = "idle"
last_uid = None
last_uid_time = 0
UID_COOLDOWN = 3000
last_log_time = 0

# -----------------------------------------------------------
# Timer helper
# -----------------------------------------------------------
class TimerNB:
    def __init__(self, ms=0):
        self.set(ms)
    def set(self, ms):
        self.start = time.ticks_ms()
        self.duration = ms
    def done(self):
        return time.ticks_diff(time.ticks_ms(), self.start) >= self.duration

# -----------------------------------------------------------
# Hardware
# -----------------------------------------------------------
# Magnet sensor
adc = ADC(Pin(36))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

# PIR
pir = Pin(17, Pin.IN)

# RFID (SPI)
spi = SoftSPI(baudrate=1_000_000, polarity=0, phase=0,
               sck=Pin(18), mosi=Pin(23), miso=Pin(19))
reader = MFRC522(spi, Pin(21))

# LCD
lcd = LCD(rs=27, e=25, d4=33, d5=32, d6=16, d7=22, bl=2)

# Stepper
pins = [Pin(p, Pin.OUT) for p in [15,2,0,4]]
sequence = [[1,0,0,1],[1,0,0,0],[1,1,0,0],[0,1,0,0],
            [0,1,1,0],[0,0,1,0],[0,0,1,1],[0,0,0,1]]
step_index = 0
steps_left = 0
step_delay = 2
last_step_time = 0

# Servo
servo = PWM(Pin(14), freq=50)
servo_timer = TimerNB()
def set_angle(angle):
    duty = int(40 + (angle / 180) * (115 - 40))
    servo.duty(duty)

# -----------------------------------------------------------
# Stepper funktioner
# -----------------------------------------------------------
def start_rotate_24_deg(direction=1):
    global steps_left
    steps_left = int(24 / (360/4096)) * direction

def update_stepmotor():
    global step_index, steps_left, last_step_time
    if steps_left == 0:
        return
    now = time.ticks_ms()
    if time.ticks_diff(now, last_step_time) < step_delay:
        return
    last_step_time = now
    seq = sequence if steps_left > 0 else sequence[::-1]
    step = seq[step_index]
    for pin, val in zip(pins, step):
        pin.value(val)
    step_index = (step_index + 1) % 8
    steps_left += -1 if steps_left > 0 else 1

# -----------------------------------------------------------
# WiFi / server
# -----------------------------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.2)
    return wlan.ifconfig()[0]

def safe_get(url):
    try:
        r = urequests.get(url, headers=HEADERS)
        data = r.json()
        r.close()
        return data
    except:
        return None

def safe_post(url, payload):
    try:
        r = urequests.post(url, data=ujson.dumps(payload), headers=HEADERS)
        r.close()
    except:
        pass

# -----------------------------------------------------------
# Tidsplan
# -----------------------------------------------------------
def get_ms_until_next_target(times):
    now = time.localtime()
    now_sec = now[3]*3600 + now[4]*60 + now[5]
    best = None
    for h,m in times:
        t = h*3600 + m*60
        diff = t - now_sec
        if diff < 0: diff += 86400
        if best is None or diff < best: best = diff
    return best * 1000

# -----------------------------------------------------------
# State machine
# -----------------------------------------------------------
def update_give_piller():
    global state
    if state == "rotate" and steps_left == 0:
        lcd.clear()
        print("Tjekker kop...")
        state = "check_magnet"
    elif state == "check_magnet":
        if adc.read() > 100:
            lcd.clear()
            lcd.write("Piller gives")
            set_angle(170)
            servo_timer.set(60_000)
            state = "wait_servo"
        else:
            lcd.clear()
            lcd.write("Husk koppen!")
            state = "idle"
    elif state == "wait_servo" and servo_timer.done():
        set_angle(0)
        state = "idle"

# -----------------------------------------------------------
# Async tasks
# -----------------------------------------------------------
async def stepmotor_task():
    while True:
        update_stepmotor()
        await asyncio.sleep_ms(20)

async def servo_task():
    while True:
        update_give_piller()
        await asyncio.sleep_ms(80)

async def rfid_task():
    global state, last_uid, last_uid_time
    while True:
        status, bits = reader.request(reader.CARD_REQIDL)
        if status == reader.OK:
            status, uid = reader.anticoll()
            if status == reader.OK:
                uid = uid[:4]
                now = time.ticks_ms()
                if uid == last_uid and time.ticks_diff(now, last_uid_time) < UID_COOLDOWN:
                    await asyncio.sleep_ms(200)
                    continue
                last_uid = uid
                last_uid_time = now
                if uid in ALLOWED_UIDS and state == "idle":
                    lcd.clear()
                    lcd.write("RFID OK")
                    start_rotate_24_deg()
                    state = "rotate"
                    # Send til server straks
                    rfid_str = ":".join(str(b) for b in uid)
                    safe_post(URL_SEND, {"RF_log_time":[rfid_str,int(time.time())]})
                else:
                    lcd.clear()
                    lcd.write("RFID AFVIST")
                    print("Ukendt UID:", uid)
        await asyncio.sleep_ms(400)

async def pir_task():
    last = 0
    while True:
        now = pir.value()
        if now and not last:
            lcd.clear()
            print("Bevægelse!")
        last = now
        await asyncio.sleep_ms(300)

async def server_log_task():
    global last_log_time, last_uid
    last_log_time = time.ticks_ms()
    while True:
        if time.ticks_diff(time.ticks_ms(), last_log_time) > 60_000:
            rfid_str = ":".join(str(b) for b in last_uid) if last_uid else None
            payload = {
                "RF_log_time":[rfid_str,int(time.time())],
            }
            safe_post(URL_SEND, payload)
            last_log_time = time.ticks_ms()
        await asyncio.sleep_ms(1000)

# -----------------------------------------------------------
# Scheduler
# -----------------------------------------------------------
async def scheduler_task():
    global state, next_pill_time
    while True:
        if time.ticks_ms() >= next_pill_time and state == "idle":
            start_rotate_24_deg()
            state = "rotate"
            next_pill_time = time.ticks_ms() + get_ms_until_next_target(TIMES)
        await asyncio.sleep_ms(200)

# -----------------------------------------------------------
# Main
# -----------------------------------------------------------
try:
    connect_wifi()
    server_data = safe_get(URL_GET)
    TIMES = server_data.get("Tider", FALLBACK_TIMES) if server_data else FALLBACK_TIMES
except:
    TIMES = FALLBACK_TIMES

print("Klar til pilledeling")
next_pill_time = time.ticks_ms() + get_ms_until_next_target(TIMES)

async def main():
    await asyncio.gather(
        stepmotor_task(),
        servo_task(),
        rfid_task(),
        pir_task(),
        server_log_task(),
        scheduler_task()
    )

asyncio.run(main())
