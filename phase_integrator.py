import math

class PhaseIntegrator():
    
    def __init__(self):
        self.integral=0.1
        self.prev_phase=0
        self.prev_d_phase=0
        
        self.p0=0
        self.p1=0
        self.p2=0
        self.p3=0
        self.p4=0
        self.limit=99

    def integrate(self,x,y):

        phase=math.atan2(x,y)

        dphase=(self.prev_phase-phase)
        dp=dphase
        """
        If the change is greater than 180, there might be a bit flip or a change from 0 to -350 (example)
        """
        if(abs(dphase)>math.pi/2):        
            #Special case -89 to 1 but fliping.
            if(abs(dphase)>2*math.pi-math.pi/2):                
                if(dphase>0):       
                    dphase-=2*math.pi
                else:    
                    dphase+=2*math.pi
            else: #nominal case
                """
                Flip the phase such that it enters the first quadrant!
                """                
                if(dphase>0):
                    dphase-=math.pi        
                else:
                    dphase+=math.pi


        self.p4=self.p3  *0.9
        self.p3=self.p2  *0.9
        self.p2=self.p1  *0.9
        self.p1=self.p0  *0.9
        self.p0=dphase
      
        avg=self.p4+self.p3+self.p2+self.p1+self.p0
        avg/=5
        dphase=avg
            
        self.integral+=dphase
        self.prev_d_phase=dphase
        self.prev_phase=phase

            
    def get_integral(self):
        return self.integral
   
    def get_integral_xy(self):
        return [math.cos(self.integral),math.sin(self.integral)]
    
    def reset_integral(self):
        self.integral=0


    
       
