import numpy as np
from scipy import signal
import math
from prn_handler import *
from data_reader import *
import matplotlib.pyplot as plt
from tools import *
from _operator import is_





class Tracker:

    def __init__(self, sv):
        self.doppler_freq = -6070
        self.sv = sv
        self.has_lock = False
        self.MAX_SCAN_LEN=16
        self.prn_offset=0                 
   
    def _get_lock(self,buffer):
        first_acceptable_freq = 0
        possible_correlation = False
        """
        At this point we do not know what the doppler shift is or if there is a signal.
        Therefore we test possible frequencies in the range of possible doppler shift,
        do so with a coarse jump in frequency for a initial rough scan.
        """
        for i in range(-10, 10):
            freq = i * 1000;
            info = get_buffer_info(buffer,freq,14,self.sv)
            if(info["peaks"] > 1):
                first_acceptable_freq = freq;
                possible_correlation = True
                break;
        """
        If the initial scan for a possible singnal did no yield any result we abandon the search, but
        if we think we might have something we move on to the next step: refining the doppler estimation.
        """
        if not possible_correlation:
            return False
        """
        In this step we do a very rough optmization, we make a guess below and above our best guess
        for the dopller frequency. If the guess is better (We jugdge this by several factors) we update
        our guess. This is repeated and hopefully the guess converges on a frequency that is our doppler shift.
        """
        new_guess_delta_freq = 1000;
        freq = first_acceptable_freq;
        number_of_guess_itterations=15
        for i in range(1, number_of_guess_itterations):            
            new_guess_delta_freq = new_guess_delta_freq / 3            
            info_a = get_buffer_info(buffer,freq + new_guess_delta_freq,14,self.sv)
            info_b = get_buffer_info(buffer,freq - new_guess_delta_freq,14,self.sv)                        
            if(info_a["best_snr"] > info_b["best_snr"]):
                freq += new_guess_delta_freq
            else:
                freq -= new_guess_delta_freq
        """
        Now check if we have a lock
        """
        info = get_buffer_info(buffer,freq,14,self.sv)
        if(info["peaks"] > 2):
            self.doppler_freq = freq
            self.has_lock=True
            self._update_lock_info(buffer)
            print("Got lock for SV", self.sv, "Doppler", round(self.doppler_freq, 2), "Hz | Offset",self.prn_offset)
            return True
        return False





    def _update_lock_info(self,buffer):
        
        peaks=[]
        for j in range(self.MAX_SCAN_LEN-1):
            info = get_prn_info(j * PRN_LEN,buffer, self.doppler_freq,self.sv)
            peaks.append(info["max_idx"])
        if(get_num_peaks(peaks)>3):
            self.prn_offset=int(get_idx_of_common_peaks(peaks))
        
        
    def run_tracker(self, buffer):        
        
        #Discard old information
        if(len(buffer)!=PRN_LEN*self.MAX_SCAN_LEN):
            print("len not as expected...")
        
        if(self.has_lock):
            self._update_lock_info(buffer)
        elif(len(buffer) + 1 >= PRN_LEN * self.MAX_SCAN_LEN):
            self._get_lock(buffer)

            pass
        else:
            pass







################################################################################

        
def get_real_signal(data):
    signal = []
    for i in range(len(data[0])):
        d = data[0][i] + data[1][i]
        signal.append(d)
    return signal





read_offset=0
read_buffer_len=16*4000


class Reader:
    def __init__(self,trakcer):
        self.tracker=trakcer
        self.sv=trakcer.sv
        self.nav_bitstream=[]
        
    def read_signal(self,buffer):
        
        #Try to get lock
        self.tracker.run_tracker(buffer[0:PRN_LEN*self.tracker.MAX_SCAN_LEN])
        if(self.tracker.has_lock):
            
            prev_was_positive=True
            same_polarity_streak=0
            edge_prn_count=0
            bits=[]
            self.tracker.doppler_freq=7075
            for prn_idx in range(int( (len(buffer)/PRN_LEN)/2  )-1):
                
                

                #Timeshift/Center the correlation spike to the middle of the correlation
                offset=prn_idx*PRN_LEN*2
              #  print(offset/8000)
                
                if((prn_idx%20)==0):
                    self.tracker.run_tracker(buffer[offset:offset+PRN_LEN*self.tracker.MAX_SCAN_LEN])                
                    print(self.tracker.doppler_freq,self.tracker.prn_offset)
             #   print(offset+2*PRN_LEN,len(buffer))
                offset+=int(self.tracker.prn_offset+PRN_LEN/2)          
                       
                iq_signal = np.array(buffer[offset:offset+2*PRN_LEN])
                delta=3
                corr_a=get_corr(self.tracker.doppler_freq+delta, self.sv, iq_signal)
                corr_b=get_corr(self.tracker.doppler_freq-delta, self.sv, iq_signal)
                width=5
                
                a=max(abs(corr_a[int(PRN_LEN/2-width):int(PRN_LEN/2+width)]))
                b=max(abs(corr_b[int(PRN_LEN/2-width):int(PRN_LEN/2+width)]))
                
                if(a>b):
                    self.tracker.doppler_freq+=0.1
                else:
                    self.tracker.doppler_freq-=0.1
                    
                
                corr=get_corr(self.tracker.doppler_freq, self.sv, iq_signal)
                
                
                
              #  plt.plot(corr)
              #  plt.show()
                corr=corr[int(PRN_LEN/2-width):int(PRN_LEN/2+width)]
                
                
             #   print(corr)
                minimum_peak=min(corr)
                maximum_peak=max(corr)
                

        
                is_positive=maximum_peak>abs(minimum_peak)
                
                if(prev_was_positive==is_positive):
                    same_polarity_streak+=1
                    edge_prn_count+=2
                    
                else:
                    same_polarity_streak=0
                    edge_prn_count=0
                                    
                if(is_positive):                    
                  #  print("P:",int(maximum_peak),"\t\t|\t",same_polarity_streak,edge_prn_count)
                    bits.append(maximum_peak)
                else:
                   # print("N:",int(minimum_peak),"\t|\t\t",same_polarity_streak,edge_prn_count)
                    bits.append(minimum_peak)
                
                prev_was_positive=is_positive
            plt.plot(bits)
            plt.show()                
                
sv=1
raw_iq = get_real_signal(read_data_spain(0,PRN_LEN*4000))  
print("file read")
reader=Reader(Tracker(sv))
reader.read_signal(raw_iq)

"""
#for sv in range(1, 33):
if True:
    sv=11
    tracker = Tracker(sv)
    tracker.run_tracker(raw_iq[read_offset:read_offset+read_buffer_len])
    read_offset+=PRN_LEN*tracker.MAX_SCAN_LEN;
    for i in range(3):
        tracker.run_tracker(raw_iq[read_offset:read_offset+read_buffer_len])
        read_offset+=PRN_LEN*tracker.MAX_SCAN_LEN;    
        
        

    for i in range(2):
        offset=read_offset
        offset+=tracker.prn_offset-2000
        
        iq_signal = np.array(raw_iq[offset:offset+4000*2])
        
        read_offset+=8000
        corr=get_corr(tracker.doppler_freq, sv, iq_signal)
        width=100
        corr=corr[2000-width:2000+width]
        plt.plot(corr)
        plt.show()
        
"""