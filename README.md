# GPS Receiver
GPS receivers are an amazing technology that we all too often take for granted. This program is an exploration of the techniques that make GPS possible. The program takes input in the form of an SDR capture in quadrature form. From this data, the program extracts the signals originating from the GPS satellites by correlating their C/A codes to the received data. For now, the program does not deal with the calculations of determining the exact position of the user.

This is still a work in progress, but it is able to lock onto the C/A codes, producing the following output:
```
Starting at t 25.00025 s
Got lock for SV 1 doppler -6722.22 Hz
Got lock for SV 11 doppler -5200.96 Hz
Got lock for SV 17 doppler -9833.33 Hz
Got lock for SV 20 doppler -8388.89 Hz
Got lock for SV 32 doppler -6500.0 Hz
```

This corresponds with the satellites that are received by the reference log, found [HERE](https://gnss-sdr.org/my-first-fix/). Note that the SDR capture is not included here, due to it's size.
