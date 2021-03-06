import time
from PyQt5.QtGui import*
from PyQt5.uic import*
from PyQt5.QtCore import QDate, QRunnable, Qt, QThreadPool

#from PyQt5.QtWidgets import QApplication, QWidget, QListWidget
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets

import investpy
import quandl
quandl.ApiConfig.api_key = "towPrUKzQkPs37W1A-2o"

import pickle
import copy
import sip

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

import asset_srch as ass
import sys
import numpy as np

from datetime import date
import datetime
from dateutil.relativedelta import relativedelta

import os
#os.chdir("C:\\Users\\JMCrosair\\OneDrive\\00 Finance")
################

from risk_calculator import RebalRisk


class Window2(QMainWindow):                           # <===
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Window22222")
        loadUi('plotwindow.ui', self)

class Canvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=5, dpi=100):
        #self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig = Figure(dpi=dpi, figsize=(width, height))
        FigureCanvas.__init__(self, self.fig)
        
        self.setParent(parent)
        self.ax = self.figure.add_subplot(111)
        
        #make transparent and do some formating
        self.fig.tight_layout(pad=1.08, h_pad=None, w_pad=None, rect=None)
        self.setStyleSheet("background-color:transparent;")
        self.figure.patch.set_facecolor("None")
        self.fig.patch.set_alpha(0.0)
        self.ax.patch.set_alpha(0.0)
        
        ################Formating#################################
        self.fig.subplots_adjust(   left=0.0,
                                    bottom=0.04, 
                                    right=0.990, 
                                    top=1, 
                                    wspace=0.0, 
                                    hspace=0.0)
        ##########################################################
        self.ln = None
        
    def remplot(self, ln):
        ln.remove()
        self.ax.relim()
        self.draw()
        self.ax.relim()
        print("i was run and relimited 2x")
 
    def plot(self, x, y, override=True):
        self.ax.grid(True)
        
        ln, = self.ax.plot(x, y)
        if override:
            if self.ln is not None: self.ln.remove()
            self.ln = ln
            
        else: pass
        
        self.ax.relim()
        self.draw()
        return ln
        
    def tickerplot(self, x):
        ln, = self.ax.plot(x)
        self.fig.patch.set_alpha(0.0)
        self.ax.patch.set_alpha(0.0)
        self.ax.axis('off')
        self.draw()
    
        
class SlideWidget(QWidget):
    def __init__(self, wlw):
        super().__init__()
        loadUi('slideWidget.ui', self)
        self.wlw = wlw
        self.setValue(5)
        
        self.horizontalSlider.setMaximum(1000)
        self.horizontalSlider.setMinimum(1)
        self.spinBox.setMaximum(100)
        self.spinBox.setMinimum(0.01)
        self.horizontalSlider.valueChanged.connect(self.sliderAction)
        #self.horizontalSlider.valueChanged.connect(SlideManager.adjustWeights)
        SlideManager.register(self)
        
    def setValue(self, val):
        if val <= 0.00:
            print("was instructed to set smaller 0 (got: {}), setting to 0".format(val))
            val = 0
        elif val >= 100.0001:
            print("was instructed to set larger 100 (got: {}), setting to 100".format(val))
            val = 100
    
        self.value = val
        self.horizontalSlider.setValue(int(val*10))
        self.spinBox.setValue(val)
        
    def getValue(self):
        if self.value >= 0 and self.value <= 100:
            return self.value
        else: print("error!!!!!!!!!!!!")
        
    def sliderAction(self):
        #print(self.horizontalSlider.value())
        self.value = float(self.horizontalSlider.value()) / 10
        self.spinBox.setValue(self.value)
        #SlideManager.recalc(self)
        self.wlw.mw.plotBalanced()
        
class SlideManager():
    sliders = []
    lastActuated = None

    def __init__(self):
        pass

    def register(issuer):
        SlideManager.sliders.append(issuer)
        x = sum([slid.getValue() for slid in SlideManager.sliders])
        issuer.setValue(100-x)
        
    def unregister(issuer):
        SlideManager.sliders.remove(issuer)
        x = sum([slid.getValue() for slid in SlideManager.sliders])
        for slid in SlideManager.sliders:
            val = slid.getValue()
            slid.setValue(100/x)
        
    def recalc(issuer):
        SlideManager.lastActuated = issuer
        val = issuer.getValue()
        #print("value gotten by getValue(): {}".format(val))
        
        allvals = sum([slid.getValue() for slid in SlideManager.sliders])
        othervals = sum([slid.getValue() if slid is not issuer else 0 for slid in SlideManager.sliders])
        if othervals == 0: scaledown = 1
        else:
            scaledown = (100 - val) / othervals
        
        #print("scaledown: {}".format(scaledown))
        
        #[slid.setValue(slid.getValue() * scaledown) for slid in SlideManager.sliders ]
        
        
        for slid in SlideManager.sliders:
            if slid is not issuer:
                slid.setValue(slid.getValue() * scaledown)
                
    def adjustWeights():
        ultraverbose = False
        if ultraverbose: print("running adjustWeights function...")
        sumslidval = sum([slid.getValue() for slid in SlideManager.sliders])
        if ultraverbose: print(f"sumslidval, the sum of all slider values is: {sumslidval}")
        
        for en, slid in enumerate(SlideManager.sliders):
            if ultraverbose:
                print("=====================")
                print(f"slider number: {en}")
                print(f"has value {slid.getValue()}")
                print(f"is divided by {sumslidval}")
                print("then multiplyed by 100")
            
            slid.setValue( slid.getValue() / sumslidval *100 )
            #slid.setValue( slid.getValue() / sumslidval *100 )
            if ultraverbose:
                print(f"was set to {slid.getValue() / sumslidval *100}")
                print("====================")
                print(f"sum of all value is {sum([slid.getValue() for slid in SlideManager.sliders])}")
            

    
class WatchWidget(QWidget):
    def __init__(self, mw, name, search_ar, parent=None):
        super().__init__()
        self.setParent(parent)
        loadUi('watchlistWidget.ui', self)
        #self.watchlistCheckBox.stateChanged.connect(self.wlwCheckboxInSrch)
        self.watchlistCheckBox.stateChanged.connect(mw.plotSearch)
        
        self.minicanv = Canvas(self, width=138, height=25)
        self.minicanv.tickerplot(search_ar)
        self.mw = mw
        #self.ln = mw.canvas.plot(x=self.mw.time4xax(search_ar), y=search_ar, override=False)
        self.search_ar = search_ar
        
        self.slw = SlideWidget(self)
        #c = mw.slideLayout.count()
        mw.slideLayout.insertWidget(1, self.slw)
        
        self.label.setText(name)
        self.setToolTip(name)
        self.miniCanvLay.addWidget(self.minicanv)
        self.mw.updateNormAt_srch()
        
        self.remWatchButton.clicked.connect(self.removeMyself)
        
    def wlwCheckboxInSrch(self):
        if self.watchlistCheckBox.isChecked():
            sa = self.search_ar
            ln = self.mw.canvas.plot(x=self.mw.time4xax(sa), y=sa, override=False)
            self.ln = ln
        else:
            self.mw.canvas.remplot(self.ln)
        
    def removeMyself(self):
        print(f"my name is {self.label.text()}, I executed the removeMyself function")
        SlideManager.unregister(self.slw)
        self.mw.slideLayout.removeWidget(self.slw)
        sip.delete(self.slw)
        self.mw.watchListScrollLayout.removeWidget(self)
        sip.delete(self)
        
        try:
            self.mw.canvas.remplot(self.ln)
        except: pass
        
        
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("Layout.ui", self)
        self.move(50, 50)
        
        self.setWindowTitle("PyQt Portfolio Manager")
        self.srchPushButton.clicked.connect(self.getSearchQ)
        self.viewButton.clicked.connect(self.plotSearch)
        self.add2WatchButton.clicked.connect(self.add2watch)
        
        self.srch_objs = None
        self.search_ar = None
        
        #self.searchbar_checkBox.stateChanged.connect(self.search_hider)
        
        #initialize main plot on search tab
        self.canvas = Canvas(self, width=8, height=4)
        self.graphLayout.addWidget(self.canvas)
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.graphLayout.addWidget(self.navi_toolbar)
        
        #initialize tools on search tab
        self.srchResLstWdgt.currentItemChanged.connect(self.search_res_change)
        self.normCheckBox.stateChanged.connect(self.plotSearch)
        
        #initialize balance plot
        self.balCanvas = Canvas(self, width=8, height=4)
        self.bal_navi_toolbar = NavigationToolbar(self.balCanvas, self)
        
        self.naviLayout.addWidget(self.bal_navi_toolbar)
        self.balanceGraphLayout.addWidget(self.balCanvas)
        
        #self.normat = 0
        self.balanceLen = 0
        #self.normatButton.clicked.connect(self.normatFunction)
        
        #connect buttons on balance page
        self.weightButton.clicked.connect(SlideManager.adjustWeights)
        self.weightButton.clicked.connect(self.updateLCD)
        self.debugButton.clicked.connect(self.printSliderval2console)
        self.plotBalancedButton.clicked.connect(self.plotBalanced)
        
        #reference indices in combobox
        comb_boxes = [self.srch_RefComboBox, self.bal_RefComboBox]
        for comb in comb_boxes:
            #comb.addItem("MSCI ACWI")  #miwd00000pus
            comb.addItem("Inflation GER")  #miwd00000pus
            comb.addItem("Inflation EUR")  #miwd00000pus
            comb.addItem("Inflation USA")  #miwd00000pus
            comb.addItem("Home Price USA")  #miwd00000pus
            #comb.addItem("S&P 500")  #miwd00000pus
            #comb.currentIndexChanged.connect(self.comboBoxChange)
            
        self.srch_refCheckBox.stateChanged.connect(self.plotSearch)
        self.bal_refCheckBox.stateChanged.connect(self.plotBalanced)
        
        self.reference_indices = [
            #np.mean(ass.ar_from_srch_obj(investpy.search_quotes(text=str("msci world"))[1]), axis=1),
            ass.ar_from_pand(quandl.get("RATEINF/CPI_DEU")),
            ass.ar_from_pand(quandl.get("RATEINF/CPI_EUR")),
            ass.ar_from_pand(quandl.get("RATEINF/CPI_USA")),
            ass.ar_from_pand(quandl.get('YALE/NHPI', authcode='authcode', key='towPrUKzQkPs37W1A-2o')),
            #np.mean(ass.ar_from_srch_obj(investpy.search_quotes(text=str("s&p 500"))[1]), axis=1),
            ]
        self.srch_RefComboBox.currentIndexChanged.connect(self.plotSearch)
        self.bal_RefComboBox.currentIndexChanged.connect(self.plotBalanced)
        
        #Balancing Interval Assistant
        self.spinBox.valueChanged.connect(self.plotBalanced)
        d = date.today()
        self.rebalDateEdit.setMinimumDate(QDate(d.year, d.month, d.day))
        
        #Risk calculators
        self.blc_riskCalc.clicked.connect(self.blcAsst)
        self.towindowButton.clicked.connect(self.to_window)
        
        self.balriskCanvas = Canvas(self)
        self.rebalRiskGraphLayout.addWidget(self.balriskCanvas)
        
        #save load settings toolbar
        self.loadButton.clicked.connect(self.w_load)
        self.saveButton.clicked.connect(self.w_save)
        self.saveAsButton.clicked.connect(self.w_saveAs)
        
        
        #add some items to watchlist
        if False:
            for s in ["msci", "btc"]:
                self.lineEdit.setText(s)
                self.getSearchQ()
                self.srchResLstWdgt.setCurrentRow( 1 )
                self.plotSearch()
                self.add2watch()
                
                
    def w_save(self):
        srch_quotes = [slid.wlw.srch_obj for slid in SlideManager.sliders]
        filename = "test.pk1"
        
        with open(filename, 'wb') as outp:  # Overwrites any existing file.
            pickle.dump(srch_quotes, outp, pickle.HIGHEST_PROTOCOL)
        print("exect save")
        pass
        
    def w_load(self):
        print("exect load")
        [slid.wlw.removeMyself() for slid in SlideManager.sliders]
        
        filename = "test.pk1"
        with open(filename, 'rb') as inp:
            srch_quotes = pickle.load(inp)
            
        for srch_obj in srch_quotes:
            #self.srch_quotes = srch_quote

            search_ar = ass.ar_from_srch_obj(srch_obj)
            search_ar = np.mean(search_ar, axis=1)
            self.search_ar = search_ar
            ######################################
            
            self.name = srch_obj.name
            wlw = WatchWidget(self, srch_obj.name, search_ar)
            self.watchListScrollLayout.insertWidget(0,wlw)
            
            wlw.srch_obj = srch_obj
                
            self.plotSearch()
            
        
    def w_saveAs(self):
    
        print("exect saveAs, not implemented!")
        pass
        
        
                
    def updateNormAt_srch(self):
        def timedel(i): return date.today() - datetime.timedelta( i )
        dates = [timedel(len(slid.wlw.search_ar)) for slid in SlideManager.sliders]
        if self.searchbar_checkBox.isChecked(): dates.append(timedel( len(self.search_ar)))
        d = max(dates)
        self.normDateEdit_srch.setMinimumDate(QDate(d.year, d.month, d.day))
        self.normDateEdit_bal.setMinimumDate(QDate(d.year, d.month, d.day))
        #self.normDateEdit_srch.setDate(QDate(d.year, d.month, d.day))
        e = date.today()
        self.normDateEdit_srch.setMaximumDate(QDate(e.year, e.month, e.day))
        self.normDateEdit_bal.setMaximumDate(QDate(e.year, e.month, e.day))
        return int((d-e).days + 1)
    
    def dispReference(self):
        self.plotBalanced()
    
    def search_res_change(self):
        srch_obj = self.srch_objs[self.srchResLstWdgt.currentRow()]
        search_ar = ass.ar_from_srch_obj(srch_obj)
        self.search_ar = np.mean(search_ar, axis=1)
    
    def comboBoxChange(self):
        print("x")
        #print(self.comboBox.currentText())
        
    def plotSearch(self):
        if self.srch_objs is None: return None
        if self.search_ar is None: return None
        
        ax5 = self.canvas.ax
        fig = self.canvas.figure
        
        self.canvas.xbd, self.canvas.ybd = self.canvas.ax.get_xbound(), self.canvas.ax.get_ybound()
        ax5.cla()
        ax5.grid(True)
        

        search_ar = self.search_ar
        
        self.updateNormAt_srch()
        
        #acquire all asset-arrays
        asset_ars = [slid.wlw.search_ar for slid in SlideManager.sliders if slid.wlw.watchlistCheckBox.isChecked()]
        if self.searchbar_checkBox.isChecked(): asset_ars.append(search_ar)
        
        #norm assets
        if self.normCheckBox.isChecked():
            qd = self.normDateEdit_srch.date()
            y, m, d = qd.year(), qd.month(), qd.day()
            backday = int( (date(y, m, d) - date.today()).days )
            asset_ars = [ass.normdat(ar, start=backday) for ar in asset_ars]
            
            #add reference index if needed
            if self.srch_refCheckBox.isChecked():
                ref_ar = self.get_ref_ar(self.srch_RefComboBox.currentIndex())
                ref_ar = ass.normdat(ref_ar, start=backday)
                ax5.plot(self.time4xax(ref_ar), ref_ar, "r--")
            
            #plot norm lines
            if self.checkBox_vertical.isChecked(): ax5.axvline(date(y, m, d), 0, 1, color="red", linestyle="-")
            if self.checkBox_oneline.isChecked(): ax5.axhline(y=1, color="black", linestyle="-")
            if self.checkBox_zeroline.isChecked(): ax5.axhline(y=0, color="black", linestyle="-")
            

        [ax5.plot(self.time4xax(ar), ar) for ar in asset_ars]
        #self.temp_ln = self.canvas.plot(x=self.time4xax(search_ar), y=search_ar)
        
        
        #handle ax formatting
        if self.autoframe_2.isChecked():
            ax5.relim()

        else:
            ax5.set_xbound(*self.canvas.xbd)
            ax5.set_ybound(*self.canvas.ybd)
            

        
        self.canvas.draw()
        
        
        
    def plotBalanced(self, plotBypass=False):
        """this function is executed every time an event prompts balancePlot to redraw"""
        asset_ars = [slid.wlw.search_ar for slid in SlideManager.sliders]
        blclist = np.array([slid.getValue()/100 for slid in SlideManager.sliders])
        if len(asset_ars) <= 1:
            print("Warning, not enough assets contained in your watch list")
            return None
        
        ax5 = self.balCanvas.ax
        fig = self.balCanvas.figure
        
        self.balCanvas.xbd, self.balCanvas.ybd = self.balCanvas.ax.get_xbound(), self.balCanvas.ax.get_ybound()
        ax5.cla()      
        
        
        #determine norm date for assets 
        if self.normCheckBox_bal.isChecked():                               #Execute this when norm is ticked 
            qd = self.normDateEdit_bal.date()
            y, m, d = qd.year(), qd.month(), qd.day()
            backday = int( (date(y, m, d) - date.today()).days )
        else:
            backday = 0
            
        
        lengz = np.array([len(x) for x in asset_ars]).min()
        blc_intrvl, push, l = self.interval_assistant(lengz)
        
        #run data through balance crawler 
        dlist, l = ass.multi_balance_crawler(asset_ars, blclist, backday, blc_intrvl, push, l)
        
        
        ##get proper x-axis ticks:
        dayz = np.array(self.time4xax(np.array(range(0,len(dlist[0])))))    #needed as x-axis used in plt.plot(x, y) as x
        balanceDayz = dayz[np.array(l)]                                     #days on which balancing takes place
        
        ##draw balancing event markers##
        #for day in balanceDayz:
        [ax5.axvline(day, 0, 1, color="black", linestyle="--", linewidth=0.25) for day in balanceDayz]
        
            
        ##draw plots##
        totPrtflioValue = np.array(dlist).sum(axis=0)
        ax5.plot(dayz, totPrtflioValue, "r", label=("all assets"))
        
        ax5.fill_between(dayz, dlist[0])
        for i in range(len(dlist)-1):
            #print(f"loop index nmb: {i}")
            try: yy+=dlist[i]
            except: yy=dlist[0]
            ax5.fill_between(dayz, yy+dlist[i+1], y2=yy)
        
        ##Benchmark Index##
        if self.bal_refCheckBox.isChecked():
            ref_ar = self.get_ref_ar(self.bal_RefComboBox.currentIndex())
            ref_ar = ass.normdat(ref_ar[-len(dayz):], start=backday)
            
            print("============================")
            print(f"reference_msci.shape = {self.reference_indices[0].shape}")
            print(f"refar.shape = {ref_ar.shape}")
            print(f"dayz.shape = {dayz.shape}")
            print("============================")
            
            ax5.plot(dayz, ref_ar, "r--")
            
        #plot lines
        if self.checkBox_vertical_bal.isChecked(): ax5.axvline(dayz[backday], 0, 1, color="red", linestyle="-")
        if self.checkBox_oneline_bal.isChecked(): ax5.axhline(y=1, color="black", linestyle="-")
        if self.checkBox_zeroline_bal.isChecked(): ax5.axhline(y=0, color="black", linestyle="-")
        
        #handle ax formatting
        ax5.tick_params(axis="y",direction="in", pad=-22)
        ax5.tick_params(axis="x",direction="in", pad=-15)
        ax5.yaxis.tick_right()
        if self.autoframe.isChecked():
            ax5.relim()
            ax5.set_ylim(bottom=0)
        else:
            ax5.set_xbound(*self.balCanvas.xbd)
            ax5.set_ybound(*self.balCanvas.ybd)
        
        self.balCanvas.draw()
        
        #########handle balancing assistant
        
    def interval_assistant(self, n_dtpts):
        if self.intervalAssistantTab.currentIndex() == 0:
            blc_intrvl = None
            push = None
        
            qd = self.rebalDateEdit.date()
            dte = date(qd.year(), qd.month(), qd.day())
            
            #backday = int( (date(y, m, d) - date.today()).days )
            
            rly = date.today() - datetime.timedelta(int(n_dtpts))
            
            months = [1, 3, 6, 12][self.freqencyComboBox.currentIndex()]
            
            dte_li = []
            #backward
            while len(dte_li)<50000:
                dte -= relativedelta(months=months)
                if dte < rly:
                    break
                else:
                    if dte < date.today():
                        dte_li.append(dte)
            
            dte_li = dte_li[::-1]
            l = np.array([(d-rly).days for d in dte_li])
        
        else:
            blc_intrvl = self.spinBox.value()
            push = self.blc_day_dial.value()
            l = None
            
        
        return blc_intrvl, push, l
        
        
    def blcAsst(self):
        #############################################################
        print("blcAsst() called, now initiating Thread")
        self.progressBar.setValue(int(0))
        
        threadCount = QThreadPool.globalInstance().maxThreadCount()
        self.label_10.setText("Running Calculation...")
        #############################################################
        
        #self.thread = MyThread()
        self.thread = RebalRisk(self, SlideManager)
        self.thread.change_value.connect(self.setProgressVal)
        self.thread.start()
        
    def to_window(self):
        self.w = Window2()
        
        self.w.canv = self.balriskCanvas#Canvas(self, width=8, height=4)
        self.w.navi_tolb = NavigationToolbar(self.w.canv, self.w)
        
        self.w.verticalLayout.addWidget(self.w.canv)
        self.w.verticalLayout.addWidget(self.w.navi_tolb)
        
        self.w.show()
        #self.w.hide()
        
        
        #XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  
    def setProgressVal(self, val):
        self.progressBar.setValue( int((val/365)*100) )
        if val == 365:
            self.label_10.setText("Task completed!")
            
            time.sleep(5)
            ax5 = self.balriskCanvas.ax
            ax5.cla()
            
            ax5.axhline(y=1, color="black", linestyle="-")
            ax5.axhline(y=0, color="black", linestyle="-")
            
            ar = np.load("tts.npy", allow_pickle=True)
            self.balriskCanvas.ax.boxplot(ar)
            
            m = max([max(n) for n in ar])
            
            ax5.relim()
            ax5.set_ylim(bottom=0)
            ax5.set_ylim(top=m)
            
            self.balriskCanvas.draw()
        
    def get_ref_ar(self, i):
        print(i)
        return np.copy(self.reference_indices[i])
        
    def normatFunction(self):
        normat = 150
        self.normat = normat
    
    def updateLCD(self):
        sumslid = sum([slid.getValue() for slid in SlideManager.sliders])
        self.lcdNumber.display(sumslid)
        
    def printSliderval2console(self):
        print("\n\/ \/ \/ \/ \/ \/ ")
        stringz = ["value of slider in list position {} is:   {}".format(en, slid.getValue()) for en, slid in enumerate(SlideManager.sliders)]
        for stri in stringz[::-1]: print(stri)
        print("/\ /\ /\ /\ /\ /\ \n")

    def getSearchQ(self):
        self.srchResLstWdgt.clear()
        srch_trm = self.lineEdit.text()
        
        products = ["indices", "stocks", "etfs", "funds", "commodities", "currencies",
            "cryptos", "bonds", "certificates", "fxfutures"]
        cbs = [self.cb_0, self.cb_1, self.cb_2, self.cb_3, self.cb_4, self.cb_5, self.cb_6, self.cb_7, self.cb_8, self.cb_9]
        prods = []
        for prod, cb in zip(products, cbs):
            if cb.isChecked(): prods.append(prod)
            
        self.srch_objs, displayStrings = ass.find_assets(srch_trm, products=prods, n_results=25)
        
        for dispStr in displayStrings:
            self.srchResLstWdgt.addItem(dispStr)
        
          
        
    def time4xax(self, ar, endtime=0):
        """returns list of datetime_objects matching to input array"""
        time_delta_ar = [(date.today() - datetime.timedelta(days=i)) for i in range(len(ar))][::-1]
        return time_delta_ar
    def realtime4xax(self, ar, endtime=0):
        """input integer in days from start"""
        time_delta_ar = [(date.today() - datetime.timedelta(days=i-endtime)) for i in ar[::-1]]
        return time_delta_ar

    def add2watch(self):
        if self.srch_objs is None: return None
        srch_obj = self.srch_objs[self.srchResLstWdgt.currentRow()]
        search_ar = self.search_ar
        #print(srch_obj)
        self.name = srch_obj.name
        
        wlw = WatchWidget(self, srch_obj.name, search_ar)
        #c = self.watchListScrollLayout.count()
        self.watchListScrollLayout.insertWidget(0,wlw)
        
        wlw.srch_obj = srch_obj
        
    def search_hider(self):
        if self.searchbar_checkBox.isChecked():
            sa = self.search_ar
            ln = self.canvas.plot(x=self.time4xax(sa), y=sa, override=False)
            self.temp_ln = ln
        else:
            self.canvas.remplot(self.temp_ln)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec_()
    
    
    
    
    