# GPS L1 Receiver
This is a project that I did to get some more experience of SDR receivers and real-world signal processing.
During this work, I have refrained from looking at other related implementations and have tried to solve issues on my own. Hence some parts of the receiver might seem a bit unconventional and possibly overly convoluted. That being said, this project has provided me with much insight, and it has been a lot of fun! This readme file contains a brief description of some of the key components and concepts of the project.

### Scope
This project is limited to receiving the data bits of the navigation message, however, since the offset of the PRN is known and the fields of the navigation message give the spacecraft ephemeris it is technically possible to get location data from the output of the program. The receiver cannot run in real time and processes a single GPS satellite at a time.

## RF Front End
I used the RTL-SDR which is a 30$ SDR receiver (Including *Swedish* VAT!) based on the now classic RTL2832U receiver chip. I used a sampling rate of 2MS/S which is close to the limit of the RTL-SDR. I used an active GPS antenna powered directly from the 5V bias tee of the RTL-SDR. I used GNU radio to dump the samples into a file as IQ interleaved signed int16 samples (This is the format that the program expects).  The file is far to large to upload to GitHub, however, a similar capture *2013_04_04_GNSS_SIGNAL_at_CTTC_SPAIN* can be found [here](https://gnss-sdr.org/my-first-fix/). It is captured at twice the sampling rate but the file format is the same (Interleaved 16 bit signed int).  

*Here is the SDR Receiver and active GPS antenna that I used:*
<p align="center">
<img src="doc/sdr.png" width="70%" />
</p>

## Single correlation design
As the signal is received it is divided into chunks of size 2*1024 IQ-Samples (I.e. two PRNs with unknown offset), these samples are then cross-correlated to the incoming signal. The correlation is next scanned for the maximum. If the received noise contains the signal three will be correlation and the offset of the correlation will be time offset of the signal. This time offset is ultimately what is used to determine the distance to the satellite (All satellites transmit their PRNs at exactly the same time). Once a signal has been detected, it's correlation maximum is feed to a doppler tracking algorithm.


## Doppler frequency and Correlation

The argument of the complex correlation maximum will that of the phase of the heterodyne beat of the Doppler modified pseudorandom sequence and the Heterodyne beat between the LO receiver, and the Doppler shifted LO of the sending satellite.

![](https://latex.codecogs.com/gif.latex?%5CDelta%5Cphi%28f_0%2Cf_1%2C%5CDelta%20T%29%29%3D2%5Cpi%28f_1-f_0%29%29%5CDelta%20T)

Under certain conditions ![](https://latex.codecogs.com/gif.latex?%5CDelta%5Cphi) can be used to create an integral of the phase difference between the two signals.

The phase integral can now be used as an error signal for a PID controller which controls the local estimation of the Doppler frequency.  The phase integral and doppler generator form a feedback loop as illustrated in the following figure

<p align="center">
  <img src="doc/feedback.png" width="60%"/>
</p>

## Locking onto the bitstream
Each bit is encoded using 20 PRNs, to get a basic bit lock I used this metric to find transitions that are dividable by 20 with a zero remainder (I.e 20, 40,60,80..120 etc ). Once such a transition is seen a confidence counter is increased. This way the receiver locks onto the bitstream, if there is noise it is ignored due to the previously achieved lock. However, merely locking onto the bitstream does not provide information about where we are in the bitstream, for this purpose the bitstream contains preambles which we can scan for. Note, however, that the preambles occurs at other places in the data and can only be accepted after checking the parity of the preamble and adjacent data


## Result
The program is able to track the L1 navigation data stream. Here is a screenshot from the program showing the phase of the correlation maximum and the Doppler frequency drift over time:
<p align="center">
  <img src="doc/gui.png" width="60%"/>
</p>



So far I have been able to receive bits from the navigation messages. Here are some received bits from spacecraft #20 captured with the RTL-SDR:
```
111101010101000111010101010011111011010111011110110011010110100100011100110011010110011001110001100010000111100010111001000001111011110110010000000101011011011010110101110010000011010011111000000010011010111101000111111001010100011000000011010110111111110101101100000110010110111010011110000001110111000001010101000111011001011111100110000000000010101111000110011110111100111101011100010010101111111111111011100110110100111101110000110001111000110001011100001101101001110010110100111111010001100110111111110110111010000000001011101010110101011100101111011111011111011101101110111010011110000001110111000001010101000111011101100101101111010001011111010111101010000011111000011100100010100101111001111110101100000000000001111101010000100001100010101110101010011011001110101011110000101000011111101111111100110101010010111000101011010110110101110011101100000000000001000110101110111010011110000001110111000001010101000111100001101010000111011100010011100101101011010011111000011110110100110001111001111110101000110000000001011101010000100001100100100011011111000110110110111000001011110101001101011111000011100001111011111111110001001110110110011111111011100000000001111111110110111010011110000001110111000001010101000111100101001101111110000001110101111111111110001011010011101100111101010001100001000010110110011111011101110101100110011001110111001010000100010001010001000111011100001111010000101111111101011011010011111111111111111111110110111011011101111000110111010100110110111010011110000001110111000001010101000111101001010001011111010000100001001100101000100100011100110011010110011001110001100010000111100010111001000001111011110110010000000101011011011010110101110010000011010011111000000010011010111101000111111001010100011000000011010110111111110101101100000110010110111010011110000001110111000001010101000111101101011101001110000000000010101111000110011110111100111101011100010010101111111111111011100110110100111101110000110001111000110001011100001101101001110010110100111111010001100110111111110110111010000000001011101010110101011100101111011111011111011101101110111010011110000001110111000001010101000111110001100010101111010000111100010101111011101111111000000000000000001101010110000001011000111111111111001110101111011110011010001101101100111001110000101110100011100010111101001101101100010000111000000000001101010000011011111101111110011111111110011100110110111010011110000001110111000001010101000111110101101110111111011011111011110111011111101111111000011101110001001111010001111110101010001000000001110010101111011110010111101001001110011100110010010101100010110010001000000101010000101011011101000001010000101111100010111001110111100000000000010011011110111010011110000001110111000001010101000111111001001110110110000001110101111111111110001011010011101100111101010001100001000010110110011111011101110101100110011001110111001010000100010001010001000111011100001111010000101111111101011011010011111111111111111111110110111011011101111000110111010100110110111010011110000001110111000001010101000111111101010101100111010000100001001100101000100100011100110011010110011001110001100010000111100010111001000001111011110110010000000101011011011010110101110010000011010011111000000010011010111101000111111001010100011000000011010110111111110101101100000110010110111010011110000001110111000001010101001000000001011000000110000000000010101111000110011110111100111101011100010010101111111111111011100110110100111101110000110001111000110001011100001101101001110010110100111111010001100110111111110110111010000000001011101010110101011100101111011111011111011101101110111010011110000001110111000001010101001000000101100010001111010000010110100111100001111000000111100001100011001110110101111110101001011000000000010101010000100001110000011100100011000110100101010111011001010010000000111010001110000000111101111000101000001111001110000000000100111111111111001000110110111010011110000001110111000001010101001000001001101001101111011011011110011111100010100100000111100000110010010100001101111110101010001000000000100001010000100001101101011100101100100011001101010001110011100000100010001111110010101011100110111101110111111111001101010000011111011111111111101011000110111010011110000001110111000001010101001000001101001110010110000001110101111111111110001011010011101100111101010001100001000010110110011111011101110101100110011001110111001010000100010001010001000111011100001111010000101111111101011011010011111111111111111111110110111011011101111000110111010100110110111010011110000001110111000001010101001000010001010000101111010000100001001100101000100100011100110011010110011001110001100010000111100010111001000001111011110110010000000101011011011010110101110010000011010011111000000010011010111101000111111001010100011000000011010110111111110101101100000110010110111010011110000001110111000001010101001000010101011100111110000000000010101111000110011110111100111101011100010010101111111111111011100110110100111101110000110001111000110001011100001101101001110010110100111111010001100110111111110110111010000000001011101010110101011100101111011111011111011101101110111010011110000001110111000001010101001000011001100001000111001111111101100010011100110011111000011110110111001110100001111110101010100000000000010010101111011110010011111000101111011100101010111001000110010001001010011001001011010110111010110110011010010110010010100001101100100000000101001010001110111010011110000001110111000001010101001000011101101101010111011010111011101111011010110011111000011110011001100001001010000001010111010111111111010010101111011110011001001101101000001110000110000111000000000001000110111110010000001101000110011011010011001110010110011100001001011111111110111110000110111010011110000001110111000001010101001000100001001001010110000001110101111111111110001011010011101100111101010001100001000010110110011111011101110101100110011001110111001010000100010001010001000111011100001111010000101111111101011011010011111111111111111111110110111011011101111000110111010100110110111010011110000001110111
```
I was surprised by how well the signal correlates, there are few false bit flips. Here is a printout from the program showing how many PRNs were the same before inverting (I.e "Transition 40" means that 40 PRN were the same) occurring in multiple of 20 PRN correlations:  
```
Transition 40 bit# 1061
Transition 20 bit# 1062
Transition 40 bit# 1064
Transition 20 bit# 1065
Transition 20 bit# 1066
Transition 20 bit# 1067
Transition 20 bit# 1068
Transition 80 bit# 1072
Transition 20 bit# 1073
Transition 20 bit# 1074
Transition 40 bit# 1076
Transition 40 bit# 1078
Transition 20 bit# 1079
Transition 20 bit# 1080
Transition 20 bit# 1081
```
