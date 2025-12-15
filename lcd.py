from machine import Pin
from time import sleep_ms

class LCD:
    def __init__(self, rs, e, d4, d5, d6, d7, bl=None):
        self.rs = Pin(rs, Pin.OUT)
        self.e = Pin(e, Pin.OUT)
        self.data = [Pin(d4, Pin.OUT), Pin(d5, Pin.OUT),
                     Pin(d6, Pin.OUT), Pin(d7, Pin.OUT)]
        self.bl = Pin(bl, Pin.OUT) if bl is not None else None

        self.init_lcd()

    def pulse(self):
        self.e.value(1)
        sleep_ms(1)
        self.e.value(0)
        sleep_ms(1)

    def send_nibble(self, nibble):
        for i in range(4):
            self.data[i].value((nibble >> i) & 1)
        self.pulse()

    def send_byte(self, value, rs):
        self.rs.value(rs)
        self.send_nibble(value >> 4)  # high nibble
        self.send_nibble(value & 0x0F)  # low nibble
        sleep_ms(2)

    def command(self, cmd):
        self.send_byte(cmd, 0)

    def write_char(self, char):
        self.send_byte(ord(char), 1)

    def init_lcd(self):
        sleep_ms(50)
        self.send_nibble(0x03)
        sleep_ms(5)
        self.send_nibble(0x03)
        sleep_ms(1)
        self.send_nibble(0x03)
        self.send_nibble(0x02)  # 4-bit mode
        self.command(0x28)      # 2 lines, 5x8 font
        self.command(0x0C)      # Display on, cursor off
        self.command(0x06)      # Entry mode, increment
        self.clear()

    def clear(self):
        self.command(0x01)
        sleep_ms(2)

    def home(self):
        self.command(0x02)
        sleep_ms(2)

    def write(self, text):
        row = 0
        col = 0
        for c in text:
            if c == '\n':
                row += 1
                col = 0
                self.command(0x80 + 0x40 * row)  # Move cursor to next line
            else:
                self.write_char(c)
                col += 1

