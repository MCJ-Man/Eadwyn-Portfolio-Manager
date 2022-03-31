#documantation: https://readthedocs.org/projects/investpy/downloads/pdf/latest/
# go to page 96 for search object methods

#matlab python doku: https://blogs.mathworks.com/loren/2020/03/03/matlab-speaks-python/#7cfcb146-9e87-4ead-b9f0-ad4ba34466fd

import quandl
import investpy
import numpy as np
import sys
import argparse
from datetime import date
import datetime
import pandas as pd

import matplotlib.pyplot as plt



def find(srch_key):
    """returns a list of all search quotes from investpy"""
    
    srch_objs = investpy.search_quotes(text=str(srch_key), n_results=10)
    #srch_objs = investpy.search_quotes("msci", n_results=10)

    
    symbols = [srch_obj.symbol for srch_obj in srch_objs]
    names = [srch_obj.name for srch_obj in srch_objs]
    countrys = [srch_obj.country for srch_obj in srch_objs]
    pair_types = [srch_obj.pair_type for srch_obj in srch_objs]
    exchanges = [srch_obj.exchange for srch_obj in srch_objs]

    return_array = np.array([ symbols, names, countrys, pair_types, exchanges ])
    return_array = return_array.T
    return_list = return_array.tolist()
    if __name__ == "__main__":
        for i, num in zip(return_list, range(len(return_list))):
            print("{} {}".format(num+1, i))
        
    return return_list
    
def find_assets(srch_key, n_results=10, products=None):
    """returns a list of all search quotes from investpy"""
    
    try:
        srch_objs = investpy.search_quotes(text=str(srch_key), products=products, n_results=n_results)
        
        symbols = [srch_obj.symbol for srch_obj in srch_objs]
        names = [srch_obj.name for srch_obj in srch_objs]
        countrys = [srch_obj.country for srch_obj in srch_objs]
        pair_types = [srch_obj.pair_type for srch_obj in srch_objs]
        exchanges = [srch_obj.exchange for srch_obj in srch_objs]

        displayStrings = ["[{}] \t {} {} {} {}".format(s, n, c, p, e) for s, n, c, p, e in zip(
                                                    symbols, names, countrys, pair_types, exchanges)]
    except: srch_objs, displayStrings = None, ["no results"]
    
    return srch_objs, displayStrings
    
def convdate(date, format):
    if format=="/": format = "%d/%m/%Y"
    if format=="-": format = "%Y-%m-%d"
    return date.strftime(format)

    
def ar_from_pand(data):
    muricatoday     = convdate( date.today()                                      , "-")
    muricatenyago   = convdate( date.today() - datetime.timedelta(days=365.25*50) , "-")
    data = data.asfreq('D', method="pad")
    loced_data = data.loc[muricatenyago:muricatoday]
    toar = np.ndarray.flatten(loced_data.to_numpy())
    return toar
    
def ar_from_srch_obj(srch_obj):
    today           = convdate( date.today()                                      , "/")
    muricatoday     = convdate( date.today()                                      , "-")
    tenyago         = convdate( date.today() - datetime.timedelta(days=365.25*50) , "/")
    muricatenyago   = convdate( date.today() - datetime.timedelta(days=365.25*50) , "-")
    
    data = srch_obj.retrieve_historical_data(tenyago, today)
    
    #if no entry on current date: copy data from most recent entry to current date (necessary for asfreq to work)
    """try:
        data.loc[muricatoday]
    except:
        data.loc[muricatoday] = data[-1:]
    
    data = data.asfreq('D', method="pad")"""
    
    data = data.asfreq('D', method="pad")
    
    try: loced_data = data.loc[muricatenyago:muricatoday][["Open", "High", "Low", "Close"]]
    except: loced_data = data.loc[muricatenyago:muricatoday]
    
    toar = loced_data.to_numpy()

    return toar
    
    
def sma(dat, day):
    #simple moving average
    sma = []
    if len(dat.shape) == 2:
        for i in range(len(dat)):
            if i < day:
                sma.append(sum(sum(dat[0:day])/day)/4)
            else:
                sma.append(sum(sum(dat[i-day:i])/day)/4)
        
    else:
        for i in range(len(dat)):
            if i < day:
                sma.append(sum(dat[0:day])/day)
            else:
                sma.append(sum(dat[i-day:i])/day)
                
    return np.array(sma)
    
    
def datclipperz(datlist):
    if len(datlist[0]) == datlist[0].shape[0]:
        lengz = np.array([len(x) for x in datlist]).min()       #save length of shortest data set in datlist
        cutlist = [x[-lengz:] for x in datlist]                  #cut every other data set to the length of the shortest one
        
    else:
        lengz = np.array([len(x[:,0]) for x in datlist]).min()
        cutlist = [x[-lengz:] for x in datlist]
    
    return cutlist
    
def normdat(dat, start=0, to=None, back=True):
    #norms input data (input can be shape infx4 or infx1
    #if backwards false: norms data from range [start] [to] 
    #
    if back is False:
        head = dat[:start]
        body = dat[start:]/np.mean(dat[start])
        dat = np.append(head,body, axis=0)
    else:
        #print(f"start is {start}")
        #print(f"dat shape is {dat.shape}")
        dat = dat/np.mean(dat[start])
    
    return dat

    
    
    
def give_info(srch_key, indx):
    srch_objs = investpy.search_quotes(text=str(srch_key), n_results=indx)
    try: srch_obj = srch_objs[-1]
    except: srch_obj = srch_objs
    info = srch_obj.retrieve_information()
    
    Type = srch_obj.pair_type
    Country = srch_obj.country
    try: Dividend = str(info["dividend"])
    except: Dividend = "-"
    try: EPS = str(info["eps"])
    except: EPS = "-"
    try: Mrkt_CP = info["marketCap"]
    except: Mrkt_CP = "-"
    Issuer = ""
    try: Exchange = info["exchange"]
    except: Exchange = "-"
    try: Beta = info("beta")
    except: Beta = "-"
    try: Xpense_Ratio = ""
    except: Xpense_Ratio = ""
    Creation = "older 5y"
    
    rtn_1a = info['oneYearReturn']
    
    today = date.today()
    dt1 = today - datetime.timedelta(days=365.25)
    dt3 = today - datetime.timedelta(days=365.25*3)
    dt5 = today - datetime.timedelta(days=365.25*5)

    data = srch_obj.retrieve_historical_data(convdate(dt5, "/") ,convdate(today, "/"))
    today_prce = (float(data.tail(1)["High"]) + float(data.tail(1)["Low"])) / 2
    rlyst_price = (float(data.head(1)["High"]) + float(data.head(1)["Low"])) / 2
    
    rtn_1a, rtn_3a, rtn_5a = "-", "-", "-"
    i=0
   
    return [Type, Country, Dividend, EPS, Mrkt_CP, Issuer, Exchange, Beta, Xpense_Ratio, Creation, str(round(rtn_1a,1)), str(round(rtn_3a,1)), str(round(rtn_5a,1)), vola_1a, vola_3a, vola_5a]



def multi_balance_crawler(datlist, blclist, normat=0, blc_intrvl=100, push=0, l=None):
    """ This function return a list of assets arrays with periodic re balancing according to its input parameters
    datlist: list of arrays of assets, must be 1xn. blclist: list of weighting for assets
    blc_intrvl: days between each balancing event
    normat: return arrays are normalized at given day (used for capital gain percentage from given date)
    normat can also be negative (relative to first day of input assets)
    push: first balancing occurs at first push=n. push is first balancing occurrence"""
    if sum(blclist) != 100:
        #print(f"blclist is: {blclist}")
        #print("Warning, blclist did not sum up to 100, adjusting values!")
        blclist = blclist/sum(blclist)
        blclist = list(blclist)
        #print(f"blclist now is: {blclist}")
        
    try: datlist = [np.mean(x, axis=1) for x in datlist]
    except: pass

    datlist = datclipperz(datlist)
    datlist = [normdat(dat, start=0) for dat in datlist]

    n_dtpts = datlist[0].size
    if l is None: l = range(push, n_dtpts, blc_intrvl)
    #print("l is now: {}".format([i for i in l]))
    
    #multiply weighting with each normalized asset array
    datlist = [x*w for x, w in zip(datlist, blclist)]
    
    #run algo for each balancing event (except for the first one)
    for i in range(0, len(l)):
        #if i == 0: break
        netvals = np.array([x[l[i]] for x in datlist])
        netsum = netvals.sum()                              #total value of portfolio
        netvals = [netsum*blc for blc in blclist]            #value of individual assets aft re balancing

        datlist = [normdat(x, start=l[i], back=False) for x in datlist]        
        datlist = [np.append(x[:l[i]], x[l[i]:]*netv, axis=0) for x, netv in zip(datlist, netvals)]  #data leak!
    
    if normat != 0:
        datlist = [normdat(dat, start=normat) for dat in datlist]
        datlist = [x*w for x, w in zip(datlist, blclist)]
        
    return np.array(datlist), l


def main():
    print("hello world!")
    """
    try:
        arg = str(sys.argv[1])
        typearg = False
    except:
        arg = input("Type your search in here: ")
        typearg = True
    print('lookup '+ arg)
    find(arg)
    if typearg: i = int(input("type the index arg (1-10): "))
    else: i = 1"""
    
    #give_info(arg, 1)
    #display_single_asset_plot(arg, i)
    

if __name__ == "__main__":
    main()