'''
Created on May 15, 2024

@author: luis
'''


import numpy as np

from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class SacHistoWidget(QWidget):
    '''
    classdocs
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self.plotLayout = QVBoxLayout()
        self.setLayout(self.plotLayout)
        self.view = FigureCanvasQTAgg(Figure(figsize=(4,3)))
        self.view.figure.suptitle("Histogram")
        self.data = np.zeros(256)
        self.ax = self.view.figure.subplots()
        self.ax.plot(self.data)
        self.view.draw()
        self.plotLayout.addWidget(self.view)

    def putdata(self, data):
        self.data = data

    def plot(self):
        if self.data is not None:
            self.ax.clear()
            self.ax.plot(self.data)
            self.view.draw()
            
