import os, sys, time, argparse, serial, pyautogui, threading
import logging
from PIL import Image


pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.DEBUG)
log_to_file = False

if log_to_file:
    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(message)s', level=level)
else: 
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
    
mutexserial = threading.Lock()
mutexserial2 = threading.Lock()

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
# reset_arduino =  30006
# reset_arduino_byte_code = mouse_move_code.to_bytes(2, 'little', signed=False) 
# reset can be done by opening and closing serial with baud 1200
right_click =  30007
right_click_byte_code = right_click.to_bytes(2, 'little', signed=False)
change_delay_between =  30008
change_delay_between_byte_code = change_delay_between.to_bytes(2, 'little', signed=False)

class key:
    LEFT_GUI = (b'\x83'+b'\x00', "left_gui")
    RIGHT_GUI = (b'\x87'+b'\x00', "right_gui")
    ESC = (b'\xB1'+b'\x00', "esc")
    ENTER = (b'\xB0'+b'\x00', "enter")
    HOME = (b'\xD2'+b'\x00', "home")
    LEFT_CTRL = (b'\x80'+b'\x00', "left_ctrl")
    TAB = (b'\xB3'+b'\x00', "tab")
    m = (b'\x6D'+b'\x00', "m")
    i =(b'\x69'+b'\x00', "i")
    CAPS_LOCK =(b'\xC1'+b'\x00', "caps lock key")


class ardclick:
    def __init__(self, reset_arduino=False):
        self.find_fun_timeout = 15
        self.prev_time = time.time()
        self.screen_res = pyautogui.size()
        self.default_region = [0, 0, self.screen_res.width, self.screen_res.height]
        self.stop_t = False
        self.ard = None
        self.reset_arduino = reset_arduino
        self.log = ""
        self.key = key()
    
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
                print(f"{count} TIMES: WARNING THERE WAS DATA IN THE BUFFER {len(empty_read)}")
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
            self.ard = serial.Serial(port=ard_port, baudrate=115200, timeout=1000)
            logging.info(f"Found port {ard_port}")

        print("arduino connection sucess")

        time.sleep(1)

        # fail = self.empty_read_buffer()
        # if fail:
        self.start_conn_fun(arduino_start_conn)

        print("sent resolution to arduino")

    def start_conn_fun(self, arduino_start_conn):
        print("sending arduino_start_conn code")

        self.serial_write(arduino_start_conn)
        self.serial_write(arduino_start_conn)

        screen_res = pyautogui.size()

        print("sending w h")
        self.serial_write(screen_res.width)
        self.serial_write(screen_res.height)

       # if args.ard_com > -1:
       #     n = args.ard_com


    def reboot_arduino(self, ard_port):
        if self.ard and not self.ard.closed:
            self.ard.close()
        self.ard = serial.Serial(port=ard_port, baudrate=1200, timeout=5)
        self.ard.close()
        logging.info(f"Found port {ard_port}")
        time.sleep(3)
        # if self.serial_write(reset_arduino) == -1: raise Exception 
        # self.serial_write(reset_arduino)
        # self.ard.close()    
        print("arduino connection sucess, it has been restarted, connecting to it again")

        try_nb = 1
        while try_nb < 20:
            try:
                self.ard = serial.Serial(port=ard_port, baudrate=115200, timeout=1000)
                break
            except:
                time.sleep(1)
                print("attempting try nb ", try_nb)
                try_nb+=1
        print("arduino rebooted")

    def search_port(self, func):
        n = 0
        while 1:
            try:
                ard_port = f'COM{n}'
                #self.init_arduino(ard_port)
                func(ard_port)
                break
            except Exception as e: 
                s = str(e)
                if not "he system cannot find the file specified" in s:
                    print(e)
                n+=1
            #print(e)
                if n == 100:
                    logging.info("arduino port not found")
                    print("arduino port not found")
                    sys.exit()
                    
    def init(self):
        self.search_port(self.init_arduino)

    def reboot(self):
        self.search_port(self.reboot_arduino)



    def change_delay_between(self, new_delay):
        self.serial_write(change_delay_between)
        self.serial_write(new_delay)
        logging.info(f"new delay set to {new_delay}")

        

    def serial_write2(self, bytes_):
        with mutexserial2:
            size = len(bytes_)
            data = b''

            ret = self.ard.write(bytes_)

            data += self.ard.read(ret)

            if data != bytes_:
                print("Warning serial bytes_:", bytes_, " data: ", data)
                logging.debug(f"Warning serial bytes_: {bytes_} data: {data}")
                return -1
                
    def serial_write(self, n):
        byt = int(n).to_bytes(2, 'little', signed=False)
        return self.serial_write2(byt)



    def write_mouse_coor(self, point, x_of=0, y_of=0):
        logging.debug(f"{self.log} moving mouse and click {point}, {x_of}, {y_of}") 
        with mutexserial:
            x = point[0]+ x_of 
            y = point[1]+ y_of
            self.serial_write(x)
            self.serial_write(y)


    def write_mouse_coor_right(self, point, x_of = 0, y_of = 0):
        logging.debug(f"{self.log} moving mouse and click {point}, {x_of}, {y_of}") 
        with mutexserial:
            x = point[0]+ x_of
            y = point[1]+ y_of
            self.serial_write2(right_click_byte_code)
            self.serial_write2(right_click_byte_code)
            self.serial_write(x)
            self.serial_write(y)
            
    def write_custom(self, custom_code, values):
        logging.debug(f"{self.log} sending custom command {custom_code}, {values}") 
        with mutexserial:
            self.serial_write(custom_code)
            self.serial_write(custom_code)
            for value in values:
                self.serial_write(value)

    def mouse_move(self, point, x_of=0, y_of=0):
        logging.debug(f"{self.log} moving mouse {point}, {x_of}, {y_of}") 
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
                logging.debug(f"Warning serial string: {string} data: {data}")
                

    def write_string(self, string, c):
        logging.debug(f"{self.log} writing string {string}") 
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
        logging.debug(f"{self.log} pressing key {key[1]}") 
        with mutexserial:
            self.serial_write2(press_key_byte_code)
            time.sleep(0.1)
            
            self.serial_write2(key[0])
            time.sleep(0.1)

# a = ardclick()
# print(a.ard)
# a.init()
# print(a.ard)
# a.change_delay_between(100)

# a.mouse_move((1000 , 100))
# a.write_mouse_coor((1000, 1000))

# a.write_string("hello", False)

# a.press_key(key.m)