# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 09:09:12 2020

@author: Lucia
"""

from __future__ import print_function
import os
import sys
import numpy as np
import time
import pickle

from PyQt5 import Qt
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit,
                             QTextEdit, QGridLayout, QApplication)

import pyqtgraph as pg
import pyqtgraph.console
from pyqtgraph.parametertree import Parameter, ParameterTree
import matplotlib.pyplot as plt

import ZmeterModule as Zmeter
import PyqtTools.FileModule as FileMod


class MainWindow(QWidget):
    ''' Main Window '''
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setFocusPolicy(Qt.Qt.WheelFocus)
        layout = Qt.QVBoxLayout(self)
        
        self.threadSerial = None
        self.threadAcq = None
        
        # #############################Save##############################
        self.SaveStateParams = FileMod.SaveSateParameters(QTparent=self,
                                                          name='FileState',
                                                          title='Save/load config')
        
        # #############################File##############################
        self.FileParams = FileMod.SaveFileParameters(QTparent=self,
                                                      name='FileDat',
                                                      title='Save data')


        self.PortSerieParams = Zmeter.PortSerieParameters(QTparent=self,
                                                          name='PortSerie',
                                                          title='Port Serie Configuration')
        
        self.Parameters = Parameter.create(name='params',
                                            type='group',
                                            children=(self.SaveStateParams,
                                                      self.FileParams,
                                                      self.PortSerieParams,
                                                      )
                                            )
        
        self.Parameters.sigTreeStateChanged.connect(self.on_Params_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')
        
        self.btnConnect= Qt.QPushButton("Connect")
        self.btnStartMeas = Qt.QPushButton("Start Acq")
        self.TestMode = Qt.QCheckBox('Test Software Mode')        

        
        namecommand = Qt.QLabel('Send command:')
        self.linecommands = Qt.QLineEdit()
        sendbutton = Qt.QPushButton('Send')
        clearbutton = Qt.QPushButton('Clear')
        
        hlayout = Qt.QHBoxLayout()
        hlayout.addWidget(sendbutton)
        hlayout.addWidget(clearbutton)
        
        self.Console = QTextEdit()
        self.Console.setReadOnly(True)
        
        grid = QGridLayout()
        grid.setSpacing(150)
        grid.addWidget(self.Console, 3, 1, 5, 1)

        layout.addWidget(self.treepar)
        layout.addWidget(self.btnConnect)   
        layout.addWidget(self.btnStartMeas)   
        layout.addWidget(self.TestMode)
        layout.addLayout(grid)
        layout.addWidget(namecommand)
        layout.addWidget(self.linecommands)
        layout.addLayout(hlayout)

        self.setGeometry(450, 50, 700, 950)
        self.setWindowTitle('MainWindow')
        self.show()
        

        self.btnConnect.clicked.connect(self.on_btnConnect)
        self.btnStartMeas.clicked.connect(self.on_btnStartMeas)
        sendbutton.clicked.connect(self.SendUserInput)
        clearbutton.clicked.connect(self.ClearData)
      
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.SendUserInput()
            
# #############################Changes Control##############################
    def on_Params_changed(self, param, changes):
        print("tree changes:")
        for param, change, data in changes:
            path = self.Parameters.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
        print('  parameter: %s' % childName)
        print('  change:    %s' % change)
        print('  data:      %s' % str(data))
        print('  ----------')
              
# #############################START Real Time Acquisition ####################         
    def on_btnConnect(self):
        
        if self.threadSerial is None:
            print('started')
            self.treepar.setParameters(self.Parameters, showTop=False)
            # print(self.PortSerieParams.PortSel.value())
            self.threadSerial = Zmeter.SerialThread(self.PortSerieParams.PortSel.value())
            self.threadSerial.NewLine.connect(self.on_NewLine)
            self.threadSerial.start()
            
            if self.threadSerial.alive:
                print('Connected to '+ self.PortSerieParams.PortSel.value())
            else:
                print('Error connecting to ' +self.PortSerieParams.PortSel.value())
                self.threadSerial.terminate()
                self.threadSerial = None
            
            self.btnConnect.setText("Disconnect")
            self.OldTime = time.time()
        
        else:
            print('stopped')
            self.threadSerial.close()
            print(self.PortSerieParams.PortSel.value() + ' closed')
            self.threadSerial.NewLine.disconnect()
            self.threadSerial.terminate()
            self.threadSerial = None

            self.btnConnect.setText("Connect")
    
    def on_btnStartMeas(self):
        
        if self.threadSerial is not None:
            if self.threadAcq is None:
                print('started')
                self.treepar.setParameters(self.Parameters, showTop=False)
                self.threadSerial.ThreadWrite.AddData("MEAMEA 0")
                # En vez de MEAMEA 0 se puede hacer que lea de un fichero las instrucciones
                                
                self.threadAcq = Zmeter.Measure()
                self.threadAcq.MeaDone.connect(self.NewSample)
                self.threadAcq.NewMea.connect(self.NewMeasure)
                self.threadAcq.start()
                
                self.MeaArrayMAG = np.array([])
                self.MeaArrayPH = np.array([])
                self.MeaArrayFREQ = np.array([])
                
                self.threadBode = Zmeter.PlotBode()
                self.threadBode.start()
                
                self.btnStartMeas.setText("Stop Acq")
                self.OldTime = time.time()
        
            else:
                print('stopped')
                self.threadSerial.ThreadWrite.AddData("MEACAN")
                if self.FileParams.Enabled.value() is True:
                    self.SaveMeas(FileName=self.FileParams.FilePath(),
                                  Mag=self.MeaArrayMAG,
                                  Ph=self.MeaArrayPH,
                                  Freq=self.MeaArrayFREQ
                                  )
                self.PlotMea(Mag=self.MeaArrayMAG,
                             Ph=self.MeaArrayPH,
                             Freq=self.MeaArrayFREQ
                             )
                self.threadAcq.MeaDone.disconnect()
                self.threadSerial.terminate()
                self.threadSerial = None
    
                self.btnStartMeas.setText("Start Aqc")                
        else:
            print("Port not connected")
            
    def on_NewLine(self, data):
        # print('on_newline')
        self.Console.append('>>>'+data+'\n')
        if self.threadAcq is not None:
            if self.threadAcq.freqs is None:
                self.threadAcq.freqs = self.threadSerial.freqs
                self.threadAcq.value = self.threadSerial.value     
                self.threadAcq.Bode = self.threadSerial.Bode
            if data.startswith("M"):
                self.threadAcq.AddData(data)
        
    def SendUserInput(self):
        print('WRITE')
        if self.threadSerial is not None:
            self.threadSerial.ThreadWrite.AddData(self.linecommands.text())
        self.Console.append('>'+self.linecommands.text()+'\n')
        self.linecommands.setText("")
        
    def ClearData(self):
        self.linecommands.setText("")
        self.Console.clear()
        
    def NewSample(self, freq, val):
        # print("Freq is -->", freq)
        # print("Value is -->", val)
        print('NextFreq')
        
    def NewMeasure(self, freq, val, Bode):
        # print('BODE')
        #NO LE DA TIEMPO A PLOTEAR
        self.threadBode.AddData(Mag=Bode[:,0],
                                Ph=Bode[:,1],
                                w=2*np.pi*freq)
        print("Freq is -->", freq)
        print("Value is -->", val)
        print("Bode is -->", Bode)
        if self.MeaArrayMAG.shape[0] is 0:
            self.MeaArrayMAG = Bode[:,0].copy()
            self.MeaArrayPH = Bode[:,1].copy()
            # self.MeaArrayFREQ = 2*np.pi*freq
            self.MeaArrayFREQ = freq
        else:
            self.MeaArrayMAG = np.c_[self.MeaArrayMAG, Bode[:,0]]
            self.MeaArrayPH = np.c_[self.MeaArrayPH, Bode[:,1]]
            self.MeaArrayFREQ = np.c_[self.MeaArrayFREQ, freq]

    def PlotMea(self, Mag, Ph, Freq):
        fig, (axMag, axPh) = plt.subplots(2,1, sharex=True)

        for ind, (M, P, W) in enumerate(zip(Mag.transpose(), 
                                            Ph.transpose(), 
                                            Freq.transpose())):
            
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
        
    def SaveMeas(self, FileName, Mag, Ph, Freq):
        self.FileName = FileName
        self.DictMea = {'Magnitude': Mag,
                        'Phase': Ph,
                        # 'w': 2*np.pi*Freq,
                        'w': Freq,
                        }

        with open(self.FileName, "wb") as f:
            pickle.dump(self.DictMea, f)

        print('Saved')      
        
# #############################MAIN##############################
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())