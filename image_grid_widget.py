from PyQt5.QtWidgets import QWidget, QGraphicsScene, QGridLayout, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPixmap, QPen, QColor
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
from tifffile import imread, imwrite
import numpy as np
from custom_graphics_view import CustomGraphicsView

class ImageGridWidget(QWidget):
    pointTracked = pyqtSignal(int, int)
    
    def __init__(self, mainController, parent=None):
        super().__init__(parent)
        self.mainController = mainController
        self.initUI()

    def initUI(self):
        self.layout = QGridLayout(self)
        self.scene = QGraphicsScene(self)
        self.views = []
        self.coordinateView = []
        self.opacityView = 0.5
        self.maskVisible = False
        
        self.checked = [0, 0, 0, 0]

        for i in range(2):
            row = []
            for j in range(2):
                view = CustomGraphicsView(self.mainController, self) 
                self.layout.addWidget(view, i, j)
                row.append(view)
                view.zoomed.connect(self.syncZoom)
                view.moved.connect(self.syncMove)
                view.pointTracked.connect(self.handlePointTracked)
                view.scrolled.connect(self.syncScroll) 
                self.coordinateView.append([i, j])
            self.views.append(row)

    def handlePointTracked(self, x, y):
        self.pointTracked.emit(x, y)          

    def syncZoom(self, factor):
        sender = self.sender()
        for row in self.views:
            for view in row:
                if view != sender:
                    view.scale(factor, factor)
                    
    def syncZoomIn(self):
        sender = self.sender()
        for row in self.views:
            for view in row:
                if view != sender:
                    view.zoomIn()

    def syncZoomOut(self):
        sender = self.sender()
        for row in self.views:
            for view in row:
                if view != sender:
                    view.zoomOut()

    def syncMove(self, centerPoint):
        sender = self.sender()
        for row in self.views:
            for view in row:
                if view != sender:
                    view.centerOn(centerPoint)
                    
    def syncScroll(self, horiz, vert):
        if QApplication.keyboardModifiers() != Qt.ControlModifier:
            sender = self.sender()
            for row in self.views:
                for view in row:
                    if view != sender:
                        view.horizontalScrollBar().setValue(horiz)
                        view.verticalScrollBar().setValue(vert)
            
    def openImageAtPath(self, path, num, allPath):
        row, col = self.coordinateView[num]
        self.views[row][col].openImage(path)
        self.checked[num] = 1
        if(sum(self.checked) == 3):
            self.openImageRGB(allPath)
            
    def openImageRGB(self, allPath):        
        r = imread(allPath[2])
        g = imread(allPath[3])
        b = imread(allPath[1])
        RGB = np.dstack((r,g,b))
        imwrite(f'rgb.tiff', RGB)
        
        row, col = self.coordinateView[0]
        self.views[row][col].openImage('rgb.tiff')
                    
    def changeMask(self, maskPath, maskClone = None):
        self.addMask(maskPath)
        if maskClone is not None:
            self.addBoundingBox(maskClone)
    
    def addMask(self, maskPath):                                    
        maskPixmap = QPixmap(maskPath)
        sender = self.sender() 
        
        for row in self.views:
            for view in row:
                if view != sender:
                    view.addMask(maskPixmap)
        
        self.maskVisible = True
                    
    def addHighlight(self, maskHighlightPath):                                    
        maskPixmap = QPixmap(maskHighlightPath)
        sender = self.sender() 

        for row in self.views:
            for view in row:
                if view != sender:
                    view.addSingleMaskItem(maskPixmap)
    
    def addBoundingBox(self, maskClone):
        indices = np.where(maskClone)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        boundingRect = QRectF(minCol, minRow, maxCol - minCol + 1, maxRow - minRow + 1)
        
        sender = self.sender() 
        for row in self.views:
            for view in row:
                if view != sender:
                    view.addBoundingBox(boundingRect)
    
    def scaleToObject(self, boundingRect):
        sender = self.sender()
        for row in self.views:
            for view in row:
                if view != sender:
                    view.fitInView(boundingRect, Qt.KeepAspectRatio)
                    view.scale(1/8, 1/8)

    def toggleMask(self):
        sender = self.sender()
        for row in self.views:
            for view in row:
                if view != sender:
                    if self.maskVisible:
                        view.maskItem.hide()
                    else:
                        view.maskItem.show()
                    
        self.maskVisible = not self.maskVisible
                    
    def changeTransparency(self, opacity):
        sender = self.sender()
        self.opacityView = opacity
        for row in self.views:
            for view in row:
                if view != sender:
                    if view.maskItem:
                        view.maskItem.setOpacity(self.opacityView)
                    if view.singleMaskItem:
                        view.singleMaskItem.setOpacity(self.opacityView)
                    
    def toggleMouseTracking(self):
        sender = self.sender()
        for row in self.views:
            for view in row:
                if view != sender:
                    view.setMouseTracking(True)