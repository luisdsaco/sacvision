'''
Created on May 15, 2024

@author: luis

Programa: Sacvision. Módulo: backend. Version: 0.1.1

(C) 2017-2022 Luis Díaz Saco

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import numpy as np
import cv2
from PySide6.QtCore import QObject, QThread, Signal

class SacOperation(QObject):
    
    endOperation = Signal(str);
    
    def __init__(self,bck):
        super().__init__()
        self.backend = bck
        self.isRunning = True
    
    def doOperation(self):
        pass

class SacOperationGroup(SacOperation):
    
    def __init__(self,bck,gr):
        super().__init__(bck)
        self.group = gr
        
    def doOperation(self):
        print("En SacOperationGroup")
        im = np.copy(self.backend.in_image)
        for i in self.group:
            i.doOperation()
        self.backend.in_image = np.copy(im)
        self.endOperation.emit("End Operation Group")
        print("Fin de SacOperationGroup")
        
class SacAcquisition(SacOperationGroup):
    
    def initCamera(self):
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            return True
        else:
            print("I cannot open camera")
            self.cap.release()
            return False
    
    def closeCamera(self):
        self.cap.release()
    
    def acquireImage(self):
        ret, im = self.cap.read()
        self.backend.in_image = np.asarray(im)
        return ret
    
    def doOperation(self):
        if self.initCamera():
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.backend.changeSize.emit(width,height)
            while (self.isRunning):
                if self.acquireImage():
                    for i in self.group:
                        i.doOperation()
                    self.backend.refreshScreen.emit()
            self.closeCamera()
    
    
        
class SacFilterNone(SacOperation):
    
    def doOperation(self):
        print("En SacFilterNone")
        self.backend.out_image = np.copy(self.backend.in_image)
        print("Fin de SacFilterNone")

class SacFilterEdges(SacOperation):
    
    def doOperation(self):
        imggray = cv2.cvtColor(self.backend.in_image, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((3, 3), np.uint8)
        imgop = cv2.morphologyEx(imggray, cv2.MORPH_OPEN, kernel)
        imgdx = cv2.Sobel(imgop, cv2.CV_32F, 1, 0, ksize=3)
        imgdy = cv2.Sobel(imgop, cv2.CV_32F, 0, 1, ksize=3)
        imgsob32f = cv2.add(np.square(imgdx), np.square(imgdy))
        imgsob = np.uint8(np.sqrt(imgsob32f))
        ret, imgthr = cv2.threshold(imgsob, 0, 255,
                                    cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        self.backend.out_image = cv2.cvtColor(imgthr, cv2.COLOR_GRAY2BGR)
        
class SacFilterSmooth(SacOperation):
    
    def doOperation(self):
        self.backend.out_image = cv2.blur(self.backend.in_image, (3, 3))
        
class SacFilterFFT(SacOperation):
    
    def doOperation(self):
        imggray = cv2.cvtColor(self.backend.in_image, cv2.COLOR_BGR2GRAY)
        imgfreq = np.fft.fft2(imggray)
        imgfreq = np.fft.fftshift(imgfreq)
        imgabs = np.absolute(imgfreq)
        imglog = np.log(imgabs)
        imgones = np.ones_like(imglog)
        imgres = np.uint8(
                (imglog-imgones*imglog.min())*255/(imglog.max()-imglog.min()))
        self.backend.out_image = cv2.cvtColor(imgres, cv2.COLOR_GRAY2BGR)
        
class SacOutputAsInput(SacOperation):
    
    def doOperation(self):
        self.backend.in_image = np.copy(self.backend.out_image)
        
class SacOperationThread(QThread):
    
    def __init__(self,ops=None):
        super().__init__()
        self.operations = ops
    
    def run(self):
        if self.operations is not None:
            self.operations.doOperation()
    
    def setOperations(self,ops):
        self.operations = ops
        
    def stopOperations(self):
        self.operations.isRunning = False
        
    def startOperations(self):
        self.operations.isRunning = True
        self.start()

class SacBackend(QObject):
    '''
    classdocs
    '''
    changeSize = Signal(int,int)
    refreshScreen = Signal()

    def __init__(self, params=None):
        super().__init__()
        '''
        Constructor
        '''
        self.in_image = np.zeros(512*512*3,np.uint8).reshape(512,512,3)
        self.out_image = self.in_image.copy()
        self.histim = None
        self.camera = False
        self.thread = SacOperationThread()

    
    def getInput(self):
        return self.in_image
    
    def getOutput(self):
        return self.out_image
    
    def setInput(self,im):
        del self.in_image
        self.in_image = np.copy(im)
        
    def setCameraOn(self,flag):
        self.camera = flag
        
    def clsInput(self):
        del self.in_image
        self.in_image = np.zeros(512*512*3,np.uint8).reshape(512,512,3)
        
    def clsOutput(self):
        del self.out_image
        self.out_image = np.zeros(512*512*3,np.uint8).reshape(512,512,3)
        
    def calcHistogram(self,im):
        imggray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        self.histim = cv2.calcHist([imggray], [0], None, [256], [0, 256])
        
    def histogram(self,im):
        self.calcHistogram(im)
        return self.histim
    
    def setFilter(self,ops):
        if self.camera:
            return SacAcquisition(self,ops)
        else:
            return SacOperationGroup(self,ops)
    
    def setOperationCopyImage(self):
        op = SacFilterNone(self)
        ops = self.setFilter([op])
        self.thread.setOperations(ops)
        
    def setOperationEdgeDetection(self):
        op = SacFilterEdges(self)
        ops = self.setFilter([op])
        self.thread.setOperations(ops)
        
    def setOperationSmooth(self):
        op = SacFilterSmooth(self)
        ops = self.setFilter([op])
        self.thread.setOperations(ops)
        
    def setOperationFFT(self):
        op = SacFilterFFT(self)
        ops = self.setFilter([op])
        self.thread.setOperations(ops)
        
    def setOperationComplex(self):
        op1 = SacFilterSmooth(self)
        op2 = SacOutputAsInput(self)
        op3 = SacFilterEdges(self)
        ops = self.setFilter([SacOperationGroup(self,[op1,op2,op3])])
        
        self.thread.setOperations(ops)
        
    def setOperationAcquire(self):
        op = SacFilterNone(self)
        op = SacAcquisition(self,[op])
        self.thread.setOperations(op)
        
    def runOperations(self):
        self.thread.startOperations()
        
    def stopOperations(self):
        self.thread.stopOperations()
        self.thread.wait()
    
    def saveOutputImage(self,name):
        if self.out_image is not None:
            print('Writing image', name)
            cv2.imwrite(name, self.out_image)
            
    def loadInputImage(self,name):
        self.in_image = cv2.imread(name,cv2.IMREAD_COLOR)
        
    