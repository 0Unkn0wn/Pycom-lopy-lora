# Pycom-lopy-lora
The code that enables the connection between the Pycom-Lopy and the TTN console.
The device sends the data from its sensors(temperature, humidity, pressure, and light index) in the form of an array of bits.
The data is then decoded in the TTN console with the help of a custom function.

```js
  // Based on https://stackoverflow.com/a/37471538 by Ilya Bursov
function bytesToFloat(bytes) {
  // JavaScript bitwise operators yield a 32 bits integer, not a float.
  // Assume LSB (least significant byte first).
  var bits = bytes[3]<<24 | bytes[2]<<16 | bytes[1]<<8 | bytes[0];
  var sign = (bits>>>31 === 0) ? 1.0 : -1.0;
  var e = bits>>>23 & 0xff;
  var m = (e === 0) ? (bits & 0x7fffff)<<1 : (bits & 0x7fffff) | 0x800000;
  var f = sign * m * Math.pow(2, e - 150);
  return f;
}
  
  
function Decoder(bytes, port) {
  var pres = (bytes[9] << 8) | bytes[8];
  var li = (bytes[13] << 8) | bytes[12];

  return {
    Temperature: Number(bytesToFloat(bytes.slice(0, 4)).toFixed(2)),
    Humidity: Number(bytesToFloat(bytes.slice(4, 8)).toFixed(2)),
    Pressure: pres,
    Light: li,
    Voltage: Number(bytesToFloat(bytes.slice(16, 20)).toFixed(2)),
  };
}
```
