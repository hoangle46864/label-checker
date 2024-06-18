from PyQt5.QtWidgets import QGraphicsView, QApplication
from PyQt5.QtCore import Qt


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent):
        super().__init__(scene)
        self.parent = parent
        self.setMouseTracking(False)  # Disable mouse tracking by default

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

    def mouseMoveEvent(self, event):
        point = self.mapToScene(event.pos())
        self.parent.highlightObjectAtPoint(point)
        super().mouseMoveEvent(event)
