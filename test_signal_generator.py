from tools import *
class Simulator:
    def __init__(self):
        self.c=Correlator()
        self.doppler=-3001.0
        self.sv=20
        self.slask=None
        self.offset=400
        self.is_first=True
        self.dir=1
    def mod_doppler(self):
        
        
        return;
        """
        if(self.doppler<-3105):
            self.dir=1;
        if(self.doppler>-3000):
            self.dir=-1;
            
        self.doppler+=self.dir*0.001
      #  print(self.doppler)
        """
        
    def get_simulated_signal(self):
        
        a=np.array([])
        """
        We need to save the last bit of the previous prn sequence and append it to the one that we
        return now, otherwise there will be a jump in time.
        """
        self.mod_doppler()  
        if(self.is_first):
            self.is_first=False
            self.slask=self.c.get_sprn(self.sv,self.doppler)[self.offset:]

        prn_sequence=self.c.get_sprn(self.sv,self.doppler)

        last_prn=self.c.get_sprn(self.sv,self.doppler)
        
        
        a=np.append(self.slask,prn_sequence)
        first_part=last_prn[0:self.offset]
        last_part=last_prn[self.offset:]
        a=np.append(a,first_part)
        self.slask=last_part

        return a
        

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D    
from matplotlib import cm
from matplotlib import colors

if __name__ == "__main__":  


    s=Simulator()
    sig=s.get_simulated_signal()
    sig=np.append(sig,s.get_simulated_signal())
    sig=np.append(sig,s.get_simulated_signal())
    
    t = np.linspace(0.0, 2.0, len(sig))

    fig, ax = plt.subplots()
    ax.plot(t, sig.real)
    ax.plot(t, sig.imag)
    
    plt.show()
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d', proj_type = 'ortho')
    
    
    sig=get_simulated_signal()
    
    x=sig.real
    y=sig.imag
    N=len(sig)
    t = np.linspace(0,10, N)
    ax.plot(x, y, t)
        
    ax.plot([0,0],[0,0],[-10,10])
   # ax.scatter(x, y, t, c=t, cmap='viridis', linewidth=0.5);
    ax.legend()
    
    plt.show()
    """
    
