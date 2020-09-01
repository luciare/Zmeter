# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 13:12:06 2020

@author: -
"""

import pickle 
import matplotlib.pyplot as plt

File = r"C:\Users\Lucia\Dropbox (ICN2 AEMD - GAB GBIO)\TeamFolderLMU\FreqMux\Lucia\ZMeter"  
Name = "\TestSaveData.h5"
FileName = File+Name
with open(FileName,"rb") as f:
    Mea= pickle.load(f, encoding='latin1')

fig, (axMag, axPh) = plt.subplots(2,1, sharex=True)

for ind, (M, P, W) in enumerate(zip(Mea['Magnitude'].transpose(), 
                                    Mea['Phase'].transpose(),
                                    Mea['w'].transpose())):
    axMag.semilogx(W, M, label='MEA'+str(ind))
    axPh.semilogx(W, P, label='MEA'+str(ind))

axMag.set_ylabel('Magnitude', fontsize=15)
axPh.set_ylabel('Phase', fontsize=15)
axPh.set_xlabel('Freq(W)', fontsize=15)

axMag.tick_params(direction='out', length=10, width=3, colors='black',
               grid_color='black', grid_alpha=0.5, labelsize=13)
axPh.tick_params(direction='out', length=10, width=3, colors='black',
               grid_color='black', grid_alpha=0.5, labelsize=13)

plt.legend()