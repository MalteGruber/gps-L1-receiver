

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from phase_integrator import *
import math


import random
t=0
psk=1
integ=PhaseIntegrator()
def update_line(num, data, line0,line1,line2,line3,line4,line5):
    global t
    global integ
    global psk
    t+=0.01
    
    dir=+1
    print(num)
    if((num%5)==0):
        psk=-psk
    
    x=psk*math.cos(dir*t)
    y=psk*math.sin(dir*t)   
    rsize=0.2
    if(False):
        x+=random.uniform(-rsize, rsize) 
        y+=random.uniform(-rsize, rsize)
    line0.set_data([x],[y])
    line1.set_data([x],[y])
    
    integ.integrate(x, y)
    p=integ.get_integral_xy()
    line2.set_data([0,p[0]],[0,p[1]])
    line3.set_data([p[0]],[p[1]])
    
    #Absolute fliped:
    p=integ.get_abs_phase()
    line4.set_data([0,p[0]],[0,p[1]])
    line5.set_data([p[0]],[p[1]])    
    
    
   # input("cont?")
    return line0,line1,line2,line3,line4,line5

fig1 = plt.figure()
ax = fig1.add_subplot(1, 1, 1)
ax.set_aspect('equal')
ax.grid(True, which='both')


ax.axhline(y=0, color='k')
ax.axvline(x=0, color='k')

data = np.random.rand(2, 25)
l0, = plt.plot([], [], 'k-')
l1, = plt.plot([], [], 'ko')

l2, = plt.plot([], [], 'g-')
l3, = plt.plot([], [], 'r-')

l4, = plt.plot([], [], 'b-')
l5, = plt.plot([], [], 'bx')

d=1.5
plt.xlim(-d, d )
plt.ylim(-d, d)
plt.ylabel('Imaginary')
plt.xlabel('Real')
plt.title('test')
line_ani = animation.FuncAnimation(fig1, update_line, 25, fargs=(data, l0,l1,l2,l3,l4,l5),
                                   interval=50, blit=True)

# To save the animation, use the command: line_ani.save('lines.mp4')

plt.show()
