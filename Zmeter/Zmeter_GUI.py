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

from PyQt5 import Qt
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit,
                             QTextEdit, QGridLayout, QApplication)

import pyqtgraph as pg
import pyqtgraph.console
from pyqtgraph.parametertree import Parameter, ParameterTree

import ZmeterModule as Zmeter
import PyqtTools.FileModule as FileMod


class MainWindow(QWidget):
    ''' Main Window '''
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setFocusPolicy(Qt.Qt.WheelFocus)
        layout = Qt.QVBoxLayout(self)
        
        self.threadSerial = None
        
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
        
        self.btnStart = Qt.QPushButton("Start Gen and Adq!")
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
        grid.setSpacing(50)
        grid.addWidget(self.Console, 3, 1, 5, 1)

        layout.addWidget(self.treepar)
        layout.addWidget(self.btnStart)   
        layout.addWidget(self.TestMode)
        layout.addLayout(grid)
        layout.addWidget(namecommand)
        layout.addWidget(self.linecommands)
        layout.addLayout(hlayout)

        self.setGeometry(550, 300, 400, 700)
        self.setWindowTitle('MainWindow')
        self.show()
                
        self.btnStart.clicked.connect(self.on_btnStart)
        sendbutton.clicked.connect(self.SendUserInput)
        clearbutton.clicked.connect(self.ClearData)
        
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
    def on_btnStart(self):
        
        if self.threadSerial is None:
            print('started')
            self.treepar.setParameters(self.Parameters, showTop=False)
            print(self.PortSerieParams.PortSel.value())
            self.threadSerial = Zmeter.SerialThread(self.PortSerieParams.PortSel.value())
            self.threadSerial.NewLine.connect(self.on_NewLine)
            self.threadSerial.start()
            
            if self.threadSerial.alive:
                print('Connected to '+ self.PortSerieParams.PortSel.value())
            else:
                print('Error connecting to ' +self.PortSerieParams.PortSel.value())
                self.threadSerial.terminate()
                self.threadSerial = None
            
            self.btnStart.setText("Stop Gen")
            self.OldTime = time.time()
        
        else:
            print('stopped')
            self.threadSerial.close()
            print(self.PortSerieParams.PortSel.value() + ' closed')
            self.threadSerial.NewLine.disconnect()
            self.threadSerial.terminate()
            self.threadSerial = None

            self.btnStart.setText("Start Gen and Adq!")
            
    def on_NewLine(self):
        print('on_newline')
        print(self.threadSerial.ReadData)
        self.Console.append('>>>'+self.threadSerial.ReadData+'\n')
    
    def SendUserInput(self):
        print('WRITE')
        if self.threadSerial is not None:
            self.threadSerial.ThreadWrite.AddData(self.linecommands.text())
        self.Console.append('>'+self.linecommands.text()+'\n')
    
    def ClearData(self):
        self.linecommands.setText("")
        self.Console.Clear()
        
# #############################MAIN##############################
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())