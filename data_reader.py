import random
import struct

def read_data_spain(samples):
    dati = []
    datq = []    
    with open("2013_04_04_GNSS_SIGNAL_at_CTTC_SPAIN/2013_04_04_GNSS_SIGNAL_at_CTTC_SPAIN.dat", "rb") as f:
        r = 100000
        skipped_samples = 0
        print("r =", r)
        for p in range(int(r)):
            f.read(2000)
            skipped_samples += 2000
        f.read(2000)   
        skipped_samples += 2000
        print("Starting at t", skipped_samples / (2*4e6), "s") 
        for p in range(int(samples)):               
            i = float(struct.unpack('<h', f.read(2))[0])
            q = float(struct.unpack('<h', f.read(2))[0])
            dati.append(i)
            datq.append(q)
    return [dati, datq]    
    
