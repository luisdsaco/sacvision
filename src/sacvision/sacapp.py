'''
Created on May 14, 2024

@author: luis

Programa: Sacvision. Módulo: sacapp. Version: 0.1.1

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

import sys

import numpy as np

from sacvision.backend import SacBackend
from cv2 import __version__ as opencvver


from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox,\
    QGraphicsScene, QFileDialog
from sacvision.ui_form import Ui_MainWindow
from PySide6.QtGui import QImage, QPixmap, QActionGroup
from PySide6.QtCore import Slot


class MainWindow(QMainWindow):
    
    def __init__(self,param):
        super().__init__(param)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        

class SacWindow(MainWindow):
    '''
    SacWindow
    '''
    def __init__(self,bck,param=None):
        super().__init__(param)
        
        self.backend = bck
        self.filename = None
        self.result = False
        self.initial = False
        
        self.processGroup = QActionGroup(self)
        self.processGroup.addAction(self.ui.actionCopy)
        self.processGroup.addAction(self.ui.actionSmooth)
        self.processGroup.addAction(self.ui.actionEdge_Detection)
        self.processGroup.addAction(self.ui.actionFFT)
        self.processGroup.addAction(self.ui.actionComplex)
        self.processGroup.setEnabled(False)
        
        self.ui.actionAcquire.setEnabled(True)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionSave_As.setEnabled(False)
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionClose.setEnabled(False)
        
        self.ui.statusbar.showMessage('Sacvision 0.1.1. (c) Luis Díaz Saco')
        
        self.graphicsscene = QGraphicsScene(0, 0, 512, 512)
        self.ui.graphicsView.setScene(self.graphicsscene)
        self.ui.graphicsView.setMinimumSize(512, 512)
        self.ui.graphicsView.setFrameStyle(0)
        
        self.ui.actionNew.triggered.connect(self.onNew)
        self.ui.actionClose.triggered.connect(self.onClose)
        self.ui.actionOpen.triggered.connect(self.onOpen)
        self.ui.actionSave.triggered.connect(self.onSave)
        self.ui.actionSave_As.triggered.connect(self.onSaveAs)
        
        self.ui.actionStart.triggered.connect(self.onStart)
        self.ui.actionStop.triggered.connect(self.onStop)
        
        self.ui.actionCopy.triggered.connect(self.backend.setOperationCopyImage)
        self.ui.actionEdge_Detection.triggered.connect(self.backend.setOperationEdgeDetection)
        self.ui.actionSmooth.triggered.connect(self.backend.setOperationSmooth)
        self.ui.actionFFT.triggered.connect(self.backend.setOperationFFT)
        self.ui.actionComplex.triggered.connect(self.backend.setOperationComplex)
        self.ui.actionAcquire.toggled.connect(self.onAcquire)
        
        self.ui.actionLibraries.triggered.connect(self.onLibraries)
        
        self.ui.actionAboutQt.triggered.connect(lambda:QMessageBox.aboutQt(self,"About Qt"))
        self.ui.actionAbout.triggered.connect(lambda:QMessageBox.about(self,"About Sacvision",
                "(C) 2017-2024 Luis Díaz Saco\nDistributed under AGPL"))
        self.ui.actionLicense.triggered.connect(lambda:QMessageBox.information(self,"Sacvision License",
                "This program is free software: you can redistribute it and/or "
                "modify it under the terms of the GNU Affero General Public "
                "License as published by the Free Software Foundation, either "
                "version 3 of the License, or any later version.\n\n"
                "This program is distributed in the hope that it will be useful,"
                " but WITHOUT ANY WARRANTY; without even the implied warranty of"
                " MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the"
                " GNU Affero General Public License for more details.\n\n"
                "You should have received a copy of the GNU Affero General Public "
                "License along with this program.  If not, see "
                "<https://www.gnu.org/licenses/>.\n\n"
                "Contact the author at saconsultingacs@outlook.com"))
        
        self.backend.thread.finished.connect(lambda:self.showResult("End of Thread"))
        self.backend.refreshScreen.connect(self.updateScreen)
        #self.backend.changeSize.connect(self.sizeChanged)
        
    def onNew(self):
        self.ui.actionNew.setEnabled(False)
        self.ui.actionClose.setEnabled(True)
        self.ui.actionOpen.setEnabled(False)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionSave_As.setEnabled(False)
        
        self.processGroup.setEnabled(True)
        self.ui.actionStart.setEnabled(True)
        if self.processGroup.checkedAction() == None:
                self.ui.actionCopy.trigger()
        
        self.result = False
        image = QImage(':/images/default.jpg').convertToFormat(QImage.Format.Format_BGR888)
        
        self.backend.setInput(self.imageToNp(image))
        self.showImage(self.backend.getInput())
        self.statusBar().showMessage('Default image loaded')
        self.initial = True
        self.result = False
        
    def onAcquire(self):
        if self.ui.actionAcquire.isChecked():
            self.ui.actionNew.setEnabled(False)
            self.ui.actionClose.setEnabled(False)
            self.ui.actionOpen.setEnabled(False)
            self.ui.actionSave.setEnabled(False)
            self.ui.actionSave_As.setEnabled(False)
            self.processGroup.setEnabled(True)
            self.ui.actionStart.setEnabled(True)
            self.backend.setCameraOn(True)
            if self.processGroup.checkedAction() == None:
                self.ui.actionCopy.trigger()
        else:
            if not self.initial:
                self.ui.actionNew.setEnabled(True)
                self.ui.actionClose.setEnabled(False)
                self.ui.actionOpen.setEnabled(True)
                self.processGroup.setEnabled(False)
                self.ui.actionStart.setEnabled(False)
            else:
                self.ui.actionClose.setEnabled(True)
            if self.result:
                self.ui.actionSave.setEnabled(True)
                self.ui.actionSave_As.setEnabled(True)
                
            self.backend.setCameraOn(False)
        
    def onClose(self):
        self.ui.actionNew.setEnabled(True)
        self.ui.actionClose.setEnabled(False)
        self.ui.actionOpen.setEnabled(True)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionSave_As.setEnabled(False)
        self.ui.actionStart.setEnabled(False)
        self.processGroup.setEnabled(False)
        
        self.backend.clsInput()
        self.filename = None
        self.showImage(self.backend.getInput())
        self.initial = False
        self.result = False
        
    def onOpen(self):       
        self.filename, ftype = QFileDialog.getOpenFileName(
            self, 'Open file', '.', "Image files (*.jpg *.gif)")
        if len(self.filename)>0:
            image = QImage(self.filename).convertToFormat(QImage.Format.Format_BGR888)
        
            self.backend.setInput(self.imageToNp(image))
            self.showImage(self.backend.getInput())
            self.statusBar().showMessage('Image loaded')
            self.ui.actionNew.setEnabled(False)
            self.ui.actionClose.setEnabled(True)
            self.ui.actionOpen.setEnabled(False)
            self.ui.actionSave.setEnabled(False)
            self.ui.actionSave_As.setEnabled(False)
            self.processGroup.setEnabled(True)
            self.ui.actionStart.setEnabled(True)
            if self.processGroup.checkedAction() == None:
                self.ui.actionCopy.trigger()
            self.result = False
            self.initial = True
        
    def onSave(self):
        self.ui.actionSave.setEnabled(False)
        if self.filename is not None:
            self.backend.saveOutputImage(self.filename)
            self.result = False
        else:
            self.onSaveAs()
    
    def onSaveAs(self):
        self.filename, ftype = QFileDialog.getSaveFileName(
            self, 'Open file', '.', "Image files (*.jpg *.gif)")
        if len(self.filename)>0:
            self.backend.saveOutputImage(self.filename)
            self.ui.actionSave.setEnabled(False)
            self.result = False
            
    def onLibraries(self):
        mplstr = 'Matplotlib version ' + '3.6.3' + '\n\n'
        ocvstr = 'Opencv version ' + opencvver + '\n\n'
        npstr = 'Numpy version ' + np.__version__
        QMessageBox.information(self, "Using libraries",
                                          mplstr + ocvstr + npstr)
    
    def onStart(self):
        self.ui.actionStart.setEnabled(False)
        self.backend.runOperations()
        self.ui.actionStop.setEnabled(True)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionSave_As.setEnabled(False)
        self.processGroup.setEnabled(False)
        self.initial = True

    def onStop(self):
        self.ui.actionStop.setEnabled(False)
        self.backend.stopOperations()
        
        self.ui.actionStart.setEnabled(True)
        self.ui.actionSave.setEnabled(True)
        self.ui.actionSave_As.setEnabled(True)
        self.ui.actionClose.setEnabled(True)
        
        
    def npToImage(self,im):
        image = QImage(im.tobytes(), np.shape(im)[1], np.shape(im)[0],                                                                                                                                                 
                     QImage.Format.Format_BGR888)
        return image
    
    def imageToNp(self,image):
        return np.frombuffer(image.bits(),np.uint8).reshape(image.width(),image.height(),image.depth()//8)
    
    def showImage(self,im):
        image = self.npToImage(im)
        pixmap = QPixmap(image)
        
        sc = self.graphicsscene
        sc.clear()
        sc.addPixmap(pixmap)
        sc.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        sc.update(sc.sceneRect())
        self.ui.graphicsView.setMinimumSize(pixmap.width(),pixmap.height())
        self.ui.widget.putdata(self.backend.histogram(im))
        self.ui.widget.plot()
        self.adjustSize()
        
    @Slot(str)
    def showResult(self,res):
        print("Inicio de showResult")
        self.showImage(self.backend.getOutput())
        self.statusBar().showMessage(res)
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionSave.setEnabled(True)
        self.ui.actionSave_As.setEnabled(True)
        self.processGroup.setEnabled(True)
        print("Fin de showResult")
        self.result = True
        
    @Slot()
    def updateScreen(self):
        self.showImage(self.backend.getOutput())
        
    @Slot(int,int)
    def sizeChanged(self,x,y):
        sc = self.graphicsscene
        sc.setSceneRect(0, 0, x, y)
        sc.update(sc.sceneRect())
        self.ui.graphicsView.setMinimumSize(x,y)
        self.adjustSize()
        
    
        
class SacApp(QApplication):
    '''
    classdocs
    '''

    def __init__(self,params):
        '''
        Constructor
        '''
        super().__init__(params)
        
def main():
    app = SacApp(sys.argv)
    bck = SacBackend()
    win = SacWindow(bck)
    win.show()

    ret = app.exec()
    return ret
    
if __name__ == '__main__':
    print('Sacvision 0.1.1: (c) 2017-2024 Luis Díaz Saco')
    sys.exit(main())
        