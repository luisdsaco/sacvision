# -*- coding: utf-8 -*-
"""
Editor de Spyder

Programa: Sacvision. Módulo: main. Version: 0.0.1

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
"""

import cv2
import numpy as np

from matplotlib import pyplot as plt
from matplotlib import __version__ as mplver
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvas

import sys
from threading import Thread

from matplotlib.backends.qt_compat import QtCore, QtWidgets, QtGui


class SacWindow(QtWidgets.QMainWindow):
    """
    Main Qt Window for Sacvision
    """

    def __init__(self, parent=None):
        super(SacWindow, self).__init__(parent)
        self.resize(512, 512)
        self.move(300, 300)
        self.setWindowTitle('Sacvision 0.0.1')
        self.setWindowIcon(QtGui.QIcon('logo_saconsulting.png'))
        self.statusBar().showMessage('Sacvision 0.0.1. (c) Luis Díaz Saco')
        self.header = QtWidgets.QLabel()
        self.header.setAlignment(QtCore.Qt.AlignCenter)
        self.header.setPixmap(QtGui.QPixmap('logo_saconsulting.png'))
        self.pixmapit = None
        self.graphicsscene = QtWidgets.QGraphicsScene(0, 0, 512, 512)
        self.graphicsview = QtWidgets.QGraphicsView(self.graphicsscene)
        self.graphicsview.setMinimumSize(512, 512)
        self.graphicsview.setFrameStyle(0)
        self.pixmap = None

        self.histo = SacHistoWidget(Figure(figsize=(5, 3), dpi=70))
        self.histo.setMinimumSize(256, 100)
        mainlayout = QtWidgets.QGridLayout()

        layout = [self.header, self.histo]

        for i in range(len(layout)):
            mainlayout.addWidget(layout[i], 0, i)
        mainlayout.addWidget(self.graphicsview, 1, 0, 1, 2)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        self.mainproc = SacProcess()
        self.acqthread = None

        filemenu = {"New": self.getnew,
                    "Open": self.openfile,
                    "Save": self.savefile,
                    "Quit": self.close
                    }

        acqmenu = {"Start": self.startAcquisition,
                   "Stop": self.stopAcquisition
                   }

        viewmenu = {"Input": self.showinput,
                    "Output": self.showoutput
                    }

        opsmenu = {"None": self.filternone,
                   "Edges": self.filteredges,
                   "Smooth": self.filtersmooth,
                   "Freq": self.filterfreq
                   }

        hlpmenu = {"About": self.aboutmessage,
                   "Qt Version": self.qtversion,
                   "Other libraries": self.libraries,
                   "License": self.saclicense
                   }

        menu = self.menuBar()
        file = menu.addMenu("File")
        acq = menu.addMenu("Acquisition")
        view = menu.addMenu("View")
        ops = menu.addMenu("Operations")
        hlp = menu.addMenu("Help")

        self.vwgroup = QtWidgets.QActionGroup(self)
        self.opsgroup = QtWidgets.QActionGroup(self)

        self.actions = {}

        for entry, function in filemenu.items():
            f = QtWidgets.QAction(entry, self)
            file.addAction(f)
            f.setStatusTip("File actions")
            f.triggered.connect(function)
            self.actions[entry] = f

        for entry, function in acqmenu.items():
            f = QtWidgets.QAction(entry, self)
            acq.addAction(f)
            f.setStatusTip("Acquisition actions")
            f.triggered.connect(function)
            self.actions[entry] = f

        for entry, function in viewmenu.items():
            f = QtWidgets.QAction(entry, self)
            self.vwgroup.addAction(f)
            f.setCheckable(True)
            view.addAction(f)
            f.setStatusTip("View images")
            f.triggered.connect(function)
            self.actions[entry] = f
        self.vwgroup.setExclusive(True)

        for entry, function in opsmenu.items():
            f = QtWidgets.QAction(entry, self)
            self.opsgroup.addAction(f)
            f.setCheckable(True)
            ops.addAction(f)
            f.setStatusTip("Operations")
            f.triggered.connect(function)
            self.actions[entry] = f
        self.opsgroup.setExclusive(True)

        for entry, function in hlpmenu.items():
            f = QtWidgets.QAction(entry, self)
            hlp.addAction(f)
            f.setStatusTip("Help actions")
            f.triggered.connect(function)
            self.actions[entry] = f

        self.actions['Input'].setChecked(True)
        self.actions['None'].setChecked(True)

        self.actions['Stop'].setEnabled(False)
        self.actions['Save'].setEnabled(False)
        self.vwgroup.setEnabled(False)

        self.centralwidget.setLayout(mainlayout)
        self.adjustSize()

    def processingmenu(self):
        self.close()
        
    def showimage(self):
        if self.pixmapit is not None:
            self.graphicsscene.removeItem(self.pixmapit)
        self.pixmapit = self.graphicsscene.addPixmap(self.pixmap)
        sc = self.graphicsscene
        sc.setSceneRect(0, 0, self.pixmap.width(),
                        self.pixmap.height())
        self.graphicsview.setFixedSize(self.pixmap.width(),
                                              self.pixmap.height())
        sc.update(sc.sceneRect())
        self.adjustSize()

    def showhistogram(self):
        if self.mainproc.histim is None:
            self.mainproc.gethist(self.inp)
        self.histo.putdata(self.mainproc.histim)
        self.histo.plot()
    
    def getnew(self):
        self.mainproc.getnew()
        self.showinput()
        self.actions['Save'].setEnabled(False)
        self.vwgroup.setEnabled(True)

    def openfile(self):
        fname, ftype = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open file', '.', "Image files (*.jpg *.gif)")
        if len(fname) > 0:
            self.mainproc.setparam(fname)
            self.mainproc.getinput()
            self.showinput()
            self.actions['Save'].setEnabled(False)
            self.vwgroup.setEnabled(True)
            if self.mainproc.filter == 'None':
                self.actions['Output'].setEnabled(False)
            else:
                self.actions['Output'].setEnabled(True)
            self.update()

    def savefile(self):
        fname, ftype = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save file', '.', "Image files (*.jpg *.gif)")
        if len(fname) > 0:
            self.mainproc.saveoutput(fname)

    def startAcquisition(self):
        self.actions['Start'].setEnabled(False)
        self.actions['Stop'].setEnabled(True)
        self.vwgroup.setEnabled(False)
        self.opsgroup.setEnabled(False)
        self.statusBar().showMessage('Acquiring image from camera')
        
        if self.mainproc.filter is None:
            self.mainproc.filter = 'None'
        self.acqthread = SacFilterAcquisition(self)
        self.acqthread.start()

    def stopAcquisition(self):
        if self.acqthread is not None and self.acqthread.is_alive():
            self.mainproc.inp = self.acqthread.stopAcquisition()
        self.showinput()
        self.actions['Stop'].setEnabled(False)
        self.actions['Start'].setEnabled(True)
        self.vwgroup.setEnabled(True)
        if self.mainproc.filter == 'None':
            self.actions['Output'].setEnabled(False)
        else:
            self.actions['Output'].setEnabled(True)
        self.opsgroup.setEnabled(True)
        self.statusBar().showMessage('End of acquisition')

    def showinput(self):
        self.pixmap = self.mainproc.showinput()
        self.mainproc.gethist(self.mainproc.inp)
        self.showhistogram()
        self.showimage()
        self.update()
        self.actions['Input'].setChecked(True)
        self.statusBar().showMessage('Input Image')

    def showoutput(self):
        self.pixmap = self.mainproc.showoutput()
        self.mainproc.gethist(self.mainproc.outp)
        self.showhistogram()
        self.showimage()
        if self.mainproc.outp is not None:
            self.update()
            self.actions['Output'].setChecked(True)
            self.actions['Save'].setEnabled(True)
            self.statusBar().showMessage('Output Image')

    def filternone(self):
        self.mainproc.filternone()
        if self.mainproc.inp is not None:
            self.showinput()
            self.actions['Output'].setEnabled(False)
            self.actions['Save'].setEnabled(False)
            self.actions['Input'].setChecked(True)
            self.statusBar().showMessage('Input Image')

    def filteredges(self):
        self.mainproc.filteredges()
        if self.mainproc.inp is not None:
            self.showoutput()
            self.actions['Output'].setEnabled(True)
            self.actions['Output'].setChecked(True)
            self.statusBar().showMessage('Output Image')

    def filtersmooth(self):
        self.mainproc.filtersmooth()
        if self.mainproc.inp is not None:
            self.showoutput()
            self.actions['Output'].setEnabled(True)
            self.actions['Output'].setChecked(True)
            self.statusBar().showMessage('Output Image')

    def filterfreq(self):
        self.mainproc.filterfreq()
        if self.mainproc.inp is not None:
            self.showoutput()
            self.actions['Output'].setEnabled(True)
            self.actions['Output'].setChecked(True)
            self.statusBar().showMessage('Output Image')

    def aboutmessage(self):
        QtWidgets.QMessageBox.about(self, "About", "Sacvision 0.0.1\n\n"
                                    "(c) 2017-2022 Luis Díaz Saco\n\n"
                                    "Distributed under GNU AGPLv3 License")

    def qtversion(self):
        QtWidgets.QMessageBox.aboutQt(self, "Qt Version")

    def libraries(self):
        mplstr = 'Matplotlib version ' + mplver + '\n\n'
        ocvstr = 'Opencv version ' + cv2.__version__ + '\n\n'
        npstr = 'Numpy version ' + np.__version__
        QtWidgets.QMessageBox.information(self, "Using libraries",
                                          mplstr + ocvstr + npstr)

    def saclicense(self):
        QtWidgets.QMessageBox.information(self, "License",
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
            "Contact the author at saconsultingacs@outlook.com")

    def closeEvent(self, event):
        self.mainproc.close()

    def paintEvent(self, event):
        if self.pixmap is not None:
            self.showimage()
        super(SacWindow, self).paintEvent(event)


class SacThreadOperation(Thread):
    """
    Base class for different operations with images
    """

    def __init__(self, window=None):
        Thread.__init__(self)
        self.image = None
        self.isRunning = False
        self.window = window

    def mainloop(self):
        if self.initcamera():
            self.initscreen()
            self.isRunning = True
            while (self.isRunning):
                if self.acquireimage():
                    self.mainoperation()
            self.closecamera()
            self.closescreen()

    def initcamera(self):
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            return True
        else:
            print("I cannot open camera")
            self.cap.release()
            return False

    def initscreen(self):
        pass

    def acquireimage(self):
        ret, self.image = self.cap.read()
        return ret

    def closecamera(self):
        self.cap.release()

    def closescreen(self):
        pass

    def mainoperation(self):
        pass

    def stopAcquisition(self):
        self.isRunning = False
        return self.image

    def run(self):
        self.mainloop()


class SacAcquisitioncv(SacThreadOperation):
    """
    Initial class to acquire images using the OpenCV interface.
    It is not used with the Qt interface
    """

    def __init(self, window=None):
        SacThreadOperation.__init__(self, window)
        self.windowName = 'Saconsulting Acquisition'

    def closescreen(self):
        cv2.destroyWindow(self.windowName)

    def mainoperation(self):
        cv2.imshow(self.windowName, self.image)


class SacAcquisition(SacThreadOperation):
    """
    Acquire images through the Qt interface.
    Show the source image from the camera.
    """

    def __init__(self, window=None):
        SacThreadOperation.__init__(self, window)

    def initscreen(self):
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.window.graphicsscene.setSceneRect(0, 0, width, height)
        self.window.graphicsview.setFixedSize(width, height)
        self.window.update()
        self.window.adjustSize()

    def mainoperation(self):
        if self.window is not None:
            self.window.pixmap = self.window.mainproc.createfromBGRimage(self.image)
            self.window.mainproc.gethist(self.image)
            self.window.showhistogram()
            self.window.update()


class SacEdgesAcquisition(SacAcquisition):
    """
    Acquire images through the Qt interface.
    Shows an edge detection operator of the source image from the camera
    """

    def mainoperation(self):
        if self.window is not None:
            im = self.window.mainproc.doprocessedges(self.image)
            self.window.pixmap = self.window.mainproc.createfromBGRimage(im)
            self.window.mainproc.gethist(im)
            self.window.showhistogram()
            self.window.update()


class SacSmoothAcquisition(SacAcquisition):
    """
    Acquire images through the Qt interface.
    Shows the smoothed image of the source image from the camera
    """

    def mainoperation(self):
        if self.window is not None:
            im = self.window.mainproc.doprocesssmooth(self.image)
            self.window.pixmap = self.window.mainproc.createfromBGRimage(im)
            self.window.mainproc.gethist(im)
            self.window.showhistogram()
            self.window.update()

class SacFreqAcquisition(SacAcquisition):
    """
    Acquire images through the Qt interface.
    Shows the smoothed image of the source image from the camera
    """

    def mainoperation(self):
        if self.window is not None:
            im = self.window.mainproc.doprocessfrequency(self.image)
            self.window.pixmap = self.window.mainproc.createfromBGRimage(im)
            self.window.mainproc.gethist(im)
            self.window.showhistogram()
            self.window.update()
            
class SacFilterAcquisition(SacAcquisition):
    """
    Acquire image through the Qt interface.
    Shows a filtered image of the source image from the camera
    """
    
    def mainoperation(self):
        if self.window is not None:
            im = self.window.mainproc.applyfilter(self.image)
            self.window.pixmap = self.window.mainproc.createfromBGRimage(im)
            self.window.mainproc.gethist(im)
            self.window.showhistogram()
            self.window.update()


class SacHistoWidget(FigureCanvas):
    """
    Draw an histogram from a set of data
    """

    def __init__(self, fig):
        super().__init__(fig)
        self.data = np.zeros(256)
        self.ax = self.figure.subplots()
        self.ax.plot(self.data)

    def putdata(self, data):
        self.data = data

    def plot(self):
        if self.data is not None:
            self.ax.clear()
            self.ax.plot(self.data)
            self.figure.canvas.draw()


class SacProcess():
    """
    Define methods for image processing with OpenCV
    """

    def __init__(self, param=None):
        self.inp = None
        self.outp = None
        self.histim = None
        self.filter = 'None'
        if param is None:
            self.param = 'lena.jpg'
        else:
            self.param = param

    def main(self):
        self.filteredges()

    def filternone(self):
        self.filter = 'None'
        if self.inp is not None:
            self.showinput()

    def filteredges(self):
        self.filter = 'Edges'
        if self.inp is not None:
            self.showoutput()

    def filtersmooth(self):
        self.filter = 'Smooth'
        if self.inp is not None:
            self.showoutput()

    def filterfreq(self):
        self.filter = 'Freq'
        if self.inp is not None:
            self.showoutput()

    def setparam(self, param=None):
        self.param = param

    def getnew(self):
        self.inp = cv2.imread('lena.jpg', cv2.IMREAD_COLOR)
        print('New input image set to the default image')

    def getinput(self):
        self.inp = cv2.imread(self.param, cv2.IMREAD_COLOR)
        print('Reading image', self.param)

    def saveoutput(self, name):
        if self.outp is not None:
            print('Writing image', name)
            cv2.imwrite(name, self.outp)

    def gethist(self, im):
        imggray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        self.histim = cv2.calcHist([imggray], [0], None, [256], [0, 256])

    def doprocessnone(self, img):
        return img

    def doprocessedges(self, img):
        imggray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((3, 3), np.uint8)
        imgop = cv2.morphologyEx(imggray, cv2.MORPH_OPEN, kernel)
        imgdx = cv2.Sobel(imgop, cv2.CV_32F, 1, 0, ksize=3)
        imgdy = cv2.Sobel(imgop, cv2.CV_32F, 0, 1, ksize=3)
        imgsob32f = cv2.add(np.square(imgdx), np.square(imgdy))
        imgsob = np.uint8(np.sqrt(imgsob32f))
        ret, imgthr = cv2.threshold(imgsob, 0, 255,
                                    cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        return cv2.cvtColor(imgthr, cv2.COLOR_GRAY2BGR)

    def doprocesssmooth(self, img):
        return cv2.blur(img, (3, 3))

    def doprocessfrequency(self, img):
        imggray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imgfreq = np.fft.fft2(imggray)
        imgfreq = np.fft.fftshift(imgfreq)
        imgabs = np.absolute(imgfreq)
        imglog = np.log(imgabs)
        imgones = np.ones_like(imglog)
        imgres = np.uint8(
                (imglog-imgones*imglog.min())*255/(imglog.max()-imglog.min()))
        return cv2.cvtColor(imgres, cv2.COLOR_GRAY2BGR)

    def applyfilter(self, img=None):
        filterdict = {'None': self.doprocessnone,
                      'Edges': self.doprocessedges,
                      'Smooth': self.doprocesssmooth,
                      'Freq': self.doprocessfrequency
                      }
        if self.filter is None:
            self.filter = 'None'
        if img is None:
            return filterdict[self.filter](self.inp)
        else:
            return filterdict[self.filter](img)

    def showoutput(self):
        self.outp = self.applyfilter()
        pixmap = None
        
        if self.outp is not None:
            pixmap = self.createfromBGRimage(self.outp)
            self.gethist(self.outp)
        return pixmap
    
    def showinput(self):
        if self.inp is None:
            self.getinput()
        pixmap = self.createfromBGRimage(self.inp)
        self.gethist(self.inp)
        return pixmap

    def createfromBGRimage(self, image):
        imrgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        qim = QtGui.QImage(imrgb.data, imrgb.shape[1], imrgb.shape[0],
                           QtGui.QImage.Format_RGB888)
        return QtGui.QPixmap(qim)

    def createfromgrayimage(self, image):
        imrgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        qim = QtGui.QImage(imrgb.data, imrgb.shape[1], imrgb.shape[0],
                           QtGui.QImage.Format_RGB888)
        return QtGui.QPixmap(qim)

    def close(self):
        plt.close('all')


class SacApp(QtWidgets.QApplication):
    """
    Main Qt application
    """

    def __init__(self, param):
        super(SacApp, self).__init__(param)


if __name__ == '__main__':
    print('Sacvision 0.0.1: (c) 2017-2022 Luis Díaz Saco')
    app = SacApp(sys.argv)
    win = SacWindow()
    win.show()

    ret = app.exec_()
    sys.exit(ret)
