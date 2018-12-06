import numpy as np
from scipy import signal
import math
from prn_handler import *

#GPS
PRN_LEN=4000

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
    corr = signal.correlate(iq_signal, sprn, mode='valid',method="fft") 
    return corr



"""
Returns information about
"""
def get_prn_info(offset, buffer,doppler_freq,sv):
    
    iq_signal = np.array(buffer[offset: offset + PRN_LEN * 2])  
    corr = get_corr(doppler_freq, sv, iq_signal)
    acorr = abs(corr)
    peak = max(acorr)
    avg = sum(acorr) / len(acorr)
    return {"max_idx":(acorr.argmax()),
            "snr":peak / avg
            }
 
    
def get_peak_matches(peaks,tol):
    no_peaks = []
    for i in range(len(peaks)):
        no_peaks.append(0)
        this_peak = peaks[i]
        # Now get the number of peaks that match this peak
        for j in  range(len(peaks)):
            if(i == j):
                continue #Skip the peak that is being tested for
            if(this_peak > peaks[j] - tol and this_peak <= peaks[j] + tol):
                no_peaks[i] += 1
    return no_peaks
"""
@param peaks: A list of the location of maximum correlation
@return: The number of matching peaks within the tolerance
"""
def get_num_peaks(peaks):
    no_peaks=get_peak_matches(peaks,3)
    return max(no_peaks)


def get_idx_of_common_peaks( peaks):
    no_peaks=get_peak_matches(peaks,3)
    max_peaks=max(no_peaks)
    idx_of_max_peaks=[]
    for i in range(len(no_peaks)):
        p=no_peaks[i]
        
        if(p==max_peaks):
            idx_of_max_peaks.append(peaks[i])
    
    return sum(idx_of_max_peaks)/len(idx_of_max_peaks)
"""
This function analyzes the buffer and provides information about its properties
@param freq: The doppler frequency at which to do the analyzis
@return: peaks: maximum number of peaks that occure within the same time delay
@return: snr: a rough estimation of the maximum peaks relationship to the remaning correlation
"""
def get_buffer_info(buffer,freq,scan_len,sv):
    peaks = []
    snr_lst = []        
    for j in range(scan_len):
        info = get_prn_info(j * PRN_LEN,buffer, freq,sv)
        peaks.append(info["max_idx"])
        snr_lst.append(info["snr"])  
    return {"peaks":get_num_peaks(peaks), "best_snr":max(snr_lst)}    


    