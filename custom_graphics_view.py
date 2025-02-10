import numpy as np
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QCursor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QGraphicsRectItem
from pyqtgraph import ImageView, ViewBox


class CustomViewBox(ViewBox):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.editMode = False
        self.isDrawing = False
        self.lastPoint = None

    def mouseDragEvent(self, ev):
        if self.editMode:
            # Get scene coordinates and map to data coordinates
            pos = self.mapSceneToView(ev.scenePos())
            x, y = int(pos.x()), int(pos.y())

            if ev.button() == Qt.LeftButton:
                if ev.isStart():  # Mouse press
                    if self.parent_view.isValidPoint(x, y):
                        self.isDrawing = True
                        self.lastPoint = (x, y)
                        self.parent_view.parent.undoStack.append(
                            self.parent_view.parent.maskArray.copy(),
                        )
                        self.parent_view.drawPoint(x, y)
                        self.parent_view.parent.updateMaskDisplay()
                elif ev.isFinish():  # Mouse release
                    self.isDrawing = False
                    self.lastPoint = None
                    self.parent_view.parent.changeMask()
                else:  # Mouse move
                    if self.isDrawing and self.lastPoint is not None:
                        if self.parent_view.isValidPoint(x, y):
                            self.parent_view.drawLine(
                                self.lastPoint[0],
                                self.lastPoint[1],
                                x,
                                y,
                            )
                            self.parent_view.parent.updateMaskDisplay()
                            self.lastPoint = (x, y)
            ev.accept()
        else:
            super().mouseDragEvent(ev)  # Normal panning in view mode

    def mouseClickEvent(self, ev):
        if self.editMode:
            ev.accept()
        else:
            super().mouseClickEvent(ev)


class CustomGraphicsView(ImageView):
    def __init__(self, parent):
        # Create custom ViewBox
        self.view_box = CustomViewBox(self)  # Pass self as parent_view
        super().__init__(view=self.view_box)
        self.parent = parent
        self.setMouseTracking(True)
        self.boundingBox = None
        self.editMode = False
        self.drawMode = "draw"  # or 'erase'
        self.view.setCursor(Qt.ArrowCursor)
        self.updateCursor()  # Add this line

    def mouseMoveEvent(self, event):
        """Handle mouse movement"""
        point = self.getView().mapSceneToView(event.pos())
        x, y = int(point.x()), int(point.y())

        if self.editMode:
            # Handle drawing if mouse button is pressed
            if event.buttons() & Qt.LeftButton:
                if self.isValidPoint(x, y):
                    if self.lastPoint is not None:
                        self.drawLine(self.lastPoint[0], self.lastPoint[1], x, y)
                        self.parent.updateMaskDisplay()
                    self.lastPoint = (x, y)
        else:
            # Handle hover selection in normal mode
            if self.isValidPoint(x, y):
                obj = self.parent.maskArray[y, x]
                if obj != 0:
                    self.drawBoundingBox(obj)
                    self.parent.highlightObjectAtPoint(point)

    def mousePressEvent(self, event):
        """Handle mouse press"""
        point = self.getView().mapSceneToView(event.pos())
        x, y = int(point.x()), int(point.y())

        if self.editMode and event.button() == Qt.LeftButton:
            if self.isValidPoint(x, y):
                self.parent.undoStack.append(self.parent.maskArray.copy())
                self.lastPoint = (x, y)
                self.drawPoint(x, y)
                self.parent.updateMaskDisplay()
            event.accept()
        else:
            # Only update coordinates on single click
            self.parent.coordinateLabel.setText(f"{int(point.x())}, {int(point.y())}")
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click for object selection"""
        if not self.editMode:
            point = self.getView().mapSceneToView(event.pos())
            x, y = int(point.x()), int(point.y())

            if self.isValidPoint(x, y):
                obj = self.parent.maskArray[y, x]
                if obj != 0 and obj in self.parent.objects:
                    index = self.parent.objects.tolist().index(obj)
                    self.parent.objectList.setCurrentRow(index)
                    self.parent.onItemClicked(self.parent.objectList.item(index))

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.editMode and event.button() == Qt.LeftButton:
            self.lastPoint = None
            self.parent.changeMask()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def setEditMode(self, enabled):
        self.editMode = enabled
        self.view.editMode = enabled
        self.updateCursor()  # Replace cursor setting with this

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

    def isValidPoint(self, x, y):
        return (
            0 <= x < self.parent.maskArray.shape[1]
            and 0 <= y < self.parent.maskArray.shape[0]
        )

    def setDrawMode(self, mode):
        self.drawMode = mode

    def updateCursor(self):
        """Create a circular cursor based on brush size"""
        if not self.editMode:
            self.view.setCursor(Qt.ArrowCursor)
            return

        # Scale up the cursor size (multiply by 5 to make it appear larger)
        display_size = self.parent.currentBrushSize * 5

        # Create a larger pixmap for better visibility
        pixmap = QPixmap(display_size, display_size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        # Enable antialiasing for smoother circle
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw outer circle (black)
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(1, 1, display_size - 2, display_size - 2)

        # Draw inner circle (white) for better visibility
        painter.setPen(QPen(Qt.white, 1))
        painter.drawEllipse(2, 2, display_size - 4, display_size - 4)

        painter.end()

        # Set the cursor hot spot to the center of the circle
        cursor = QCursor(pixmap, display_size // 2, display_size // 2)
        self.view.setCursor(cursor)

    def drawPoint(self, x, y):
        current_object = self.parent.objects[self.parent.currentObjectIndex]
        brush_size = self.parent.currentBrushSize

        # For brush_size 1, just draw a single pixel
        if brush_size == 1:
            if self.isValidPoint(x, y):
                self.parent.maskArray[y, x] = (
                    current_object if self.drawMode == "draw" else 0
                )
            return

        # For larger brushes, create a circular brush
        radius = brush_size // 2
        y_indices, x_indices = np.ogrid[-radius : radius + 1, -radius : radius + 1]
        # Create circular mask
        mask = x_indices * x_indices + y_indices * y_indices <= radius * radius

        # Create a circular brush using distance calculation
        radius = brush_size / 2
        y_indices, x_indices = np.ogrid[-radius : radius + 1, -radius : radius + 1]
        distances = np.sqrt(x_indices * x_indices + y_indices * y_indices)
        mask = distances <= radius

        # Get bounds for the brush area
        y_min, y_max = int(y - radius), int(y + radius + 1)
        x_min, x_max = int(x - radius), int(x + radius + 1)

        # Clip bounds to image size
        y_min = max(0, y_min)
        y_max = min(self.parent.maskArray.shape[0], y_max)
        x_min = max(0, x_min)
        x_max = min(self.parent.maskArray.shape[1], x_max)

        # Calculate mask indices after clipping
        mask_y_start = y_min - int(y - radius)
        mask_y_end = mask_y_start + (y_max - y_min)
        mask_x_start = x_min - int(x - radius)
        mask_x_end = mask_x_start + (x_max - x_min)

        # Apply the mask
        if self.drawMode == "draw":
            self.parent.maskArray[y_min:y_max, x_min:x_max][
                mask[mask_y_start:mask_y_end, mask_x_start:mask_x_end]
            ] = current_object
        else:  # erase mode
            self.parent.maskArray[y_min:y_max, x_min:x_max][
                mask[mask_y_start:mask_y_end, mask_x_start:mask_x_end]
            ] = 0

    def drawLine(self, x1, y1, x2, y2):
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            self.drawPoint(x, y)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
