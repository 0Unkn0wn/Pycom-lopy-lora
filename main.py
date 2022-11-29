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

app_eui = '0000000000000000' # leave as default even in ttn
app_key = '4DB0377D6A9278786CE27B70688B2419' # change this to change the ttn app

#offset values used to make the sensor print correct values
offset_value = -7
offset_procentage = 0.75

#reboot settings
pycom.heartbeat(False)
pycom.rgbled(0x0A0A08) # white

py = Pycoproc(Pycoproc.PYSENSE)

lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
app_eui = ubinascii.unhexlify(app_eui)
app_key = ubinascii.unhexlify(app_key)
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
##
# Looping until it connects to ttn.
# Red until the loop is done green when it connects.
#
while not lora.has_joined():
    pycom.rgbled(0xFF0000) #red
    print('Not yet joined...')
    time.sleep(2)

print('Joined')
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setblocking(True)
pycom.rgbled(0x00FF00) #green
time.sleep(4)

##
# Looping so it sends the sensor readings.
# Green all the time while it is connected.
#

while lora.has_joined():
    pycom.rgbled(0x000000)
    mpp = MPL3115A2(py,mode=PRESSURE) # Returns pressure in Pa. Mode may also be set to ALTITUDE, returning a value in meters.
    si = SI7006A20(py)#Temperature sensor.
    lt = LTR329ALS01(py)#Light sensor
    #Default value of the sensor reading.
    #temp=si.temperature()
    hum=si.humidity()
    press=mpp.pressure()
    li=lt.lux()
    #temp with offset comment both lines and change the payload and temppack to go to the ones without the offset
    temp_with_offset = (si.temperature()+offset_value)
    temp_with_offset = (si.temperature()*offset_procentage)
    #How the payload will look like in the ttn console
    payload = '{"Temperature":'+str(temp_with_offset)+',"Humidity":'+str(hum)+',"Pressure":'+str(press)+',"Light_index":'+str(li)+'}'
    print(payload)
    #Packing the data into bytes so it is be sent in a package.
    temppack = ustruct.pack('f',temp_with_offset)
    humpack = ustruct.pack('f',hum)
    presspack = ustruct.pack('f',press)
    lippack = ustruct.pack('f',li)
    #Making the final package.
    payloadpack = temppack+humpack+presspack+lippack
    #Sending the packet
    s.send(payloadpack)
    #Modify this to change how fast the data is sent.
    time.sleep(6)
