import numpy as np
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QCursor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem
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
                    self.parent_view.parent.setFocus()
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
        self.drawMode = "draw"  # or 'erase' or 'new'
        self.view.setCursor(Qt.ArrowCursor)
        self.brushPreview = None
        self.updateCursor()

        # Create a hover event handler for the image item
        self.imageItem.hoverEvent = self.imageItemHoverEvent

    def imageItemHoverEvent(self, ev):
        """Handle hover events on the image item"""
        if not ev.isExit() and self.editMode:
            # Get position in scene coordinates
            pos = ev.scenePos()
            # Convert to view coordinates
            point = self.view_box.mapSceneToView(pos)
            x, y = point.x(), point.y()

            # Update the brush preview on hover
            self.updateBrushPreview(x, y)

        elif ev.isExit() or not self.editMode:
            # Remove the preview when mouse leaves or not in edit mode
            self.removeBrushPreview()

        # Let the event continue to propagate
        # No need to call original handler as it will continue naturally

    def mouseMoveEvent(self, event):
        """Handle mouse movement"""
        # Get scene coordinates and map to view coordinates with floating point precision
        point = self.view_box.mapSceneToView(event.scenePos())
        # Use exact floating point position (not integers) for the preview
        x, y = point.x(), point.y()

        # But use integers for actual drawing and checking
        x_int, y_int = int(x), int(y)

        if self.editMode:
            # Update brush preview position using exact floating point coordinates
            self.updateBrushPreview(x, y)

            # Handle drawing if mouse button is pressed
            if event.buttons() & Qt.LeftButton:
                if self.isValidPoint(x_int, y_int):
                    if self.lastPoint is not None:
                        self.drawLine(
                            self.lastPoint[0],
                            self.lastPoint[1],
                            x_int,
                            y_int,
                        )
                        self.parent.updateMaskDisplay()
                    self.lastPoint = (x_int, y_int)
        else:
            # Remove brush preview if not in edit mode
            self.removeBrushPreview()

            # Handle hover selection in normal mode
            if self.isValidPoint(x_int, y_int):
                obj = self.parent.maskArray[y_int, x_int]
                if obj != 0:
                    self.drawBoundingBox(obj)
                    self.parent.highlightObjectAtPoint(point)

    def updateBrushPreview(self, x, y):
        """Update the brush preview position and size"""
        # Remove existing preview if any
        self.removeBrushPreview()

        if not self.isValidPoint(int(x), int(y)):
            return

        brush_size = self.parent.currentBrushSize

        # Create a new preview ellipse
        radius = brush_size / 2

        # Create the ellipse centered exactly at the floating point coordinates
        preview_rect = QRectF(x - radius, y - radius, brush_size, brush_size)
        self.brushPreview = QGraphicsEllipseItem(preview_rect)

        # Set the pen style based on the draw mode
        pen = QPen(
            (
                QColor(255, 0, 0)
                if self.drawMode in ["draw", "new"]
                else QColor(255, 255, 255)
            ),
        )
        pen.setWidth(0.5)  # Set a thinner pen width
        pen.setStyle(Qt.DashLine if self.drawMode == "erase" else Qt.SolidLine)
        self.brushPreview.setPen(pen)

        # Add to view
        self.view.addItem(self.brushPreview)

    def removeBrushPreview(self):
        """Remove the brush preview if it exists"""
        if self.brushPreview is not None:
            self.view.removeItem(self.brushPreview)
            self.brushPreview = None

    def mousePressEvent(self, event):
        """Handle mouse press"""
        point = self.getView().mapSceneToView(event.pos())
        x, y = int(point.x()), int(point.y())

        if self.editMode and event.button() == Qt.LeftButton:
            # Temporarily remove the preview while drawing
            # self.removeBrushPreview()

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

            # Restore the preview after drawing
            point = self.getView().mapSceneToView(event.pos())
            x, y = point.x(), point.y()
            self.updateBrushPreview(x, y)

            # Ensure the parent widget gets focus back after drawing
            self.parent.setFocus()

            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def setEditMode(self, enabled):
        self.editMode = enabled
        self.view.editMode = enabled

        # Remove brush preview when exiting edit mode
        if not enabled:
            self.removeBrushPreview()

        # Use standard cursor, preview will show the brush area
        self.view.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)

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
            hasattr(self.parent, "maskArray")
            and 0 <= x < self.parent.maskArray.shape[1]
            and 0 <= y < self.parent.maskArray.shape[0]
        )

    def setDrawMode(self, mode):
        self.drawMode = mode

    def updateCursor(self):
        """Use a simpler cursor since we have the preview ellipse"""
        if not self.editMode:
            self.view.setCursor(Qt.ArrowCursor)
            self.removeBrushPreview()
        else:
            self.view.setCursor(Qt.CrossCursor)

            # If mouse is over the view, update the preview with new size
            pos = self.mapFromGlobal(QCursor.pos())
            if self.rect().contains(pos):
                point = self.view_box.mapSceneToView(self.getView().mapToScene(pos))
                self.updateBrushPreview(point.x(), point.y())

    def drawPoint(self, x, y):
        current_object = self.parent.objects[self.parent.currentObjectIndex]
        brush_size = self.parent.currentBrushSize

        # For brush_size 1, just draw a single pixel
        if brush_size == 1:
            if self.isValidPoint(x, y):
                # Only erase if the pixel belongs to current object
                if self.drawMode == "erase":
                    if self.parent.maskArray[y, x] == current_object:
                        self.parent.maskArray[y, x] = 0
                else:  # draw or new mode
                    self.parent.maskArray[y, x] = current_object
        else:
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

            # Get the region we're working with
            region = self.parent.maskArray[y_min:y_max, x_min:x_max]
            brush_mask = mask[mask_y_start:mask_y_end, mask_x_start:mask_x_end]

            if self.drawMode in ["draw", "new"]:
                # For drawing, simply apply the mask
                region[brush_mask] = current_object
            else:  # erase mode
                # Create a mask that only affects pixels of the current object
                erase_mask = brush_mask & (region == current_object)
                region[erase_mask] = 0

        # Update pixel count for the object
        mask_sum = np.sum(self.parent.maskArray == current_object)
        self.parent.objectPixelCount[current_object] = mask_sum
        # Update list item text
        item = self.parent.objectList.item(self.parent.currentObjectIndex)
        if item:
            item.setText(
                f"Object {int(current_object)}: {self.parent.objectPixelCount[current_object]} pixels",
            )

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
