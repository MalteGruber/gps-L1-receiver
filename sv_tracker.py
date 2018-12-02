import numpy as np
from scipy import signal
import math
from prn_handler import *
from data_reader import *


def add_doppler(b, doppler):
    t = 0
    dT = 1 / 4e6  # Timestep between samples in seconds
    for i in range(len(b)):        
        dplr = math.cos(2 * math.pi * doppler * t)        
        t += dT
        b[i] = b[i] * dplr
    return b


def get_corr(doppler, sv, iq_signal): 
    prn_samples = 4000
    sprn = get_prn(sv, prn_samples)    
    sprn = add_doppler(sprn, doppler)       
    corr = signal.correlate(iq_signal, sprn, mode='valid') 
    return corr


class Tracker:

    def __init__(self, sv):
        self.doppler_freq = -6070
        self.sv = sv
        self.signal = []
        self.has_lock = False
        self.buffer = []
        self.prn_samples = 4000

    def get_snr(self):
        pass
    
    def get_prn_info(self, offset, doppler_freq):
        
        iq_signal = np.array(self.buffer[offset: offset + self.prn_samples * 2])  
        corr = get_corr(doppler_freq, self.sv, iq_signal)
        acorr = abs(corr)
        peak = max(acorr)
        avg = sum(acorr) / len(acorr)
        return {"max_idx":(acorr.argmax()),
                "snr":peak / avg
                }

    def get_num_peaks(self, peaks):
        
        no_peaks = []
        for i in range(len(peaks)):
            no_peaks.append(0)
            this_peak = peaks[i]
            # Now get the number of peaks that match this peak
            for j in  range(len(peaks)):
                if(i == j):
                    continue
                tol = 3
                if(this_peak > peaks[j] - tol and this_peak <= peaks[j] + tol):
                    no_peaks[i] += 1

        return max(no_peaks)
    
    def get_buffer_info(self, freq):
        peaks = []
        snr_lst = []        
        for j in range(16):
            # print(j)
            info = self.get_prn_info(j * self.prn_samples, freq)
            peaks.append(info["max_idx"])
            snr_lst.append(info["snr"])  
        return {"peaks":self.get_num_peaks(peaks), "best_snr":max(snr_lst)}                  
   
    def get_lock(self):
        first_ok_freq = 0
        possible_correlation = False
        for i in range(-10, 10):
            freq = i * 1000;
            info = self.get_buffer_info(freq)
            if(info["peaks"] > 2):
                first_ok_freq = freq;
                possible_correlation = True
                break;
            
        if not possible_correlation:
            return False
        
        delta = 1000;
        freq = first_ok_freq;
        for i in range(1, 15):            
            delta = delta / 3            
            info_a = self.get_buffer_info(freq + delta)
            info_b = self.get_buffer_info(freq - delta)                        
            if(info_a["best_snr"] > info_b["best_snr"]):
                freq += delta
            else:
                freq -= delta

        # Now check if we have a lock
        info = self.get_buffer_info(freq)
        if(info["peaks"] > 2):
            self.doppler_freq = freq
            print("Got lock for SV", self.sv, "doppler", round(self.doppler_freq, 2), "Hz")
            return True
        return False

    def consume_signal(self, signal):        
        self.buffer += signal
        self.buffer = self.buffer[0:self.prn_samples * 16]
        if(self.has_lock):
            pass
        elif(len(self.buffer) + 1 >= self.prn_samples * 16):
            self.get_lock()
            pass
        else:
            pass

        
def get_real_signal(data):
    signal = []
    for i in range(len(data[0])):
        d = data[0][i] + data[1][i]
        signal.append(d)
    return signal


data = read_data_spain(80 * 4000)
raw_iq = get_real_signal(data) 
for sv in range(1, 33):
    tracker = Tracker(sv)
    tracker.consume_signal(raw_iq)

    
