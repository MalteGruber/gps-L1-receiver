import math

class BitDecoder:
    def __init__(self):
        self.prev_angles=[]    
        self.prev_b=0
        self.bit_count=0        
        self.lock_quality=0
        self.orthogonal_est=0        
        self.bit_eval_sum=0;
        self.internal_bit_counter=0
        self.nav_bits=""
    
    def get_avg_angle(self):     
        
        return self.orthogonal_est
    
    def on_bit_transititon(self,b):
        print("Transition",self.bit_count,"bit#",len(self.nav_bits))

        if(len(self.nav_bits)%500==0):
            print(self.nav_bits)
            
        if(self.bit_count%20!=0):
            self.lock_quality-=0.005
            if(self.lock_quality<0):
                self.lock_quality=0
                
        if(self.bit_count%20==0):
            self.lock_quality+=0.5
        if(self.lock_quality>5):
            self.lock_quality=5
        if(self.lock_quality>2):
            return
        print("Trying to get bit lock",self.lock_quality)
        
        if(self.bit_count%20==0):
            if(self.bit_count/20>self.lock_quality):
                self.internal_bit_counter=0
                self.lock_quality=int(self.bit_count/20)
                print(self.lock_quality)
        
    
    def on_nav_bit(self,b):
        if(b):
            self.nav_bits+="1"
        else:
            self.nav_bits+="0"
    def parse_bit(self,x,y,integ_phase):       
        p=(math.atan2(x,-(y))+1.5*math.pi)%(2*math.pi)                
        if(p>math.pi):
            p=p-math.pi 
            
        #Make orthogonal to bitstream
        p+=math.pi/2           
    
        self.orthogonal_est=p
        
        a=math.cos(p)
        b=math.sin(p)
        
        cross_product_z=b*x-a*y
        
        #Allways updated
        self.internal_bit_counter+=1
        if(self.internal_bit_counter>=20):
            self.internal_bit_counter=0
        
        b=cross_product_z>0
        
        if(b):
            self.bit_eval_sum+=1
        else:
            self.bit_eval_sum-=1

        if(self.internal_bit_counter<1):
            self.bit_eval_sum=0
        
        if(self.internal_bit_counter>18):
            self.on_nav_bit(self.bit_eval_sum>0)            
        
        #here we get a lock on the bitstream
        if(self.prev_b!=b):
            self.on_bit_transititon(b)
            self.bit_count=0
            
        self.bit_count+=1
        self.prev_b=b




        