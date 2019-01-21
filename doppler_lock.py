from data_reader import *
from tools import *
from phase_integrator import *
from bit_decoder import *
#from pyqt import *
from main_gui import live_plot_buffer
import time
import sys
from settings import *
from collections import Counter
from test_signal_generator import *

CHUNK_LEN = PRN_LEN * 2  
NO_LOCK = 0
COARSE_LOCK = 1
PHASE_LOCK = 2





def get_most_common_value(arr):
    c=Counter(arr)
    return c.most_common(1)[0][0]



"""
The Coarse Doppler scanner gives a rough estimation of the Doppler frequency
before phase lock can be accived efficiently.
"""
class CoarseDopplerScanner:

    def __init__(self, sv):
        self.sv = sv
        self.state = NO_LOCK
        self.peaks = []
        self.next_freq_countdown = 0
        self.got_lock = False
        self.COARSE_DELTA_F = 200

        self.START_FREQ = -10000
        self.NUM_FREQ_BIN_COMPARES = 5
        self.peak_compare_tolerance = 3
        self.locked_bins = []
        
        self.doppler_freq = -10000             
        self.prime_counter = 0
        self.correlations = []
        self.peak_idx=0
        
    def _on_scan_completed(self):
        if(self.got_lock):
            self.state = COARSE_LOCK
            est_dplr = (max(self.locked_bins) + min(self.locked_bins)) / 2
            self.doppler_freq = est_dplr
        else:
            #No correlation found, try again
            print("LOOOP FOR ",self.sv)
            self.doppler_freq = self.START_FREQ
    
    def step_freq(self, df):
        if(self.next_freq_countdown <= 0):
            self.next_freq_countdown = self.NUM_FREQ_BIN_COMPARES
            self.doppler_freq += df;
            if(self.doppler_freq > -df):
                self._on_scan_completed()               
        else:
            self.next_freq_countdown -= 1

        
        
    def get_coarse_lock(self):
        matches = get_peak_matches(self.peaks, self.peak_compare_tolerance)        
        if(max(matches) > 1):
            print("matches", matches, self.peaks, "freq", self.doppler_freq,"sv",self.sv)
        
        if(max(matches) > 2):
            self.got_lock = True
            if(self.doppler_freq not in self.locked_bins):
                self.locked_bins.append(self.doppler_freq)            
            self.peak_idx=get_most_common_value(self.peaks)            
        self.step_freq(self.COARSE_DELTA_F)
    
    def process_chunk(self, corr, peak_idx):        
        self.peaks.append(peak_idx)
        if(self.prime_counter > self.NUM_FREQ_BIN_COMPARES):
            self.peaks = self.peaks[1:self.NUM_FREQ_BIN_COMPARES + 1]
            self.get_coarse_lock()
        else:
            self.prime_counter += 1
        return self.state, self.doppler_freq


class DopplerPhaseLock:

    def __init__(self, sv):
        self.sv = sv
        self.doppler_freq = 0
        self.NUM_FREQ_BIN_COMPARES = 10
        self.peaks = []
        self.correlations = []
        self.prime_counter = 0
        self.state = NO_LOCK
        self.next_freq_countdown = 0
        self.print_pid_info=False
        self.peak_idx=0
        self.phase_integrator = PhaseIntegrator()        
        self.pid = PidController(p=-0.4, i=-0.0001, d=0.0)
        self.bid = BitDecoder()
        self.prev_phase=0

        self.max_avg_list=[]
        #self.count = 0
    
    def get_phase_lock(self):
        
        thrusted_sample=True
        max_idx=self.peaks[-1]
        #max_idx=self.peak_idx
        maxcorr = self.correlations[-1][max_idx]   
        avg_max=sum(self.max_avg_list)/float(len(self.max_avg_list))
        
        #Track the correlation index maximum
        if(abs(avg_max-max_idx)>3):
            max_idx=int(avg_max)
            thrusted_sample=False
        else:
            if(len(self.max_avg_list)>10):
                self.max_avg_list=self.max_avg_list[1:]
            self.max_avg_list.append(max_idx)
            self.peak_idx=max_idx
        
        avg_count=2
        for i in range(avg_count):            
            maxcorr += self.correlations[-1][max_idx-1-i]
            maxcorr += self.correlations[-1][max_idx+1+i]
        maxcorr/=(avg_count+1)
        
        


        
        #If not a good sample
        phase=self.prev_phase
        
        corr_x= maxcorr.real
        corr_y= maxcorr.imag
        if thrusted_sample:
            # TODO: Just phase, not real,imag
            self.phase_integrator.integrate(corr_x,corr_y)
            phase=self.phase_integrator.get_integral()#= math.atan2(x, y);    
            ref_phase = 0
            pintegral=self.phase_integrator.get_integral()
            pid_output = self.pid.step(ref_phase, pintegral)

           # self.print_pid_info=True
            if self.print_pid_info:    
                def r(val,digits=2):
                    x="%."+str(digits)+"f"
                    s=str(x % round(float(val),digits))
                    stuffings=6-len(s)
                    s=s+"."*stuffings
                    return s
                
                print("integral:",r(self.phase_integrator.get_integral()),
                      "\tdphase",r(self.phase_integrator.prev_d_phase,3),
                      "\tdoppler:",r(self.doppler_freq),
                      r(sim.doppler),
                      r(self.doppler_freq-sim.doppler),
                      r(2*np.pi*(self.doppler_freq-sim.doppler)*1e-3)
                      )
            

          
            self.doppler_freq += pid_output  
            self.prev_phase=phase    
        else:
            print("UNTRUSTED SAMPLE")  
            
        self.bid.parse_bit(corr_x, corr_y, phase)
            
        live_plot_buffer.phase_data["cursor"]["x"]=[0,maxcorr.real]
        live_plot_buffer.phase_data["cursor"]["y"]=[0,maxcorr.imag]
        live_plot_buffer.push_phase_data(
            self.correlations[-1].real.tolist(),
            self.correlations[-1].imag.tolist()        
        )
        
       # time.sleep(0.08)

    def process_chunk(self, corr, peak_idx):
        self.peaks.append(peak_idx)
        self.correlations.append(corr)        
        if(self.prime_counter > self.NUM_FREQ_BIN_COMPARES):
            self.get_phase_lock()
            self.peaks = self.peaks[1:self.NUM_FREQ_BIN_COMPARES + 1]
            self.correlations = self.correlations[1:self.NUM_FREQ_BIN_COMPARES + 1]    
        else:
            self.prime_counter += 1
        return self.state, self.doppler_freq
        
        
class LockHandler:

    def __init__(self, sv):
        self.sv = sv
        self.lock_state = NO_LOCK
        self.doppler_freq = -7500
        self.scanner = CoarseDopplerScanner(sv)
        self.fine_phase = DopplerPhaseLock(sv)
        self.lock_stage = 0
        self.plot_time=0    
        self.prev_last_prn_chunk=[]
        self.correlator=Correlator()        
        self.scan_mode=False
        #self.fake_coarse_lock(-3000,max_idx=1600)
        #self.fake_coarse_lock(-3000,max_idx=1600)
        
    def get_idx_of_maximum(self, corr):
        abs_corr = abs(corr)
        return abs_corr.argmax()

    def fake_coarse_lock(self, freq,max_idx):
        self.lock_stage = 1
        self.fine_phase.doppler_freq = freq
        self.fine_phase.peak_idx=max_idx
        self.fine_phase.max_avg_list=[max_idx]
        self.scan_mode=False
        use_gui=True

    def process_chunk(self, signal):    
        """
        This is the only time we calculate the cross correlation for a chirp
        """
        corr=[]
        if(self.lock_stage==0):        
            corr = self.correlator.get_corr_cpx(self.doppler_freq , self.sv, signal)        
        
        if(self.lock_stage==1):
            #Faster partial cross correlation, only for the offset of the target signal
            corr = self.correlator.get_corr_cpx(self.doppler_freq , self.sv, signal,False,self.fine_phase.peak_idx)        
                
        
        if(self.lock_stage == 0):
            # First stage, coarse scan to see if there are any matching peaks
            state, doppler_freq = self.scanner.process_chunk(corr, self.get_idx_of_maximum(corr))
            self.doppler_freq = doppler_freq
            
            if(state != NO_LOCK):
                self.fine_phase.doppler_freq = self.doppler_freq
                self.fine_phase.max_avg_list=[self.scanner.peak_idx]
                self.fine_phase.peak_idx=self.scanner.peak_idx
                print("Signal offset",self.fine_phase.peak_idx)
                self.lock_stage += 1
                
        elif(self.lock_stage == 1):
            if self.scan_mode:                
                print("GOT SCAN LOCK FOR SV ",self.sv,"@",self.doppler_freq,"Hz")
                self.lock_stage=999 
            # Second stage, hone in on the doppler frequency by using the phase of the correlation            
            localized_peak_idx=self.fine_phase.peak_idx;            
            state, doppler_freq = self.fine_phase.process_chunk(corr, self.get_idx_of_maximum(corr))
            
            self.doppler_freq = doppler_freq
            if(state != NO_LOCK):
                self.lock_stage += 1
                
            self.plot_time+=0.001 #1 ms per prn
            live_plot_buffer.doppler_data["t"].append(self.plot_time)
            live_plot_buffer.doppler_data["y"].append(self.doppler_freq)
            
    def feed_signal(self, signal):
        
        if((len(signal) % CHUNK_LEN) != 0):
            print("INVALID SIGNAL LEN!!",len(signal),"not div. by ",CHUNK_LEN)
            exit(-1)
        N = int(len(signal) / PRN_LEN)
        
        """
        Since the cross correlation needs two prn lens worth of samples, the final prn will not be used, hence we store it and
        prepend it to the next run
        """
        
        num_chunks=N-1
        
        #If not first
        if len(self.prev_last_prn_chunk) !=0:
            num_chunks+=1
            signal=np.append(self.prev_last_prn_chunk,signal)

        #Store that last chunk for prepending to next signal 
        self.prev_last_prn_chunk=signal[-CHUNK_LEN:]
            
        for i in range(num_chunks):
            offset = i * PRN_LEN;
            self.process_chunk(signal[offset:offset + CHUNK_LEN])
            
            
def exe(sv):

    
    d = LockHandler(sv)
    N = PRN_LEN * PRN_LEN
    
    q=start_data_reader_thread(2000 + 1000 * PRN_LEN, N)
        
    while True:
        d.feed_signal(q.get())



sim=Simulator() 
def exeSim(sv):
    global sim
    
    d = LockHandler(sv)
   
    while True:
        d.feed_signal(sim.get_simulated_signal())   

exe(7)

