import cv2 as cv
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import json
import serial
from serial.tools import list_ports
from calib.calib import calib

class read_serial(QThread):
    Isignal = pyqtSignal(bytes)
    def __init__(self):
        super().__init__()
    def setPort(self,Iport):
        self.Iport = Iport

    def run(self):
        self.condition = True
        while(self.condition):
            mess = self.Iport.read(2)
            if len(mess)>0:
                self.Isignal.emit(mess)
    
    def Istop(self):
        self.condition = False

class mainwindow(QMainWindow):
    def __init__(self,*args,**kwargs):
        super().__init__()
        uic.loadUi("gui.ui",self)
        with open("data.json","r") as file:
            data = json.load(file)
        #define
        self.source = {"board mach uno":"./sample/uno.jpg",
                "board mach mega":"./sample/mega.jpg"}
        self.Iport = serial.Serial()
        self.Iread = read_serial()
        self.preproc()
        self.condiShow = True
        self.cap = cv.VideoCapture()
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
        self.disconnectBtn.setEnabled(False)
        self.solidSlider.setValue(data["solidValue"])
        self.ratioSlider.setValue(data["ratioValue"])
        self.notiedLabel.setAlignment(Qt.AlignCenter)
        self.notiedLabel.setText("FALSE")
        self.notiedLabel.setFont(QFont("Arial",30,QFont.Bold))
        self.notiedLabel.setStyleSheet("background-color:red; border:2px solid black")
        
        #signal
        self.exitBtn.clicked.connect(self.exit)  
        self.startBtn.clicked.connect(self.clickedStart)
        self.stopBtn.clicked.connect(self.clickedStop)
        self.connectBtn.clicked.connect(self.clickedConnect)
        self.sampleBtn.clicked.connect(self.setSample)
        self.disconnectBtn.clicked.connect(self.clickedDis)
        self.Iread.Isignal.connect(self.readPort)
        self.solidSlider.valueChanged.connect(self.changeSolid)
        self.ratioSlider.valueChanged.connect(self.changeRatio)
        self.areaSlider.valueChanged.connect(self.changeArea)
        self.calibBtn.clicked.connect(self.calib)
    #function
    def mapValue(self,value,op):
        proValue = None
        if op == 0:
            v_max = 600
            v_min = 0
            step = 30
            proValue = value/1000
        if op == 1:
            v_max = 200
            v_min = 0
            step = 10
            proValue = value/1000
        return proValue

    def preproc(self):
        self.disCam()
        self.getPort()
        for i in self.source:
            self.boardList.addItem(i)
        self.setSample()
    
    def getPort(self):
        self.listedPort = list_ports.comports()
        for i in self.listedPort:
            self.portList.addItem(i.name)

    def disCam(self):
        self.discamImg = cv.imread("./img/discam.jpg")
        self.discamImg = self.convertFrame(self.discamImg)
        self.display.setPixmap(self.discamImg)

    def setSample(self):
        img = cv.imread(self.source[self.boardList.currentText()])
        qimg = self.convertFrame(img)
        self.sample.setPixmap(qimg)
            
    def show_cam(self):
        while(self.condiShow):
            _,frame = self.cap.read()
            if not _:
                break
            Qframe = self.convertFrame(frame)
            self.display.setPixmap(Qframe)
            cv.waitKey(10)
    #slot
    def calib(self):
        self.calib = calib(self)
        self.calib.exec_()

    def readPort(self,mess):
        self.message.append(mess.decode())

    def changeSolid(self):
        self.SolidValue = self.mapValue(self.solidSlider.value(),0)
        self.message.append("Solid value: "+str(self.SolidValue))
    def changeRatio(self):
        self.RatioValue = self.mapValue(self.ratioSlider.value(),1)
        self.message.append("Ratio Scaler value: "+str(self.RatioValue))
    def changeArea(self):
        self.AreaValue = self.areaSlider.value()
        self.message.append("Ratio Scaler value: "+str(self.AreaValue))

    def clickedConnect(self):
        self.Iport.port = self.portList.currentText()
        self.Iport.baudrate = 9600
        self.Iport.open()
        if self.Iport.isOpen():
            self.Iread.setPort(self.Iport)
            self.Iread.start()
            self.startBtn.setEnabled(True)
            self.connectBtn.setEnabled(False)
            self.disconnectBtn.setEnabled(True)
            self.message.append("Da ket noi den "+ self.portList.currentText()+"\n")
            self.portList.setEnabled(False)
            
        else:
            self.message.append("khong the ket noi den "+ self.portList.currentText())

    def clickedDis(self):
        self.Iread.Istop()
        self.Iport.close()
        if not self.Iport.isOpen():
            self.startBtn.setEnabled(False)
            self.connectBtn.setEnabled(True)
            self.disconnectBtn.setEnabled(False)
            self.portList.setEnabled(True)
            self.message.append("Da ngat ket noi "+ self.portList.currentText()+"\n")
        else:
            self.message.append("khong the ngat ket noi "+ self.portList.currentText())

    def clickedStart(self):
        self.Iport.write("open".encode())
        self.sampleBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self.startBtn.setEnabled(False)
        self.condiShow = True
        self.cap.open(0)
        self.show_cam()

    def clickedStop(self):
        self.startBtn.setEnabled(True)
        self.sampleBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        
        self.disCam()
        self.cap.release()

    def exit(self):
        self.exitBtn.clicked.connect(self.exit)
        data = {"solidValue":self.solidSlider.value(),"ratioValue":self.ratioSlider.value(),"areaValue":self.areaSlider.value()}
        with open("data.json","w") as file:
            json.dump(data,file)
            print("saved")
        self.clickedStop()
        self.close()  

    #subfuntion
    @staticmethod
    def convertFrame(img):
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        h,w,ch = img.shape
        Qimg = QImage(img.data,w,h,w*ch,QImage.Format_RGB888)
        Qimg = Qimg.scaled(w,h, Qt.KeepAspectRatio)
        return QPixmap.fromImage(Qimg)

if __name__ == "__main__":
    app = QApplication([])
    w = mainwindow()
    w.show()
    app.exec_()