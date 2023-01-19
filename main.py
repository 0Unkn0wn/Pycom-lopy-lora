import ustruct
import math

def test_unpack_payload(payloadpack):

    payload_unpacked=ustruct.unpack("ffiif",payloadpack)
    return payload_unpacked


def test_calculate_luminance(light):

    if(light < 123):
        return int(round(light))
    else:
        light = int(round(math.log(light,1.04),0))
        if(light > 255):
            light = 255
        return light

def test_construct_payload():

    temp = 20.0
    hum = 60.0
    press = 1000
    li = test_calculate_luminance(120)
    volatage = 4.5
    payloadpack = ustruct.pack('ffiif',temp,hum,press,li,volatage)
    return payloadpack

assert test_calculate_luminance(120) == 120 ,"Error"
assert test_calculate_luminance(120.3) == 120 ,"Error"
assert test_calculate_luminance(120.6) == 121 ,"Error"
assert test_calculate_luminance(150) == int(round(math.log(150,1.04),0)) ,"Error"
assert test_calculate_luminance(100000) == 255 ,"Error"
assert test_construct_payload() == ustruct.pack("ffiif",20.0,60.0,1000,120,4.5) ,"Error"
assert test_unpack_payload(test_construct_payload()) == (20.0,60.0,1000,120,4.5) ,"Error"

print("All test passed")
