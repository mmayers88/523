import scipy.io as sio
import os,sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join
import heuristic as hu

samplerate = 22000

#=====================================================
#ML Settings
#=====================================================
pi = [0,0]
pi[0] = 1-(125/5512)
pi[1] = 125/5512
c = [[0, 0],[0 ,0]]
c[0][0] = 0 #TN
c[0][1] = 50 #FP
c[1][0] = 1 #FN
c[1][1] = 0 #TP
sigma =  0.024608749522845225

def makeRange(truePoints):
    start  = np.array([])
    end  = truePoints + 10
    for i in truePoints:
        #check within a second
        start = np.append(start,(i-30))
    return start,end

def sensAspec(dici,reg,data_points):
    if 0 not in  dici:
        dici[0] = 0
    if 1 not in  dici:
        dici[1] = 0
    for i in range(2,20):
        if i in dici:
            dici[1] += dici[i]

    fn = dici[0]
    tn = data_points-(reg)
    tp = int(dici[1])
    fp = (dici['pred']) - (tp) 
    if fp < 0:
        fp = 0
    print('fn:',fn,'tn:',tn,'tp:',tp,'fp:',fp)
    sens =  tp/(tp + fn)
    spec = 1-(fp/(fp+tn))
    PPV = tp/(tp+fp)
    NPV = tn/(tn+fn)
    print('Sensitivity: ',sens,'Specificity: ',spec)
    print("PPV: ",PPV,"NPV: ",NPV)
    return sens, spec, NPV, PPV

def veri(beg,end,steps):
    #print(beg,end)
    #beg=np.multiply(beg,samplerate)
    #end=np.multiply(end,samplerate)
    bins = [0] * len(beg)
    for i in range(len(beg)):
        for j in steps:
            #print(beg[i],j,end[i])
            if j <= end[i] and j >= beg[i]:
                bins[i] += 1
    #print(bins)            
    return bins

def predict(TP,pred):
    start,end = makeRange(TP)
    bins = veri(start,end,pred)
    #print("Correctness: {}%".format(veri(TP,pred)))
    stats = my_stats(bins,pred)
    sens,spec,NPV,PPV = sensAspec(stats,10,10000)
    return sens,spec,NPV,PPV    

def my_stats(arr,att):
    unique, counts = np.unique(arr, return_counts=True)
    stats = dict(zip(unique, counts))
    stats['pred'] = len(att)
    #print(stats)
    return stats






def getData(fName):
    mydir = os.getcwd()
    fol = "Archive/Data/"
    # Join various path components  
    fNames = os.path.join(mydir,fol,fName) 
    if fNames[-4:] != ".mat":
        fNames = fNames + '.mat'
    if os.path.isfile(fNames) == False:
        print("no file with that name!")
        return
    #print(fNames)
    data = sio.loadmat(fNames)
    #print(data.keys())
    #print(data['x'].shape[1])
    if data['x'].shape[1] is not 1:
        datax = data['x'].flatten()
    else:
        datax = data['x']
    spikes = data['si']
    return datax, spikes


def LHS(window,sig):
    lhs = 0
    for i,k in enumerate(window):
        lhs += k*(sig[i])
    return lhs


def Theta():
    theta = ((c[1][0]-c[0][0])*pi[0])/((c[0][1]-c[1][1])*pi[1])
    theta_log = np.log(theta)
    return theta_log
    
def RHS(sig):
    m1m0 = 0
    for i,k in enumerate(sig):
        m1m0 += k*(sig[i])
    rhs = (m1m0/2) + ((sigma+Theta())/(len(sig)*m1m0))
    return rhs


def likelihoodRatio(window,samp):
    rhs = RHS(samp)
    lhs = LHS(window,samp)
    #print(lhs,rhs)
    if lhs >= rhs:
        return True, lhs
    return False, lhs

def sigSearch(data, samp):
    windSize = len(samp)
    slide = windSize//4
    pos = np.array([])
    lhs_array = np.array([])
    for i in range(windSize,len(data),1):
        window = data[i-windSize:i]
        yay,lhs_sing = likelihoodRatio(window,samp)
        lhs_array = np.append(lhs_array,lhs_sing)
        if yay == True:
            pos = np.append(pos,i)
    return pos,lhs_array

def fileRead():
    mypath = os.getcwd()
    fol = "Archive/Data/"
    mypath = os.path.join(mypath,fol)
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

    onlyfiles=onlyfiles[:10]
    print(onlyfiles)
    statsData = np.array([0,0,0,0])
    for fi in onlyfiles:
        if fi[-4:] != '.mat':
            continue
        else:
            sens,spec,NPV,PPV = main(fi)
            temp = np.array([sens,spec,NPV,PPV])
            statsData = np.vstack((statsData,temp))
    #np.savetxt("muhStatsBest.csv", statsData, delimiter=",",fmt='%.4f')############################################

def main(fName):
    data,spikes = getData(fName)
    #print("len: ",len(data))
    meanSample = np.genfromtxt('meanBitch10.csv', delimiter=',').reshape(-1,1)  
    #print("Truth: ",len(spikes))
    time = np.linspace(0,len(data),len(data))
    pos,lhs_array = sigSearch(data,meanSample)
    #print("Lies: ",len(pos))
    
    #winds= np.linspace(len(meanSample),len(data),len(data)//(len(meanSample)//4)-3)
    fig, axs = plt.subplots(2)
    fig.suptitle('Predictions and Filtered')
    fig.set_size_inches(20,10)
    for i in pos:
        axs[0].axvline(i,color='orange')
    axs[0].plot(time, data)
    
    axs[1].plot(time[len(meanSample):],lhs_array)
    axs[1].axhline(RHS(meanSample),color = 'red')
    plt.show()
    
    
    #_,pos = hu.run(fName,1000,11,1,.1,0,1)
    sens,spec,NPV,PPV = predict(pos,spikes)
    '''
    plt.plot(time, data)
    plt.vlines(spikes[0],np.min(data),np.max(data),colors="red")
    plt.show()
    '''
    return sens,spec,NPV,PPV

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--fileName', '-f', default='MER0102', type=str,
                        help='The file name we want to process. Default: ^DJI.csv')
    args = parser.parse_args()

    #main(args.fileName)
    fileRead()