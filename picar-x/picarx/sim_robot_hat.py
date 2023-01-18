# ****************************** From filedb.py ****************************
import os
from time import sleep


class fileDB(object):
    """A file based database.

    A file based database, read and write arguements in the specific file.
    """

    def __init__(self, db: str, mode: str = None, owner: str = None):
        '''Init the db_file is a file to save the datas.'''

        self.db = db
        # Check if db_file is existed, otherwise create one
        if self.db != None:
            self.file_check_create(db, mode, owner)
        else:
            raise ValueError('db: Missing file path parameter.')

    def file_check_create(self, file_path: str, mode: str = None, owner: str = None):
        dir = file_path.rsplit('/', 1)[0]
        try:
            if os.path.exists(file_path):
                if not os.path.isfile(file_path):
                    print('Could not create file, there is a folder with the same name')
                    return
            else:
                if os.path.exists(dir):
                    if not os.path.isdir(dir):
                        print('Could not create directory, there is a file with the same name')
                        return
                else:
                    os.makedirs(file_path.rsplit('/', 1)[0], mode=0o754)
                    sleep(0.001)

                with open(file_path, 'w') as f:
                    f.write("# robot-hat config and calibration value of robots\n\n")

            if mode != None:
                os.popen('sudo chmod %s %s' % (mode, file_path))
            if owner != None:
                os.popen('sudo chown -R %s:%s %s' % (owner, owner, file_path.rsplit('/', 1)[0]))
        except Exception as e:
            raise (e)

    def get(self, name, default_value=None):
        """Get value by data's name. Default value is for the arguemants do not exist"""
        try:
            conf = open(self.db, 'r')
            lines = conf.readlines()
            conf.close()
            file_len = len(lines) - 1
            flag = False
            # Find the arguement and set the value
            for i in range(file_len):
                if lines[i][0] != '#':
                    if lines[i].split('=')[0].strip() == name:
                        value = lines[i].split('=')[1].replace(' ', '').strip()
                        flag = True
            if flag:
                return value
            else:
                return default_value
        except FileNotFoundError:
            conf = open(self.db, 'w')
            conf.write("")
            conf.close()
            return default_value
        except:
            return default_value

    def set(self, name, value):
        """Set value by data's name. Or create one if the arguement does not exist"""

        # Read the file
        conf = open(self.db, 'r')
        lines = conf.readlines()
        conf.close()
        file_len = len(lines) - 1
        flag = False
        # Find the arguement and set the value
        for i in range(file_len):
            if lines[i][0] != '#':
                if lines[i].split('=')[0].strip() == name:
                    lines[i] = '%s = %s\n' % (name, value)
                    flag = True
        # If arguement does not exist, create one
        if not flag:
            lines.append('%s = %s\n\n' % (name, value))

        # Save the file
        conf = open(self.db, 'w')
        conf.writelines(lines)
        conf.close()


# ****************************** From basic.py *****************************
import logging


class _Basic_class(object):
    _class_name = '_Basic_class'
    DEBUG_LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL,
              }
    DEBUG_NAMES = ['critical', 'error', 'warning', 'info', 'debug']

    def __init__(self):
        self._debug_level = 0
        self.logger = logging.getLogger(self._class_name)
        self.ch = logging.StreamHandler()
        form = "%(asctime)s	[%(levelname)s]	%(message)s"
        self.formatter = logging.Formatter(form)
        self.ch.setFormatter(self.formatter)
        self.logger.addHandler(self.ch)
        self._debug    = self.logger.debug
        self._info     = self.logger.info
        self._warning  = self.logger.warning
        self._error    = self.logger.error
        self._critical = self.logger.critical

    @property
    def debug(self):
        return self._debug_level

    @debug.setter
    def debug(self, debug):
        if debug in range(5):
            self._debug_level = self.DEBUG_NAMES[debug]
        elif debug in self.DEBUG_NAMES:
            self._debug_level = debug
        else:
            raise ValueError('Debug value must be 0(critical), 1(error), 2(warning), 3(info) or 4(debug), not \"{0}\".'.format(debug))
        self.logger.setLevel(self.DEBUG_LEVELS[self._debug_level])
        self.ch.setLevel(self.DEBUG_LEVELS[self._debug_level])
        self._debug('Set logging level to [%s]' % self._debug_level)

    def run_command(self, cmd):
        import subprocess
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = p.stdout.read().decode('utf-8')
        status = p.poll()
        # print(result)
        # print(status)
        return status, result

    def map(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


# ***************************** From servo.py ******************************
import time


class Servo(_Basic_class):
    MAX_PW = 2500
    MIN_PW = 500
    _freq = 50
    def __init__(self, pwm):
        super().__init__()
        self.pwm = pwm
        self.pwm.period(4095)
        prescaler = int(float(self.pwm.CLOCK) /self.pwm._freq/self.pwm.period())
        self.pwm.prescaler(prescaler)
        # self.angle(90)

    # angle ranges -90 to 90 degrees
    def angle(self, angle):
        if not (isinstance(angle, int) or isinstance(angle, float)):
            raise ValueError("Angle value should be int or float value, not %s"%type(angle))
        if angle < -90:
            angle = -90
        if angle > 90:
            angle = 90
        High_level_time = self.map(angle, -90, 90, self.MIN_PW, self.MAX_PW)
        self._debug("High_level_time: %f" % High_level_time)
        pwr =  High_level_time / 20000
        self._debug("pulse width rate: %f" % pwr)
        value = int(pwr*self.pwm.period())
        self._debug("pulse width value: %d" % value)
        self.pwm.pulse_width(value)

    # pwm_value ranges MIN_PW 500 to MAX_PW 2500 degrees
    def set_pwm(self,pwm_value):
        if pwm_value > self.MAX_PW:
            pwm_value =  self.MAX_PW
        if pwm_value < self.MIN_PW:
            pwm_value = self.MIN_PW

        self.pwm.pulse_width(pwm_value)


# ****************************** From i2c.py ********************************
# from .basic import _Basic_class
import smbus
from smbus import SMBus


def _retry_wrapper(func):
    def wrapper(self, *arg, **kwargs):
        for i in range(self.RETRY):
            try:
                return func(self, *arg, **kwargs)
            except OSError:
                self._debug("OSError: %s" % func.__name__)
                continue
        else:
            return False
    return wrapper


class I2C(_Basic_class):
    MASTER = 0
    SLAVE = 1
    RETRY = 5

    def __init__(self, *args, **kargs):  # *args表示位置参数（形式参数），可无，； **kargs表示默认值参数，可无。
        super().__init__()
        self._bus = 1
        self._smbus = SMBus(self._bus)

    @_retry_wrapper
    def _i2c_write_byte(self, addr, data):  # i2C 写系列函数
        self._debug("_i2c_write_byte: [0x{:02X}] [0x{:02X}]".format(addr, data))
        result = self._smbus.write_byte(addr, data)
        return result

    @_retry_wrapper
    def _i2c_write_byte_data(self, addr, reg, data):
        self._debug("_i2c_write_byte_data: [0x{:02X}] [0x{:02X}] [0x{:02X}]".format(addr, reg, data))
        return self._smbus.write_byte_data(addr, reg, data)

    @_retry_wrapper
    def _i2c_write_word_data(self, addr, reg, data):
        self._debug("_i2c_write_word_data: [0x{:02X}] [0x{:02X}] [0x{:04X}]".format(addr, reg, data))
        return self._smbus.write_word_data(addr, reg, data)

    @_retry_wrapper
    def _i2c_write_i2c_block_data(self, addr, reg, data):
        self._debug("_i2c_write_i2c_block_data: [0x{:02X}] [0x{:02X}] {}".format(addr, reg, data))
        return self._smbus.write_i2c_block_data(addr, reg, data)

    @_retry_wrapper
    def _i2c_read_byte(self, addr):  # i2C 读系列函数
        self._debug("_i2c_read_byte: [0x{:02X}]".format(addr))
        return self._smbus.read_byte(addr)

    @_retry_wrapper
    def _i2c_read_i2c_block_data(self, addr, reg, num):
        self._debug("_i2c_read_i2c_block_data: [0x{:02X}] [0x{:02X}] [{}]".format(addr, reg, num))
        return self._smbus.read_i2c_block_data(addr, reg, num)

    @_retry_wrapper
    def is_ready(self, addr):
        addresses = self.scan()
        if addr in addresses:
            return True
        else:
            return False

    def scan(self):  # 查看有哪些i2c设备
        cmd = "i2cdetect -y %s" % self._bus
        _, output = self.run_command(cmd)  # 调用basic中的方法，在linux中运行cmd指令，并返回运行后的内容

        outputs = output.split('\n')[1:]  # 以回车符为分隔符，分割第二行之后的所有行
        self._debug("outputs")
        addresses = []
        for tmp_addresses in outputs:
            if tmp_addresses == "":
                continue
            tmp_addresses = tmp_addresses.split(':')[1]
            tmp_addresses = tmp_addresses.strip().split(' ')  # strip函数是删除字符串两端的字符，split函数是分隔符
            for address in tmp_addresses:
                if address != '--':
                    addresses.append(int(address, 16))
        self._debug("Conneceted i2c device: %s" % addresses)  # append以列表的方式添加address到addresses中
        return addresses

    def send(self, send, addr, timeout=0):  # 发送数据，addr为从机地址，send为数据
        if isinstance(send, bytearray):
            data_all = list(send)
        elif isinstance(send, int):
            data_all = []
            d = "{:X}".format(send)
            d = "{}{}".format("0" if len(d) % 2 == 1 else "",
                              d)  # format是将()中的内容对应填入{}中，（）中的第一个参数是一个三目运算符，if条件成立则为“0”，不成立则为“”(空的意思)，第二个参数是d，此行代码意思为，当字符串为奇数位时，在字符串最强面添加‘0’，否则，不添加， 方便以下函数的应用
            # print(d)
            for i in range(len(d) - 2, -1, -2):  # 从字符串最后开始取，每次取2位
                tmp = int(d[i:i + 2], 16)  # 将两位字符转化为16进制
                # print(tmp)
                data_all.append(tmp)  # 添加到data_all数组中
            data_all.reverse()
        elif isinstance(send, list):
            data_all = send
        else:
            raise ValueError("send data must be int, list, or bytearray, not {}".format(type(send)))

        if len(data_all) == 1:  # 如果data_all只有一组数
            data = data_all[0]
            # print("i2c write: [0x%02X] to 0x%02X"%(data, addr))
            self._i2c_write_byte(addr, data)
        elif len(data_all) == 2:  # 如果data_all只有两组数
            reg = data_all[0]
            data = data_all[1]
            self._i2c_write_byte_data(addr, reg, data)
        elif len(data_all) == 3:  # 如果data_all只有三组数
            reg = data_all[0]
            data = (data_all[2] << 8) + data_all[1]
            self._i2c_write_word_data(addr, reg, data)
        else:
            reg = data_all[0]
            data = list(data_all[1:])
            self._i2c_write_i2c_block_data(addr, reg, data)

    def recv(self, recv, addr=0x00, timeout=0):  # 接收数据
        if isinstance(recv, int):  # 将recv转化为二进制数
            result = bytearray(recv)
        elif isinstance(recv, bytearray):
            result = recv
        else:
            return False
        for i in range(len(result)):
            result[i] = self._i2c_read_byte(addr)
        return result

    def mem_write(self, data, addr, memaddr, timeout=5000, addr_size=8):  # memaddr match to chn
        if isinstance(data, bytearray):
            data_all = list(data)
        elif isinstance(data, list):
            data_all = data
        elif isinstance(data, int):
            data_all = []
            data = "%x" % data
            if len(data) % 2 == 1:
                data = "0" + data
            # print(data)
            for i in range(0, len(data), 2):
                # print(data[i:i+2])
                data_all.append(int(data[i:i + 2], 16))
        else:
            raise ValueError("memery write require arguement of bytearray, list, int less than 0xFF")
        # print(data_all)
        self._i2c_write_i2c_block_data(addr, memaddr, data_all)

    @_retry_wrapper
    def mem_read(self, data, addr, memaddr, timeout=5000, addr_size=8):  # 读取数据
        if isinstance(data, int):
            num = data
        elif isinstance(data, bytearray):
            num = len(data)
        else:
            return False
        result = bytearray(self._i2c_read_i2c_block_data(addr, memaddr, num))
        return result

    def readfrom_mem_into(self, addr, memaddr, buf):
        buf = self.mem_read(len(buf), addr, memaddr)
        return buf

    def writeto_mem(self, addr, memaddr, data):
        self.mem_write(data, addr, memaddr)


# ***************************** From pwm.py **********************************
import smbus, math
# from .i2c import I2C

timer = [
    {
        "arr": 0
    }
] * 4


class PWM(I2C):
    REG_CHN = 0x20
    REG_FRE = 0x30
    REG_PSC = 0x40
    REG_ARR = 0x44

    ADDR = 0x14

    CLOCK = 72000000

    def __init__(self, channel, debug="critical"):
        super().__init__()
        if isinstance(channel, str):
            if channel.startswith("P"):
                channel = int(channel[1:])
                if channel > 14:
                    raise ValueError("channel must be in range of 0-14")
            else:
                raise ValueError("PWM channel should be between [P0, P11], not {0}".format(channel))
        try:
            self.send(0x2C, self.ADDR)
            self.send(0, self.ADDR)
            self.send(0, self.ADDR)
        except IOError:
            self.ADDR = 0x15

        self.debug = debug
        self._debug("PWM address: {:02X}".format(self.ADDR))
        self.channel = channel
        self.timer = int(channel/4)
        self.bus = smbus.SMBus(1)
        self._pulse_width = 0
        self._freq = 50
        self.freq(50)

    def i2c_write(self, reg, value):
        value_h = value >> 8
        value_l = value & 0xff
        self._debug("i2c write: [0x%02X, 0x%02X, 0x%02X, 0x%02X]"%(self.ADDR, reg, value_h, value_l))
        # print("i2c write: [0x%02X, 0x%02X, 0x%02X] to 0x%02X"%(reg, value_h, value_l, self.ADDR))
        self.send([reg, value_h, value_l], self.ADDR)

    def freq(self, *freq):
        if len(freq) == 0:
            return self._freq
        else:
            self._freq = int(freq[0])
            # [prescaler,arr] list
            result_ap = []
            # accuracy list
            result_acy = []
            # middle value for equal arr prescaler
            st = int(math.sqrt(self.CLOCK/self._freq))
            # get -5 value as start
            st -= 5
            # prevent negetive value
            if st <= 0:
                st = 1
            for psc in range(st,st+10):
                arr = int(self.CLOCK/self._freq/psc)
                result_ap.append([psc, arr])
                result_acy.append(abs(self._freq-self.CLOCK/psc/arr))
            i = result_acy.index(min(result_acy))
            psc = result_ap[i][0]
            arr = result_ap[i][1]
            self._debug("prescaler: %s, period: %s"%(psc, arr))
            self.prescaler(psc)
            self.period(arr)

    def prescaler(self, *prescaler):
        if len(prescaler) == 0:
            return self._prescaler
        else:
            self._prescaler = int(prescaler[0]) - 1
            reg = self.REG_PSC + self.timer
            self._debug("Set prescaler to: %s"%self._prescaler)
            self.i2c_write(reg, self._prescaler)

    def period(self, *arr):
        global timer
        if len(arr) == 0:
            return timer[self.timer]["arr"]
        else:
            timer[self.timer]["arr"] = int(arr[0]) - 1
            reg = self.REG_ARR + self.timer
            self._debug("Set arr to: %s"%timer[self.timer]["arr"])
            self.i2c_write(reg, timer[self.timer]["arr"])

    def pulse_width(self, *pulse_width):
        if len(pulse_width) == 0:
            return self._pulse_width
        else:
            self._pulse_width = int(pulse_width[0])
            reg = self.REG_CHN + self.channel
            self.i2c_write(reg, self._pulse_width)

    def pulse_width_percent(self, *pulse_width_percent):
        global timer
        if len(pulse_width_percent) == 0:
            return self._pulse_width_percent
        else:
            self._pulse_width_percent = pulse_width_percent[0]
            temp = self._pulse_width_percent / 100.0
            # print(temp)
            pulse_width = temp * timer[self.timer]["arr"]
            self.pulse_width(pulse_width)