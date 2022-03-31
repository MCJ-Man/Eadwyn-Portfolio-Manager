from PyQt5.QtCore import QRunnable, Qt, QThreadPool, QThread, pyqtSignal

import numpy as np

import asset_srch as ass

import sys
import os

import time

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

class RebalRisk(QThread):
    #worker_signal = Signal(str)
    change_value = pyqtSignal(int)
    
    def __init__(self, mw, SlideManager):
        super().__init__()
        self.mw = mw
        self.SlideManager = SlideManager
        
        self.continue_running = True
        
        print(f"Initialized RebalRisk")

    def run(self):
        SlideManager = self.SlideManager
        mw = self.mw
        print("runing blc risk calculation")
        asset_ars = [slid.wlw.search_ar for slid in SlideManager.sliders]
        blclist = np.array([slid.getValue()/100 for slid in SlideManager.sliders])
        #ret = totVal[-1]/totVal[0]
        
        ret_list = []
        for blc_intrvl in range(10,365,2):
            progress(blc_intrvl, 365)
            
            self.change_value.emit(blc_intrvl)
            
            blc_coam = np.array([ ass.multi_balance_crawler(asset_ars, blclist, 0, blc_intrvl, push)[0][:,-1].sum() 
                for push in range(1,blc_intrvl, 2) ])
            
            ret_list.append( blc_coam )
        
        
        #################################
        self.change_value.emit(365)
        ret_list = np.array(ret_list)
        
        """
        try:
            mw.progressBar.setValue(100)
            mw.label_10.setText(f"Calculation completed!")
        except: pass"""
        
        print("done running blc risk calculation")
        print(f" ret_list array is now shape {ret_list.shape}")
        
        np.save("tts", ret_list)
        #return ret_list
        
    #@Slot()  # <<-- This is recommended for stability ###########################################
    def kill(self):
        self.continue_running = False
        
    """
    def quadratize(self, noquad):
        
        l = max([len(n) for n in noquad])
        pass"""
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            