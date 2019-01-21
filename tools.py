import numpy as np
from scipy import signal
import math
from prn_handler import *
from settings import *

def limit(val,lim):
    if val>lim:
        return lim
    if val<-lim:
        return -lim
    return val
    
class PidController:
    def __init__(self,p,i,d):
        self.p=p        
        self.i=i
        self.d=d
        self.integ_sum=0
        self.prev_error=0
        self.pid_output=[0]
        self.pid_output=[0]*150
        
    def step(self,ref,measurement):    
        error=(ref-measurement)
        
        error_derivative=error-self.prev_error
        self.prev_error=error
        
        self.integ_sum+=error

        output=error*self.p-error*error_derivative*self.d+self.integ_sum*self.i
        self.pid_output.append(output)
        self.pid_output=self.pid_output[1:]
        for i in range(len(self.pid_output)):
            self.pid_output[i]=self.pid_output[i]*0.3
        avg=0
        for o in self.pid_output:

            avg+=o
        avg/=len(self.pid_output)
        
        return avg


class Correlator:
    def __init__(self):
        self.t=0
        
    def add_doppler_cpx(self,b, doppler):
        dT = 1 / sample_rate_sdr
        for i in range(len(b)):      
            dplr_i = math.cos(2 * math.pi * doppler * self.t)
            dplr_q = math.sin(2 * math.pi * doppler * self.t)       
            self.t+=dT          
            b[i] = b[i].real * dplr_i  +  1.j*(b[i].real * dplr_q)
        return b
    
    def reset_local_phase(self):
        self.t=0    
        
    """
    Used for simulator
    """
    def get_sprn(self,sv,doppler):
        prn_samples = PRN_LEN
        sprn = get_prn(sv, prn_samples)  
        
        deviation=10.2
        noise = np.random.normal(0,deviation,len(sprn))+1.j*np.random.normal(0,deviation,len(sprn))
        
        deviation=0.5
        mean=0.1
        snr_noise = np.random.normal(mean,deviation,len(sprn))+1.j*np.random.normal(mean,deviation,len(sprn))
        
        sprn = np.array(sprn,dtype=np.complex_)
       # sprn=-1.j*sprn
       # sprn=-1*sprn
        sprn*=snr_noise
       # sprn+=noise       
       
        sprn = self.add_doppler_cpx(sprn, doppler)
        sprn *=-1.j    
        return sprn    
    
    def get_corr_cpx(self,doppler, sv, iq_signal,full=True,idx=0): 
        import time
        
        prn_samples = PRN_LEN
        sprn = get_prn(sv, prn_samples)    
        sprn = np.array(sprn,dtype=np.complex_)
        sprn = self.add_doppler_cpx(sprn, doppler)       


        exp_len=PRN_LEN*2
        if(len(iq_signal)!=exp_len):
            print("Unexpected iq signal len of",len(iq_signal),"expected",exp_len)
   

        corr=[]
        if(full):
            corr = signal.correlate(iq_signal, sprn, mode='valid')#,method="fft")   
                  
        else:
            
            corr=np.zeros(len(sprn),dtype=np.complex_)
        
            ref=np.conj(sprn)
            for i in range(3):
                offset=idx-1+i
                if(offset<0):
                    offset=len(sprn)+offset
                try:
                    xcorr=np.dot(iq_signal[offset:offset+len(sprn)],ref)
                except:
                    print("ERROR!!!",offset,len(sprn),len(ref))
                    print(sprn)
                corr[offset]=xcorr

        return corr
    

    
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

