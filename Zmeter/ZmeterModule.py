# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 08:53:12 2020

@author: Lucia
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
from PyQt5 import Qt
from PyQt5.QtCore import QThread, pyqtSignal
from serial.tools import list_ports

import numpy as np
import copy
import serial
import threading
import serial

PortSerie = ({'name': 'PortSerieConfig',
              'type': 'group',
              'children': ({'name': 'Load Ports',
                            'type': 'action'},
                           {'name': 'Selected Port',
                            'type': 'str',
                            'readonly': True,
                            'value': "Com1"},
                           {'name': 'Ports List',
                            'type': 'list',
                            'values': ['Com1'],
                            'value': 'Com1'},
                           )
            })

class PortSerieParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        ###############Config Parameters#############################
        self.addChild(PortSerie)
        self.PortSerieConfig = self.param('PortSerieConfig')
        self.PortList = self.PortSerieConfig.param('Ports List')
        self.PortSel = self.PortSerieConfig.param('Selected Port')
        
        self.PortSerieConfig.param('Load Ports').sigActivated.connect(self.LoadPorts)
        self.PortList.sigValueChanged.connect(self.SetPort)
        
    def LoadPorts(self):
        print('Loading Ports')
        self.Info = list_ports.comports()
        self.List = []
        self.Ports = []
        for port in self.Info:
            self.List.append(port.description)
            self.Ports.append(port.device)
        self.ChangeValuesList()
        
    def ChangeValuesList(self):
        self.PortSerieConfig.param('Ports List')
 
        print('Ports Loaded')
        cc = copy.deepcopy(PortSerie)

        for ind, child in enumerate(cc['children']):
            if child['name'] == 'Ports List':
                child['values'] = self.List
                tupleNum = ind

        self.PortSerieConfig.removeChild(self.PortList)
        self.PortSerieConfig.addChild(cc['children'][tupleNum])

        self.PortList = self.PortSerieConfig.param('Ports List')
        self.PortList.sigValueChanged.connect(self.SetPort)

    def SetPort(self):
        for ind, data in enumerate(self.List):
            if data == self.PortList.value():
                self.PortSel.setValue(self.Ports[ind])
                
# #############################THREAD ########################################
                
class SerialThread(Qt.QThread):
    NewLine = Qt.pyqtSignal(str)

    def __init__(self, port, baudrate=115200, parity=None, bytesize=8, stopbits=1, timeout=1, parent = None):
        super(SerialThread,self).__init__(parent)
        try: 
            self.my_serial = serial.Serial()
            self.my_serial.port = port              
            self.my_serial.baudrate = baudrate       
            self.my_serial.bytesize = bytesize      
            self.my_serial.stopbits = stopbits     
            self.my_serial.timeout = timeout
    
            self.ThreadRead = ReadSerial(self.my_serial)
            self.ThreadRead.ReadDone.connect(self.PrintReadData)
            
            self.ThreadWrite = WriteSerial(self.my_serial)
            self.ThreadWrite.WriteDone.connect(self.PrintWritenData)

        except Exception as error:
            print(str(error))

    def start(self):
        try:
            self.my_serial.open()

            if self.my_serial.isOpen():
                self.alive = True
                self.ThreadRead.start()
                self.ThreadWrite.start()
                return True
            
            else:
                self.alive = False
                return False
        
        except Exception as error:
            print(str(error))
            pass
    
    def PrintReadData(self, data):
        self.ReadData = data
        # print(self.ReadData)
        self.NewLine.emit(self.ReadData)

    def PrintWritenData(self):
        self.WritenData = self.ThreadWrite.WriteData
        # print(self.WritenData)
            
    def close(self):
        if self.my_serial.is_open == True:
            self.my_serial.close()
            self.alive = False
            print ('closing ' , self.my_serial.port)
            pass
        else: 
            print(self.my_serial.port , ' already closed')


class WriteSerial(Qt.QThread):
    WriteDone = Qt.pyqtSignal()
    
    def __init__(self, portSerial):
        super(WriteSerial, self).__init__()
        self.my_serial = portSerial
        self.Data = None
    
    def run(self):
        while True:
            if self.Data is not None:
                try:
                    # print(self.Data)
                    data1 = [ord(c) for c in self.Data]
                    chk = 0
                    for d in data1:
                        chk = chk ^ d
                    data_out = '\x01' + '{:02x}'.format(len(self.Data)) + '\x02' + self.Data + '\x03' + '{:02x}'.format(chk) + '\x04'
                    self.WriteData = data_out.encode('utf-8')
                    WriteOk = self.my_serial.write(self.WriteData)                
                    if WriteOk == len(self.WriteData):
                        self.WriteDone.emit()
                        self.Data = None
                        
                except Exception as ex:
                    print('No hace el write')
                    print(ex)  
                
    def AddData(self, NewData):
        if self.Data is not None:
            print("Previous Data not Sent")
        self.Data = NewData
        
        
class ReadSerial(Qt.QThread):
    ReadDone = Qt.pyqtSignal(str)
    
    def __init__(self, portSerial):
        super(ReadSerial, self).__init__()
        self.my_serial = portSerial
        
    def run(self):
        while True:
            try:
                n = self.my_serial.inWaiting()                       
                if n:
                    data = self.my_serial.read(n).decode()   
                    # print('READIN -->', n, len(data), data)
                    self.LineFinder(data)
                    # self.ReadDone.emit()
                    
            except Exception as ex:
                print(ex)
    
    def LineFinder(self, InputData):
        self.state = 0
        for d in InputData:
            if d == '\x15':
                print('NAK')
                continue
            
            if self.state == 0:
                if d == '\x01':
                    self.state += 1
                    self.tempLine = ''
                    self.Length = ''
            elif self.state == 1:
                if (d != '\x02'):
                    self.Length = self.Length + d            
                else:
                    self.state += 1
            elif self.state == 2:
                if (d != '\x03'):
                    self.tempLine = self.tempLine + d
                else:
                    if len(self.tempLine) == int(self.Length, 16):
                        self.state += 1
                        TmpCheck = ''
                    else:
                        print('error on LineFinder state = 2')
                        self.state = 0
            elif self.state == 3:
                if (d != '\x04'):
                    TmpCheck = TmpCheck + d            
                else:            
                    self.state = 0
                    chk = 0
                    for d in self.tempLine:
                        chk = chk ^ ord(d)
                    if chk == int(TmpCheck, 16):                        
                        # print(self.tempLine)
                        toEmit = str(copy.copy(self.tempLine))
                        self.ReadDone.emit(toEmit)
                        # self.NewLine.emit(str(self.tempLine))
                    else:
                        print('error on LineFinder state = 3')
                        

class Measure(Qt.QThread):
    MeaDone = Qt.pyqtSignal()
    
    def __init__(self):
        super(Measure, self).__init__()
        self.freqs = None
        self.value = None
        self.Data = None
        
    def run(self):
        while True:
            if self.Data is not None:
                print("###################################################")
                print(self.Data)
                print(self.Data.startswith("M"))
                if self.Data.startswith("M"):
                    SplitData = self.Data.split("\t")
                    Chn = self.SelChn(MChn = SplitData[0])
                    self.SaveFreqVal(ChnInd=Chn,
                                     Freq=SplitData[1],
                                     ValMag=SplitData[2],
                                     ValPh=SplitData[3],
                                     ValRe=SplitData[4],
                                     ValImag=SplitData[5])
                    self.MeaDone.emit()
                if self.Data.startswith("NFREQ"):
                    if self.freqs is None:
                        nChannels = self.Data.split("\t")[1]
                        self.freqs = np.ndarray((1, nChannels+1))
                        self.value = np.ndarray((1, nChannels+1))
                else:
                    continue
            else:
                Qt.QThread.msleep(10)
                
    def AddData(self, NewData):
        if self.Data is not None:
            print("Previous Data not Measured")
        self.Data = NewData
    
    def SelChn(self, MChn):
        Chan = MChn.split("M")
        return Chan
    
    def SaveFreqVal(self, ChnInd, Freq, ValMag, ValPh, ValRe, ValImag, MeaMode="polar"):
        self.freqs[ChnInd] = Freq
        if MeaMode == "polar":
            self.complex = np.abs(ValMag)*np.exp(ValPh*1j)
            self.value[ChnInd] = np.abs(self.complex)
            
        if MeaMode == "Bin":
            self.complex = ValRe + (ValImag*1j)
            self.value[ChnInd] = np.abs(self.complex)
         