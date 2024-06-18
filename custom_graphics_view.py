from PyQt5.QtWidgets import QGraphicsView, QGraphicsRectItem, QApplication
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QColor
import numpy as np


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent):
        super().__init__(scene)
        self.parent = parent
        self.setMouseTracking(False)  # Disable mouse tracking by default
        self.boundingBox = None

    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            factor = 1.1
            if event.angleDelta().y() > 0:
                self.scale(factor, factor)
            else:
                self.scale(1 / factor, 1 / factor)
        else:
            super().wheelEvent(event)

    def zoomIn(self):
        factor = 1.1
        self.scale(factor, factor)

    def zoomOut(self):
        factor = 1 / 1.1
        self.scale(factor, factor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            self.parent.nextObject()
        elif event.key() == Qt.Key_A:
            self.parent.previousObject()
        elif event.key() == Qt.Key_I:
            self.parent.markObjectYes()
        elif event.key() == Qt.Key_O:
            self.parent.markObjectNo()
        elif event.key() == Qt.Key_H:
            self.parent.toggleMask()
        elif event.key() == Qt.Key_E:
            self.zoomIn()
        elif event.key() == Qt.Key_Q:
            self.zoomOut()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        point = self.mapToScene(event.pos())
        self.parent.coordinateLabel.setText(f"{int(point.x())}, {int(point.y())}")
        super(CustomGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        point = self.mapToScene(event.pos())
        self.parent.highlightObjectAtPoint(point)
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = self.mapToScene(event.pos())
            x, y = int(point.x()), int(point.y())
            if (
                x >= 0
                and y >= 0
                and x < self.parent.maskArray.shape[1]
                and y < self.parent.maskArray.shape[0]
            ):
                obj = self.parent.maskArray[y, x]
                if obj != 0:
                    self.parent.selectObjectById(obj)
        super().mouseDoubleClickEvent(event)

    def drawBoundingBox(self, obj_id):
        if self.boundingBox:
            self.scene().removeItem(self.boundingBox)
        maskClone = self.parent.maskArray == obj_id
        indices = np.where(maskClone)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        boundingRect = QRectF(minCol, minRow, maxCol - minCol + 1, maxRow - minRow + 1)
        pen = QPen(QColor("red"))
        pen.setWidth(1)
        pen.setJoinStyle(Qt.MiterJoin)
        self.boundingBox = QGraphicsRectItem(boundingRect)
        self.boundingBox.setPen(pen)
        self.scene().addItem(self.boundingBox)
