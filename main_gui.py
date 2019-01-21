import _thread
import time

from PyQt4.QtCore import QObject, pyqtSignal, QThread
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np
import pyqtgraph as pg
import sys


class Window(QtGui.QWidget):
    
    plot_data_trigger = pyqtSignal(list, list)
    
    def __init__(self):
        
        QtGui.QWidget.__init__(self)
        self.setGeometry(400, 300, 700, 700)
        self.plot_data_trigger.connect(self.on_plot_data)
        layout = QtGui.QVBoxLayout()
        
#        layout.addWidget(QLabel("HEJ"))
        pg.setConfigOption('foreground', '0f4')
        
        """
        Phase Plot Widget
        """
         
        self.axis_limit = 1e4
        r = self.axis_limit      
        self.phase_plot_widget = pg.PlotWidget(title="Correlation Phase")
        self.phase_plot_widget.setAspectLocked(True, 1)
        self.phase_plot_widget.setXRange(-r,r)
        self.phase_plot_widget.setYRange(-r,r)
        
        """
        Doppler Plot Widget
        """
        r = self.axis_limit       
        self.axis_limit = 1e5
        self.doppler_plot_widget = pg.PlotWidget(title="Doppler")        
 #       self.doppler_plot_widget.setXRange(-r,r)
#        self.doppler_plot_widget.setYRange(-r,r)
    
        for i in range(10):
            self.doppler_plot_widget.plot(name="Phase #" + str(i), pen=(i, 3))
        
        layout.addWidget(self.phase_plot_widget)
        layout.addWidget(self.doppler_plot_widget)
                
        self.setLayout(layout)

    def on_plot_data(self, xdata, ydata):
        
        # if
        # for i in range(int(len(xdata)/4000)):
    #        print(i)
        i = 0
        pen = pg.mkPen(color=i, alpha=0.1, antialias=False)
            
        self.phase_plot_widget.plot(xdata, ydata, clear=(i == 0), pen=pen)
        
    def plot(self, xdata, ydata):
        self.plot_data_trigger.emit(xdata, ydata)

    def plot_from_thread(self, data):
                       
        for i in range(len(data["phase_data"]["x"])):       
            i=len(data["phase_data"]["x"])-1
            pen = pg.mkPen(color=data["phase_data"]["pens"][i], alpha=0.1, antialias=True)
            self.phase_plot_widget.plot(data["phase_data"]["x"][i], data["phase_data"]["y"][i], clear=True, pen=pen)
            break
            
        pen = pg.mkPen(color="0f0", alpha=1, antialias=True, width=3,)
        self.phase_plot_widget.plot(data["phase_data"]["cursor"]["x"], data["phase_data"]["cursor"]["y"], pen=pen, brush='g', symbol='o')
        
        i = 0
      
     #   i=0
        pen = pg.mkPen(color="0ff", alpha=0.1, antialias=False, width=4.5,)
        self.doppler_plot_widget.plot(data["doppler_data"]["t"], data["doppler_data"]["y"], clear=(i == 0), pen=pen)
        
        
class GuiUpdateThread(QtCore.QThread):

    data_downloaded = QtCore.pyqtSignal(object)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.data = []
        
        self.phase_data = {"x":[], "y":[], "pens":[],"cursor":{"x":[],"y":[]}}
        self.message_queue = [[], []]
        self.bit_data = [[], []]
        self.doppler_data = {"t":[], "y":[]}
        self.pen_count = 0
    
    def trunkate_buffers(self, buf):
        if len(buf) > 4000:
            buf = buf[-4000:]
        return buf
            
    def push_phase_data(self, x, y):
        self.phase_data["x"].append(x)
        self.phase_data["y"].append(y)
        self.phase_data["pens"].append(self.pen_count)
        phase_buffers = 20
        self.pen_count = (self.pen_count + 1) % phase_buffers
        if(len(self.phase_data["x"]) > phase_buffers):
            self.phase_data["x"] = self.phase_data["x"][1:]
            self.phase_data["y"] = self.phase_data["y"][1:]
            self.phase_data["pens"] = self.phase_data["pens"][1:]
            self.phase_data["cursor"] = self.phase_data["cursor"]
    
    def run(self):
        while(True):
            self.trunkate_buffers(self.doppler_data)
            
            
            self.doppler_data["t"]=self.trunkate_buffers(self.doppler_data["t"])
            self.doppler_data["y"]=self.trunkate_buffers(self.doppler_data["y"])
            
            self.data_downloaded.emit(
                {"phase_data":self.phase_data,
                  "doppler_data":self.doppler_data, 
                  "bit_data":self.bit_data
                  
                  })
            self.msleep(400)

"""
This thread runs the gui. 
app.exec_() -> Enters the main event loop and waits until exit() is called.
Note that this is a python thread. There are also pyqt threads which are used
zfor gui specific tasks.
"""
live_plot_buffer = None


def gui_thread_pythread(threadName, delay):
    global window
    global live_plot_buffer

    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window()
    
    live_plot_buffer = GuiUpdateThread()
    live_plot_buffer.data_downloaded.connect(window.plot_from_thread)
    live_plot_buffer.start()
    
    window.show()
    # This will block until the window is closed, hence it runs in this thread.
    sys.exit(app.exec_())


def start_gui():
    _thread.start_new_thread(gui_thread_pythread, ("Thread-1", 2,))

    
start_gui()

# Race condition "prevention"
time.sleep(1)


######
def demo():
    import math
    import random
    t = 0
    
    while True:
        t += 0.1
        
        live_plot_buffer.doppler_data["t"].append(t)
        live_plot_buffer.doppler_data["y"].append(math.sin(t))
        
        dummy_real = []
        dummy_imag = []
        for i in range(400):
            r = random.uniform(0.0, 0.4)
            dummy_real.append(math.cos(t * 1000) + r)
            r = random.uniform(0.0, 0.4)
            dummy_imag.append(math.sin(t * 1000) + r)
            
        live_plot_buffer.push_phase_data(dummy_real, dummy_imag)
        
        live_plot_buffer.phase_data["cursor"]["x"]=[-1,1]
        live_plot_buffer.phase_data["cursor"]["y"]=[-1,1]
        
        
        # time.sleep(1)
        time.sleep(0.1)


if __name__ == "__main__":  
    demo()

