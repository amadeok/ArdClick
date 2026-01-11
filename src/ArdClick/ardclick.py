import math
import os, sys, time, argparse, serial, pyautogui, threading, random
import logging
from PIL import Image
import pytweening


import logging

# Get the PIL logger
pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.DEBUG)

pil_logger.propagate = True

log_to_file = False  # Change to True if you want file logging

if log_to_file:
    handler = logging.FileHandler('app.log', mode='w')
else:
    handler = logging.StreamHandler()  # Console

handler.setLevel(logging.DEBUG)  # Allow DEBUG messages through the handler
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure root accepts DEBUG

for h in logger.handlers[:]:
    logger.removeHandler(h)

logger.addHandler(handler)

mutexserial = threading.Lock()
mutexserial2 = threading.Lock()
# Optional: also reduce noise from other loggers if needed
# logging.getLogger('some.noisy.lib').setLevel(logging.WARNING)

write_string_code = 30001
write_string_byte_code = write_string_code.to_bytes(2, 'little', signed=False)
press_key_code = 30000
press_key_byte_code = press_key_code.to_bytes(2, 'little', signed=False)
pass_code = 30002
pass_byte_code = pass_code.to_bytes(2, 'little', signed=False)
write_string2_code =  30003
write_string2_byte_code = write_string2_code.to_bytes(2, 'little', signed=False)
mouse_move_code =  30004
mouse_move_byte_code = mouse_move_code.to_bytes(2, 'little', signed=False)
arduino_start_conn =  30005
arduino_start_conn_byte_code = arduino_start_conn.to_bytes(2, 'little', signed=False)
reset_arduino =  30006
reset_arduino_byte_code = reset_arduino.to_bytes(2, 'little', signed=False) 
#reset can be done by opening and closing serial with baud 1200
right_click =  30007
right_click_byte_code = right_click.to_bytes(2, 'little', signed=False)
left_click =  30009
left_click_byte_code = left_click.to_bytes(2, 'little', signed=False)
change_delay_between =  30008
change_delay_between_byte_code = change_delay_between.to_bytes(2, 'little', signed=False)
setBoardMode = 40009
panic_code = 40019
           
press_left_click  =40013
release_left_click = 40014
press_right_click=40015
release_right_click=40016
press_key_only= 40017
release_key_only = 40018

from enum import Enum

class key:
    LEFT_ALT = (b'\x82'+b'\x00', "left_alt")
    LEFT_GUI = (b'\x83'+b'\x00', "left_gui")
    RIGHT_GUI = (b'\x87'+b'\x00', "right_gui")
    ESC = (b'\xB1'+b'\x00', "esc")
    ENTER = (b'\xB0'+b'\x00', "enter")
    HOME = (b'\xD2'+b'\x00', "home")
    LEFT_CTRL = (b'\x80'+b'\x00', "left_ctrl")
    TAB = (b'\xB3'+b'\x00', "tab")
    SHIFT = (b'\x81'+b'\x00', "shift")
    m = (b'\x6D'+b'\x00', "m")
    i =(b'\x69'+b'\x00', "i")
    r = (b'\x72'+b'\x00', "r")
    t = (b'\x74'+b'\x00', "t")
    e = (b'\x65'+b'\x00', "e") 
    o = (b'\x6f'+b'\x00', "o") 
    p = (b'\x70'+b'\x00', "p") 
    a = (b'\x61'+b'\x00', "a") 
    d = (b'\x64'+b'\x00', "d") 
    w = (b'\x77'+b'\x00', "w") 
    s = (b'\x73'+b'\x00', "s") 
    c = (b'\x63'+b'\x00', "c")
    f = (b'\x66'+b'\x00', "f")  

    one = (b'\x31'+b'\x00', "1") 
    two = (b'\x32'+b'\x00', "2") 
    three = (b'\x33'+b'\x00', "3") 
    four = (b'\x34'+b'\x00', "4") 
    five = (b'\x35'+b'\x00', "5") 
    six = (b'\x36'+b'\x00', "6") 
    seven = (b'\x37'+b'\x00', "7") 
    eight = (b'\x38'+b'\x00', "8") 
    nine = (b'\x39'+b'\x00', "9") 
    zero = (b'\x30'+b'\x00', "0") 

    two = (b'\x32'+b'\x00', "two")

    CAPS_LOCK =(b'\xC1'+b'\x00', "caps lock key")
    SPACE = ( b'\x20' + b'\x00', "space")
    F5 = (b'\xC6' + b'\x00',	"F5")
    F1 = (b'\xC2' + b'\x00',	"F1")

    LWIN = (b'\x83' + b'\x00',	"LWIN")

def map_number(num, from_min, from_max, to_min, to_max):
    normalized_num = (num - from_min) / (from_max - from_min)
    mapped_num = normalized_num * (to_max - to_min) + to_min
    return mapped_num

class ardclick:
    class boardModeEnum(Enum):
        standard = 0
        mouseKeyboard = 1
    def __init__(self, reset_arduino=False, port=None, baudrate=115200, sl_int=(0.4, 0.7)):
        self.find_fun_timeout = 15
        self.prev_time = time.time()
        self.screen_res = pyautogui.size()
        self.default_region = [0, 0, self.screen_res.width, self.screen_res.height]
        self.stop_t = False
        self.ard = None
        self.reset_arduino = reset_arduino
        self.log = ""
        self.key = key()
        self.port = port
        self.baudrate = baudrate
        self.sl_int = sl_int
    
    def empty_read_buffer(self):
        count = 0
        empty_read =  b''
        n = 0
        fail = False
        while 1:
            #if self.ard.in_waiting:
            empty_read =  self.ard.read_all()
            n+=1
            if len(empty_read):
                logger.info(f"{count} TIMES: WARNING THERE WAS DATA IN THE BUFFER {len(empty_read)}")
                count+=1
                fail = True
            elif n > 10: 
                break
            time.sleep(0.06)
        return fail

    def init_arduino(self, ard_port):
        arduino_start_conn =  30005
        if self.ard and not self.ard.closed:
            self.ard.close()
        if self.reset_arduino: # reset can be done by opening and closing serial with baud 1200
            self.reboot_arduino(ard_port)
        else:
            self.ard = serial.Serial(port=ard_port, baudrate=self.baudrate, timeout=1000)
            logger.info(f"Found port {ard_port}")

        logger.info("arduino connection sucess")

        time.sleep(1)

        # fail = self.empty_read_buffer()
        # if fail:
        self.start_conn_fun(arduino_start_conn)

        logger.info("sent resolution to arduino")

    def start_conn_fun(self, arduino_start_conn):
        logger.info("sending arduino_start_conn code")

        self.serial_write(arduino_start_conn)
        self.serial_write(arduino_start_conn)

        screen_res = pyautogui.size()

        logger.info(f"sending w h {screen_res}"  )                                
        self.serial_write(screen_res.width)
        self.serial_write(screen_res.height)

       # if args.ard_com > -1:
       #     n = args.ard_com


    def reboot_arduino(self, ard_port):
        if self.ard and not self.ard.closed:
            self.ard.close()
        if 0:
            self.ard = serial.Serial(port=ard_port, baudrate=1200, timeout=5)
            self.ard.close()
            logger.info(f"Found port {ard_port}")
            time.sleep(3)
            # if self.serial_write(reset_arduino) == -1: raise Exception 
            # self.serial_write(reset_arduino)
            # self.ard.close()    
            logger.info("arduino connection sucess, it has been restarted, connecting to it again")
        else:
            self.ard = serial.Serial(port=ard_port, baudrate=9600, timeout=1000)
            logger.info(f"Found port {ard_port}")

            #self.serial_write(reset_arduino)
            for x in range(3):
                self.serial_write2(reset_arduino_byte_code)
            time.sleep(0.1)
            self.ard.close()
            #self.ard.flush()
            time.sleep(.5)
            
            #self.serial_write(reset_arduino)

        try_nb = 1
        while try_nb < 20:
            try:
                self.ard = serial.Serial(port=ard_port, baudrate=self.baudrate, timeout=1000)
                break
            except Exception as e:
                time.sleep(1)
                logger.info(f"attempting try nb {try_nb}")
                try_nb+=1
        logger.info("arduino rebooted")

    def search_port(self, func):
        n = 2
        if not self.port:
            while 1:
                if n == 5: 
                    n+=1
                    continue
                try:
                    ard_port = f'COM{n}'
                    #self.init_arduino(ard_port)
                    func(ard_port)
                    break
                except Exception as e: 
                    s = str(e)
                    if not "he system cannot find the file specified" in s:
                        logger.info(e)
                    n+=1
                #logger.info(e)
                    if n == 100:
                        logger.info("arduino port not found")
                        logger.info("arduino port not found")
                        sys.exit()
        else:
            func(self.port)
            
                    
    def init(self):
        self.search_port(self.init_arduino)

    def reboot(self):
        self.search_port(self.reboot_arduino)

    def deinit(self):
        self.ard.close()
        if self.ard.closed:
            logger.info("Connection is still open")
        else:
            logger.info("Connection closed")

    def change_delay_between(self, new_delay):
        self.serial_write(change_delay_between)
        self.serial_write(new_delay)
        logger.info(f"new delay set to {new_delay}")

    def panic(self):
        self.serial_write(panic_code)
        logger.info(f"Panic code sent to arduino")

    def serial_write2(self, bytes_):
        with mutexserial2:
            size = len(bytes_)
            data = b''

            ret = self.ard.write(bytes_)

            data += self.ard.read(ret)

            if data != bytes_:
                print("Warning serial bytes_:", bytes_, " data: ", data)
                logger.debug(f"Warning serial bytes_: {bytes_} data: {data}")
                return -1
                
    def serial_write(self, n):
        byt = int(n).to_bytes(2, 'little', signed=False)
        return self.serial_write2(byt)



    def write_mouse_coor(self, point, x_of=0, y_of=0):
        logger.debug(f"{self.log} moving mouse and click {point}, {x_of}, {y_of}") 
        with mutexserial:
            x = point[0]+ x_of 
            y = point[1]+ y_of
            self.serial_write(x)
            self.serial_write(y)

    def write_mouse_coor_new(self, point, x_of=0, y_of=0):
        logger.debug(f"{self.log} moving mouse and left click {point}, {x_of}, {y_of}") 
        with mutexserial:
            x = point[0]+ x_of
            y = point[1]+ y_of
            self.serial_write2(left_click_byte_code)
            self.serial_write2(left_click_byte_code)
            self.serial_write(x)
            self.serial_write(y)
            ret = self.ard.read(1)
            assert(ret == b'c')

    def write_mouse_coor_right(self, point, x_of = 0, y_of = 0):
        logger.debug(f"{self.log} moving mouse and right click {point}, {x_of}, {y_of}") 
        with mutexserial:
            x = point[0]+ x_of
            y = point[1]+ y_of
            self.serial_write2(right_click_byte_code)
            self.serial_write2(right_click_byte_code)
            self.serial_write(x)
            self.serial_write(y)
            ret = self.ard.read(1)
            assert(ret == b'c')
            
    def write_custom(self, custom_code, values):
        #logger.debug(f"{self.log} sending custom command {custom_code}, {values}") 
        with mutexserial:
            self.serial_write(custom_code)
            self.serial_write(custom_code)
            for value in values:
                self.serial_write(value)
                
    def left_click_only(self, x, y):
        self.write_custom(press_left_click, [x, y])
        
    def left_release_only(self, x, y):
        self.write_custom(release_left_click, [x, y])
        
    def right_click_only(self, x, y):
        self.write_custom(press_right_click, [x, y])
        
    def right_release_only(self, x, y):
        self.write_custom(release_right_click, [x, y]) 
        
    def press_key_only(self, key):
        self.write_custom(press_key_only, [ int.from_bytes(key[0], byteorder='little')  ])
    
    def release_key_only(self, key):
        self.write_custom(release_key_only, [int.from_bytes(key[0], byteorder='little') ])     
    
    def press_key_2(self, key, int=None):
        self.press_key_only(key)
        if int:
            lsp = int if isinstance(int, float) else random.uniform(*int)
        else:
            lsp = random.uniform(*self.sl_int)
        time.sleep(lsp)
        self.release_key_only(key)

    def mouse_move(self, point, x_of=0, y_of=0, print=1):
        if print:
            logger.debug(f"{self.log} moving mouse {point}, {x_of}, {y_of}") 
        with mutexserial:
            x = point[0]+ x_of
            y = point[1]+ y_of
            self.serial_write2(mouse_move_byte_code)
            self.serial_write2(mouse_move_byte_code)
            self.serial_write(x)
            self.serial_write(y)

    def serial_write_string(self, string):
        with mutexserial:
            data = b''
            ret = self.ard.write(string)
            #for x in range(size):
            data = self.ard.read_until().decode("UTF-8")
            data = data[:ret]
            if data != string.decode("UTF-8"):
                print("Warning serial string:", string, " data: ", data)
                logger.debug(f"Warning serial string: {string} data: {data}")
                

    def write_string(self, string, c):
        logger.debug(f"{self.log} writing string {string}") 
        if c:  byte_code = write_string2_byte_code
        else: byte_code = write_string_byte_code
        #with mutex:
        self.serial_write2(byte_code)
        time.sleep(0.1)
        self.serial_write2(byte_code)
        time.sleep(0.1)
        byte_string = string.encode("UTF-8")
        self.serial_write_string(byte_string)
        time.sleep(0.1)


    def press_key(self, key):
        logger.debug(f"{self.log} pressing key {key[1]}") 
        with mutexserial:
            self.serial_write2(press_key_byte_code)
            time.sleep(0.1)
            
            self.serial_write2(key[0])
            time.sleep(0.1)
            
    def set_board_mode(self, val):
        self.write_custom(setBoardMode, [val])
        
        
    def ease_in_out_quad(self, t):
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - math.pow(-2 * t + 2, 2) / 2

    def map_number(self, value, from_min, from_max, to_min, to_max):
        return (value - from_min) / (from_max - from_min) * (to_max - to_min) + to_min

    def move_mouse_s(self, target, x_of=0, y_of=0, start=None, duration=None, randomness=10,
                    recursive=True, end_randomness=1, right_click=False, no_click=False, random_sleep=0, ease_func=lambda v:v ):
        
        def apply_randomness(integer, randomness):
            return random.randint(integer - randomness, integer + randomness)
        
        start_x, start_y = start if start else pyautogui.position()
        if len(target) > 2:
            target = target[:2]
        end_x, end_y = [apply_randomness(int(e), end_randomness) for e in target]
        end_x += int(x_of)
        end_y += int(y_of)

        # Auto-calculate duration
        if duration is None:
            distance = math.hypot(end_x - start_x, end_y - start_y)
            duration = self.map_number(distance, 0, 2202, 0.15, 0.65)

        num_steps = max(1, int(duration * 100))
        
        ease_func_ =  getattr(pytweening, ease_func) if type(ease_func) == str else ease_func
        
        for i in range(num_steps + 1):
            t = i / num_steps  # t ∈ [0, 1]
            
            eased_t = ease_func_(t)  # <-- Using pytweening!

            # Interpolated position with easing
            x = start_x + (end_x - start_x) * eased_t
            y = start_y + (end_y - start_y) * eased_t

            # Reduce randomness as we approach the target
            current_randomness = randomness * (1.0 - t)
            x += random.uniform(-current_randomness, current_randomness)
            y += random.uniform(-current_randomness, current_randomness)

            # Optional micro-pause
            if random_sleep and random.randrange(100) < random_sleep:
                time.sleep(random.uniform(0.01, 0.04))

            self.mouse_move([max(0, int(x)), max(0, int(y))], print=False)
            
        for x in range(2):
            self.mouse_move((end_x, end_y))
            pos = pyautogui.position()
            logger.debug(pos)
        #logger.info(f"dur {duration} steps {num_steps}")
        if not no_click:
            if not right_click:
                self.write_mouse_coor_new((end_x, end_y))
            else:
                self.write_mouse_coor_right((end_x, end_y))
            
    def move_mouse_s_old(self, target, x_of=0, y_of= 0, start=None, duration=None, randomness=10,
                     recursive=True, end_randomness=1, right_click=False, no_click=False, random_sleep=0):

        for i in range(num_steps):
            perc = (((num_steps-i))/num_steps) *2
            randomness_ =  randomness*min(perc, 1) 
            x = start_x + step_x * i + random.uniform(-randomness_, randomness_)
            y = start_y + step_y * i + random.uniform(-randomness_, randomness_)
            if random_sleep and random.randrange(0, 100) < random_sleep:
                time.sleep(random.uniform(0.01, 0.04))
            self.mouse_move([max(0,int(x)), max(0,int(y))], print=False)


        
if __name__ == "__main__":

    a = ardclick(reset_arduino=1, port="COM7")
    print(a.ard)
    a.init()
    print(a.ard)
    a.change_delay_between(100)
    
    a.set_board_mode(a.boardModeEnum.mouseKeyboard.value)
    # a.change_delay_between(50) #250ms for click
    
    # a.mouse_move((2000 , 2000))
    a.write_mouse_coor_new((1000, 1000))
    a.panic()
    time.sleep(1)
    # a.write_string("hello", False)

    #                 a.press_key(key.m)
    
    for x in range(1000):
        pos = pyautogui.position()
        a.left_click_only(pos.x, pos.y)
        a.press_key_only(key.SPACE)
        print(x)
        time.sleep(1)        
        pos = pyautogui.position()
        a.left_release_only(pos.x, pos.y)
        a.release_key_only(key.SPACE)                 
        time.sleep(1)




                                                   
                 

