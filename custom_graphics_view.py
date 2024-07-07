from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QColor
from pyqtgraph import ImageView
import numpy as np


class CustomGraphicsView(ImageView):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setMouseTracking(False)  # Disable mouse tracking by default
        self.boundingBox = None
        self.scene.sigMouseMoved.connect(self.mouseMoveEvent)

    def mouseMoveEvent(self, pos):
        if not self.hasMouseTracking():
            return
        # print("Mouse Move Event Triggered")
        point = self.getView().mapSceneToView(pos)
        # print(f"Mouse Point: {point}")
        self.parent.highlightObjectAtPoint(point)

    def mousePressEvent(self, event):
        if not self.hasMouseTracking():
            return
        print("Mouse Press Event Triggered")
        point = self.getView().mapSceneToView(event.pos())
        # print(f"Mouse Press Point: {point}")
        self.parent.coordinateLabel.setText(f"{int(point.x())}, {int(point.y())}")
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if not self.hasMouseTracking():
            return
        if event.button() == Qt.LeftButton:
            point = self.getView().mapSceneToView(event.pos())
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
            self.view.removeItem(self.boundingBox)

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
        self.view.addItem(self.boundingBox)
