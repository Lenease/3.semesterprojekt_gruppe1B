import time
import network
import urequests
import ujson
import json
from machine import Pin, PWM, ADC, SoftSPI
from mfrc522 import MFRC522
import uasyncio as asyncio

# -----------------------------------------------------------
# Wifi
# -----------------------------------------------------------
SSID = "Markus"
PASSWORD = "123445678"
PC_IP = "10.89.246.218"
API_KEY = "hemmelig_nokkel123"
URL_SEND = f"http://{PC_IP}:5000/send"
URL_GET  = f"http://{PC_IP}:5000/get"
HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}

# -----------------------------------------------------------
# RFID liste
# -----------------------------------------------------------
ALLOWED_UIDS = [
    [61, 145, 51, 4],
    [83, 252, 196, 1],
    [100, 210, 196, 1]
]


# -----------------------------------------------------------
# Timer helper
# -----------------------------------------------------------
class TimerNB:
    """Non-blocking timer baseret på ticks_ms"""
    def __init__(self, ms=0):
        self.set(ms)

    def set(self, ms):
        self.start = time.ticks_ms()
        self.duration = ms

    def done(self):
        return time.ticks_diff(time.ticks_ms(), self.start) >= self.duration

# -----------------------------------------------------------
# Sensors, LCD, Stepper, Servo
# -----------------------------------------------------------

# Magnet sensor
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

# PIR sensor
pir = Pin(17, Pin.IN)

# RFID
sck = Pin(18)
mosi = Pin(23)
miso = Pin(19)
spi = SoftSPI(baudrate=1_000_000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)
sda = Pin(21)
reader = MFRC522(spi, sda)

# LCD
lcd = LCD(rs=27, e=25, d4=33, d5=32, d6=16, d7=22, bl=2)

# Stepmotor (ULN2003)
IN1 = Pin(5, Pin.OUT)
IN2 = Pin(18, Pin.OUT)
IN3 = Pin(19, Pin.OUT)
IN4 = Pin(21, Pin.OUT)
pins = [IN1, IN2, IN3, IN4]

sequence = [
    [1,0,0,1],[1,0,0,0],[1,1,0,0],[0,1,0,0],
    [0,1,1,0],[0,0,1,0],[0,0,1,1],[0,0,0,1]
]

step_index = 0
steps_left = 0
step_delay = 2
last_step_time = 0

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
    steps_left -= 1 if steps_left > 0 else -1

# Servo
servo = PWM(Pin(14), freq=50)
servo_state = "idle"
servo_timer = TimerNB()

def set_angle(angle):
    duty = int(26 + (angle / 180) * (128 - 26))
    servo.duty(duty)

# -----------------------------------------------------------
# WiFi + server
# -----------------------------------------------------------
def connect_wifi(timeout=10):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        t0 = time.time()
        while not wlan.isconnected():
            time.sleep(0.2)
            if time.time() - t0 > timeout:
                raise OSError("WiFi connect timeout")
    try:
        import ntptime
        ntptime.settime()
    except:
        pass
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
        j = None
        try:
            j = r.json()
        except:
            pass
        r.close()
        return j
    except:
        return None

# -----------------------------------------------------------
# JSON log
# -----------------------------------------------------------
def write_json(value):
    data = {"value": value, "timestamp": time.time()}
    with open("data.json", "w") as f:
        json.dump(data, f)

def read_json():
    try:
        with open("data.json") as f:
            return json.load(f)
    except OSError:
        print("Filen findes ikke.")
        return None

content = read_json()
print(content)

# -----------------------------------------------------------
# Tidsplan
# -----------------------------------------------------------
FALLBACK_TIMES = [(7,0),(13,0),(18,0)]

def get_ms_until_next_target(times=FALLBACK_TIMES):
    now = time.localtime()
    now_sec = now[3]*3600 + now[4]*60 + now[5]
    min_diff = None
    for h, m in times:
        target_sec = h*3600 + m*60
        diff = target_sec - now_sec
        if diff < 0:
            diff += 24*3600
        if min_diff is None or diff < min_diff:
            min_diff = diff
    return int(min_diff*1000)

# -----------------------------------------------------------
# State machine
# -----------------------------------------------------------
state = "idle"

def update_give_piller():
    global state, servo_state, servo_timer
    if state == "rotate":
        if steps_left == 0:
            lcd.clear()
            lcd.write("Tjekker kop...")
            state = "check_magnet"
        return
    if state == "check_magnet":
        if adc.read() >= 100:
            lcd.clear()
            lcd.write("Piller gives...")
            set_angle(170)
            servo_timer.set(60*1000)
            servo_state = "open"
            state = "wait_servo"
        else:
            lcd.clear()
            lcd.write("Husk koppen!")
            state = "finished"
        return
    if state == "wait_servo":
        if servo_timer.done():
            set_angle(0)
            state = "finished"
        return
    if state == "finished":
        lcd.clear()
        state = "idle"
        servo_state = "idle"

# -----------------------------------------------------------
# uasyncio tasks
# -----------------------------------------------------------
async def stepmotor_task():
    while True:
        update_stepmotor()
        await asyncio.sleep_ms(2)

async def servo_task():
    while True:
        update_give_piller()
        await asyncio.sleep_ms(50)

async def rfid_task():
    global state
    while True:
        status, tag_type = reader.request(reader.CARD_REQIDL)
        if status == reader.OK:
            status, uid = reader.anticoll()
            if status == reader.OK:
                print("RFID fundet:", uid)
                if uid in ALLOWED_UIDS:
                    lcd.clear()
                    lcd.write("RFID OK - Starter...")
                    write_json(uid)
                    start_rotate_24_deg(direction=1)
                    state = "rotate"
                else:
                    lcd.clear()
                    lcd.write("RFID AFVIST!")
                    print("Ukendt RFID:", uid)
        await asyncio.sleep_ms(100)

async def pir_task():
    while True:
        if pir.value():
            lcd.write("Bevægelse registreret")
        await asyncio.sleep_ms(100)

async def server_log_task():
    if not hasattr(update_give_piller, "last_log_time"):
        update_give_piller.last_log_time = time.ticks_ms()
    while True:
        if time.ticks_diff(time.ticks_ms(), update_give_piller.last_log_time) > 60*1000:
            data = {"magnet": adc.read(), "pir": pir.value()}
            safe_post(URL_SEND, {"Id": ID_VAR, "RF_log_time": data})
            update_give_piller.last_log_time = time.ticks_ms()
        await asyncio.sleep_ms(1000)

# -----------------------------------------------------------
# Main program
# -----------------------------------------------------------
try:
    ip = connect_wifi()
    server_data = safe_get(URL_GET)
    if server_data and isinstance(server_data, dict):
        TIMES = server_data.get("Tider", FALLBACK_TIMES)
        ID_VAR = server_data.get("Id", 0)
    else:
        TIMES = FALLBACK_TIMES
        ID_VAR = 0
except:
    TIMES = FALLBACK_TIMES
    ID_VAR = 0

lcd.write("Klar til pilledeling...")

next_pill_time = time.ticks_ms() + get_ms_until_next_target(TIMES)

async def scheduler_task():
    global state, next_pill_time
    while True:
        if time.ticks_ms() >= next_pill_time and state == "idle":
            start_rotate_24_deg(direction=1)
            state = "rotate"
            next_pill_time = time.ticks_ms() + get_ms_until_next_target(TIMES)
        await asyncio.sleep_ms(100)

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
