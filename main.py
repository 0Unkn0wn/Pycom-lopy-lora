from network import LoRa
import socket
import time
import ubinascii
import ustruct
import pycom
from pycoproc_1 import Pycoproc
import machine
import math
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE



APP_EUI = '0000000000000000' # leave as default even in ttn
APP_KEY = '4DB0377D6A9278786CE27B70688B2419' # change this to change the ttn app

#offset values used to make the sensors print correct values
HUMIDITY_OFFSET_PERCENTAGE = 0.595
TEMPERATURE_OFFSET_PERCENTAGE = 0.718
SEND_DELAY = 240


def led_color(hex_color):
    """
    Sets the color of the LED to the specified hex color.

    @param hex_color: The hexadecimal color to set the LED to.
    @type hex_color: str
    """
    pycom.rgbled(hex_color)


def make_lora_connection(app_eui,app_key):
    """
    Makes a LoRa connection using the given app EUI and app key.

    @param app_eui: The app EUI to use for the connection.
    @type app_eui: str
    @param app_key: The app key to use for the connection.
    @type app_key: str
    @return: The LoRa object representing the connection.
    @rtype: LoRa
    """
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
    app_eui = ubinascii.unhexlify(app_eui)
    app_key = ubinascii.unhexlify(app_key)
    lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
    return lora


def print_payload(payloadpack):
    """
    Prints the values of temperature, humidity, pressure, light index, and battery voltage contained in a given payloadpack.

    @param payloadpack: The payloadpack containing the values to be printed.
    @type payloadpack: bytes
    """
    payload_unpacked=ustruct.unpack("ffiif",payloadpack)
    print("Temperature,Humidity,Pressure,Light_index,Battery_voltage\n",payload_unpacked)

def calculate_luminance(light):
    """
    Calculates the luminance value of a given light intensity.

    @param light: The light intensity to calculate the luminance for.
    @type light: int
    @return: The calculated luminance value.
    @rtype: int
    """
    if(light < 123):
        return int(round(light))
    else:
        light = int(round(math.log(light,1.04),0))
        if(light > 255):
            light = 255
        return light

def construct_payload(si,mpp,li):
    """
    Constructs a payload containing the values of temperature, humidity, pressure, light index, and battery voltage.

    @param si: The object representing the temperature and humidity sensor.
    @param mpp: The object representing the pressure sensor.
    @param lt: The object representing the light sensor.
    @return: The constructed payload containing the values of temperature, humidity, pressure, light index, and battery voltage.
    @rtype: bytes
    """
    temp = round(si.temperature() * TEMPERATURE_OFFSET_PERCENTAGE,2)
    hum = round(si.humidity() * HUMIDITY_OFFSET_PERCENTAGE,1)
    press = int(round(mpp.pressure()/100)) # mbar conversion
    li = calculate_luminance(lt.lux())
    volatage = round(py.read_battery_voltage(),2)
    # DEBUG:
    # return '{"Temperature":'+str(temp)+',"Humidity":'+str(hum)+',"Pressure":'+str(press)+',"Light_index":'+str(li)+'}'
    #Packing the data into bytes so it is be sent in a package.
    payloadpack = ustruct.pack('ffiif',temp,hum,press,li,volatage)
    return payloadpack


#reboot settings
pycom.heartbeat(False)
led_color(0x0A0A08) # white

py = Pycoproc(Pycoproc.PYSENSE)

lora = make_lora_connection(APP_EUI,APP_KEY)

# Loop until the LoRa connection has been established
while not lora.has_joined():
    # Set the LED color to red
    led_color(0xFF0000)
    # Print a message indicating that the connection is not yet established
    print('Not yet joined...')
    # Sleep for 2.5 seconds before checking the connection again
    time.sleep(2.5)

print('Joined')
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setblocking(True)
led_color(0x00FF00) #green
time.sleep(4)


# Looping so it sends the sensor readings.
# Green when it is connected then off so it doesn't affect the lux calculations.
try:#everyting under a try except so if the i2c bus fails the machine resets.
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
