import RPi.GPIO as GPIO
import time
import serial
import re

lora_rx = False

#
#               GPIO PINOUT
#
# GMX               SLOT #0             SLOT# 1
# GMX_Reset         GPIO 5              GPIO 6
# GMX_GPIO_1        GPIO 23             GPIO 21
# GMX_GPIO_2        GPIO 24             GPIO 16
# GMX_GPIO_3        GPIO 25             GPIO 12
# GMX_GPIO_4        GPIO 18             GPIO 19
# GMX_GPIO_5        GPIO 22             GPIO 26
# GMX_GPIO_6/BOOT0  GPIO 13             GPIO 13
# GMX_I2C_SCL       SCL1 (GPIO 02)      SCL1 (GPIO 02)
# GMX_I2C_SDA       SDA1 (GPIO 03)      SDA1 (GPIO 03)
# GMX_SPI_MISO      SPI_MISO (GPIO 09)  SPI_MISO (GPIO 09)
# GMX_SPI_MOSI      SPI_MOSI (GPIO10)   SPI_MOSI (GPIO10)
# GMX_SPI_CLK       SPI_CLK (GPIO11)    SPI_CLK (GPIO11)
# GMX_SPI_CS        SPI_CE0_N (GPIO 08) SPI_CE1_N (GPIO 07)
# GMX_gmxINT        GPIO 20             GPIO 27
#
#



print "Booting GMX-LR1..."

#Init GPIO's
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Reset PIN for GMX Slot #1
#  - for Slor #2 pin is 6
GPIO.setup(5, GPIO.OUT)  # Slot 0

# RX Interrupt PIN
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Cycle the Reset
GPIO.output(5,0)
time.sleep( .1 )
GPIO.output(5,1)

#wait for reboot
time.sleep(2)

# GMX STATUS Defines
GMX_OK = 0
GMX_ERROR = -1
GMX_UKNOWN_ERROR = -2

print "Ready."

# Use /dev/ttySC0 o /dev/ttySC1
# For LoRaWAN we are using slot 0
port = serial.Serial("/dev/ttySC0",  baudrate=9600)

def _sendCmd(command):
    port.reset_input_buffer()  # flush any pending data
    port.write(command)
    return

def _parseResponse():
    time.sleep(0.2)
    response = ""

    response = port.read(4)  # start reading
    response += port.read(port.in_waiting)

    matchOk = re.match(r"((.|\n)*)\r\nOK",response)

    if matchOk:
        response = matchOk.group(1)
        # not very eleganto
        matchOk2 = re.match(r"((.|\n)*)\r\n",response)
        if matchOk2:
            response = matchOk2.group(1)
        return GMX_OK,response

    matchError = re.match("((.|\n)*)\r\n(.*)ERRROR", response);
    if matchOk:
        print matchError.group()
        return GMX_ERROR,response

    return GMX_UKNOWN_ERROR,response

def _rx_callback(channel):
    global  lora_rx
    lora_rx = True;

# add RX interrupt handling
GPIO.add_event_detect(20, GPIO.FALLING, callback=_rx_callback)

# Query the Module
response = ""
_sendCmd("AT+DEUI=?\r\n")
status,response = _parseResponse()
print "DevEUI:"+response

_sendCmd("AT+APPEUI=?\r\n")
status,response = _parseResponse()
print "AppEUI:"+response

_sendCmd("AT+APPKEY=?\r\n")
status,response = _parseResponse()
print "AppKey:"+response

_sendCmd("AT+VER=?\r\n")
status,response = _parseResponse()
print "Version:"+response

print "\nJoining..."

# Now we try to Join
join_status = 0
join_wait = 0
while join_status == 0:

    if join_wait == 0:
        # Disable DutyCycle
        _sendCmd("AT+DCS=0\r\n")
        _parseResponse()
        # Set Class C
        _sendCmd("AT+CLASS=C\r\n")
        _parseResponse()

        # Join
        _sendCmd("AT+JOIN\r\n")
        _parseResponse()

    print "Join Attempt:"+str(join_wait)
    join_wait+=1
    time.sleep(5)

    #check id Network Joined
    _sendCmd("AT+NJS=?\r")
    status, response = _parseResponse()
    join_status = int(response)


# Joined - we start application

print "Joined!!!"

last_lora_tx_time = time.time()
time_interval_tx = 20

# main loop testing
print "Starting LoRa TX Loop - TX every "+str(time_interval_tx)+" seconds"
while True:
    delta_lora_tx = time.time() - last_lora_tx_time

    if ( delta_lora_tx > time_interval_tx ):
        print "LoRa TX!"
        # TX Data
        _sendCmd("AT+SENDB=1:010203\r\n")
        _parseResponse()

        last_lora_tx_time = time.time()

    if (lora_rx):
        print "LoRa RX!"
        time.sleep(0.2)  #small delay due to interrupt being faster than real RX
        _sendCmd("AT+RECVB=?\r");
        status,response = _parseResponse();
        print "Data=>"+response
        lora_rx = False