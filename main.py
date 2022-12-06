from network import LoRa
import socket
import time
import ubinascii
import ustruct
import pycom
from pycoproc_1 import Pycoproc
import machine

from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE


def led_color(hex_color):
    ##    The function that sets the color of the led.
    #    @param hex color - The color the led will have but in hexadecimal
    #
    pycom.rgbled(hex_color)


def make_lora_connection(app_eui,app_key):
    ##    The function that makes the LoRa connection
    #    @param app_eui: The standard app_eui provided by TTN documentation. Should not be changed.
    #    @param app_key: The key provided by TTN when a device is added in a TTN application.
    #
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
    app_eui = ubinascii.unhexlify(app_eui)
    app_key = ubinascii.unhexlify(app_key)
    lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
    return lora


def print_payload(payloadpack):
    ##    The function that prints how the payload will look like in the console.
    #
    payload_unpacked=ustruct.unpack("<4f",payloadpack)
    print("Temperature,Humidity,Pressure,Light_index\n",payload_unpacked)

def construct_payload(si,mpp,li):
    ##    The function that constructs the payload to be ready for sending.
    #    @param si: The variable for the temperature and humidity sensor.
    #    @param mpp: The variable for the pressure sensor.
    #    @param li: The variable for the light sensor
    #    @return: The function returns the constructed payload already in bit format ready to be sent to the TTN console.
    #

    #Default value of the temperature sensor reading.
    temp=si.temperature()*TEMPERATURE_OFFSET_PERCENTAGE
    hum=si.humidity()*HUMIDITY_OFFSET_PERCENTAGE
    press=mpp.pressure()
    li=lt.lux()
    # DEBUG:
    # return '{"Temperature":'+str(temp)+',"Humidity":'+str(hum)+',"Pressure":'+str(press)+',"Light_index":'+str(li)+'}'
    #Packing the data into bytes so it is be sent in a package.
    temppack = ustruct.pack('f',temp)
    humpack = ustruct.pack('f',hum)
    presspack = ustruct.pack('f',press)
    lippack = ustruct.pack('f',li)
    #Making the final package.
    payloadpack = temppack+humpack+presspack+lippack
    return payloadpack


APP_EUI = '0000000000000000' # leave as default even in ttn
APP_KEY = '4DB0377D6A9278786CE27B70688B2419' # change this to change the ttn app

#offset values used to make the sensor print correct values
HUMIDITY_OFFSET_PERCENTAGE = 0.595
TEMPERATURE_OFFSET_PERCENTAGE = 0.718
SEND_DELAY = 60


#reboot settings
pycom.heartbeat(False)
led_color(0x0A0A08) # white

py = Pycoproc(Pycoproc.PYSENSE)

lora = make_lora_connection(APP_EUI,APP_KEY)
##
# Looping until it connects to ttn.
# Red until the loop is done green when it connects.
#
while not lora.has_joined():
    led_color(0xFF0000) #red
    print('Not yet joined...')
    time.sleep(2.5)

print('Joined')
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setblocking(True)
led_color(0x00FF00) #green
time.sleep(4)

##
# Looping so it sends the sensor readings.
# Green all the time while it is connected.
#
try:
    while lora.has_joined():
        led_color(0x000000)#Led off
        mpp = MPL3115A2(py,mode=PRESSURE) # Returns pressure in Pa
        si = SI7006A20(py)#Temperature sensor
        lt = LTR329ALS01(py)#Light sensor
        #Making the final package.
        payloadpack = construct_payload(si,mpp,lt)
        #How the payload will look like in the ttn console
        print_payload(payloadpack)
        #Sending the packet
        s.send(payloadpack)
        time.sleep(SEND_DELAY)
except:
    machine.reset()
