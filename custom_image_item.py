from PyQt5.QtCore import QRectF
# from PyQt5.QtGui import QPen, QColor
from pyqtgraph import ImageItem
import numpy as np


class CustomImageItem(ImageItem):
    def __init__(self, parent, image=None, mask=None, *args, **kwargs):
        super().__init__(image=image, *args, **kwargs)
        self.setAcceptHoverEvents(True)
        self.highlighted = False
        self.parent = parent
        self.mask = mask
        self.bounding_rect = self.calculateBoundingRect()

    def calculateBoundingRect(self):
        indices = np.where(self.mask)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return None
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        return QRectF(minCol, minRow, maxCol - minCol + 1, maxRow - minRow + 1)

    def hoverEvent(self, event):
        if event.isExit():
            self.parent.clearHighlight()
        else:
            pos = event.pos()
            # print(f"Hover Enter Event Triggered: {pos}")
            self.parent.highlightObjectAtPoint(pos)
