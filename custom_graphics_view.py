from PyQt5.QtWidgets import (
    QMessageBox, 
    QApplication,
    QGraphicsView, 
    QGraphicsScene, 
    QGraphicsPixmapItem,
    QGraphicsRectItem)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QPen, QColor

import numpy as np

class CustomGraphicsView(QGraphicsView):
    zoomed = pyqtSignal(float)
    moved = pyqtSignal(QPointF)
    pointTracked = pyqtSignal(int, int)
    scrolled = pyqtSignal(int, int)
    
    def __init__(self, mainController, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setInteractive(True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setMouseTracking(False)
        self.maskItem = None
        self.singleMaskItem = None
        self.boundingBox = None
        self.mainController = mainController

    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale(factor, factor)
            self.zoomed.emit(factor)
        # else:
        #     super().wheelEvent(event)
                
    def mousePressEvent(self, event):
        if not self.hasMouseTracking():
            return
        point = self.mapToScene(event.pos())
        self.pointTracked.emit(int(point.x()), int(point.y()))  # Phát signal
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.moved.emit(self.mapToScene(self.viewport().rect().center()))

    def mouseMoveEvent(self, event):
        if not self.hasMouseTracking():
            return
        point = self.mapToScene(event.pos())
        self.mainController.highlightObjectAtPoint(point)
        super().mouseMoveEvent(event)
        
    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self.scrolled.emit(self.horizontalScrollBar().value(), self.verticalScrollBar().value())

    def zoomIn(self):
        self.scale(1.1, 1.1)
        self.moved.emit(self.mapToScene(self.viewport().rect().center()))

    def zoomOut(self):
        self.scale(0.9, 0.9)
        self.moved.emit(self.mapToScene(self.viewport().rect().center()))

    def openImage(self, imagePath):
        try:
            pixmap = QPixmap(imagePath)
            if pixmap.isNull():
                raise ValueError("The image file could not be loaded.")
            self.scene.clear()
            item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(item)
            self.scene.setSceneRect(item.boundingRect())
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to load image: {e}")
            
    def addMask(self, maskPixmap):
        if self.maskItem:
            if self.maskItem.scene() == self.scene:
                self.scene.removeItem(self.maskItem)
                
        if self.singleMaskItem:
            if self.singleMaskItem.scene() == self.scene:
                self.scene.removeItem(self.singleMaskItem)
        
        self.maskItem = QGraphicsPixmapItem(maskPixmap)
        self.maskItem.setOpacity(self.parent().opacityView)
        self.scene.addItem(self.maskItem)
        
        
    def addSingleMaskItem(self, maskPixmap):        
        if self.singleMaskItem:
            if self.singleMaskItem.scene() == self.scene:
                self.scene.removeItem(self.singleMaskItem)
        
        self.singleMaskItem = QGraphicsPixmapItem(maskPixmap)
        self.singleMaskItem.setOpacity(1)
        self.scene.addItem(self.singleMaskItem)
        
    def addBoundingBox(self, boundingRect):
        if self.boundingBox:
            self.scene.removeItem(self.boundingBox)
            
        pen = QPen(QColor("red"))
        pen.setWidth(1)
        pen.setJoinStyle(Qt.MiterJoin)
        self.boundingBox = QGraphicsRectItem(boundingRect)
        self.boundingBox.setPen(pen)
        self.scene.addItem(self.boundingBox)
        
    def keyPressEvent(self, event):
        if event.key() == self.mainController.hotkeys['Next']:
            self.mainController.nextObject()
        elif event.key() == self.mainController.hotkeys['Previous']:
            self.mainController.previousObject()
        elif event.key() == self.mainController.hotkeys['Yes']:
            self.mainController.markObjectYes()
        elif event.key() == self.mainController.hotkeys['No']:
            self.mainController.markObjectNo()
        elif event.key() == self.mainController.hotkeys['Toggle']:
            self.mainController.toggleMask()
        elif event.key() == self.mainController.hotkeys['Zoom In']:
            self.parent().syncZoomIn()
        elif event.key() == self.mainController.hotkeys['Zoom Out']:
            self.parent().syncZoomOut()
        else:
            super().keyPressEvent(event)
            
    def mouseDoubleClickEvent(self, event):
        if not self.hasMouseTracking():
            return
        if event.button() == Qt.LeftButton:
            point = self.mapToScene(event.pos())
            x, y = int(point.x()), int(point.y())
            if (
                x >= 0
                and y >= 0
                and x < self.mainController.maskArray.shape[1]
                and y < self.mainController.maskArray.shape[0]
            ):
                obj = self.mainController.maskArray[y, x]
                if obj != 0:
                    self.mainController.selectObjectById(obj)
        super().mouseDoubleClickEvent(event)