import random
import struct

def read_data_spain(iq_offset,len_iq_samples):
    dati = []
    datq = []    
    with open("2013_04_04_GNSS_SIGNAL_at_CTTC_SPAIN/2013_04_04_GNSS_SIGNAL_at_CTTC_SPAIN.dat", "rb") as f:

        skipped_samples = 0
        
        for p in range(int(iq_offset)):
            f.read(4)
            skipped_samples += 4
            
        print("Starting at t", skipped_samples / (2*4e6), "s") 
        
        for p in range(int(len_iq_samples)):               
            i = float(struct.unpack('<h', f.read(2))[0])
            q = float(struct.unpack('<h', f.read(2))[0])
            dati.append(i)
            datq.append(q)
    return [dati, datq]    
    
