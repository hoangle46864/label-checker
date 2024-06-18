from PyQt5.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QDialog,
    QTextEdit,
    QDialogButtonBox,
    QLabel,
    QSlider,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QSplitter,
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt, QRectF
import sys
import csv
import numpy as np
from PIL import Image


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent):
        super().__init__(scene)
        self.parent = parent
        self.setMouseTracking(True)

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


class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        mainLayout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        leftWidget = QWidget()
        leftLayout = QVBoxLayout()
        leftWidget.setLayout(leftLayout)

        rightWidget = QWidget()
        rightLayout = QVBoxLayout()
        rightWidget.setLayout(rightLayout)

        splitter.addWidget(leftWidget)
        splitter.addWidget(rightWidget)
        splitter.setStretchFactor(0, 4)

        self.labelNameImage = QLabel("")
        leftLayout.addWidget(self.labelNameImage)

        self.labelNameMask = QLabel("")
        leftLayout.addWidget(self.labelNameMask)

        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        leftLayout.addWidget(self.view)

        self.progressBar = QProgressBar(self)
        rightLayout.addWidget(self.progressBar)
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(0)
        self.progressBar.setFormat("%p%")

        self.objectList = QListWidget(self)
        rightLayout.addWidget(self.objectList)
        self.objectList.itemClicked.connect(self.onItemClicked)

        self.btnLoad = QPushButton("Load Image", self)
        self.btnLoad.clicked.connect(self.loadImage)
        rightLayout.addWidget(self.btnLoad)

        self.btnNext = QPushButton("Next Object", self)
        self.btnNext.clicked.connect(self.nextObject)
        rightLayout.addWidget(self.btnNext)
        self.btnNext.setDisabled(True)

        self.btnPre = QPushButton("Previous Object", self)
        self.btnPre.clicked.connect(self.previousObject)
        rightLayout.addWidget(self.btnPre)
        self.btnPre.setDisabled(True)

        self.btnYes = QPushButton("Yes", self)
        self.btnYes.clicked.connect(self.markObjectYes)
        rightLayout.addWidget(self.btnYes)
        self.btnYes.setDisabled(True)

        self.btnNo = QPushButton("No", self)
        self.btnNo.clicked.connect(self.markObjectNo)
        rightLayout.addWidget(self.btnNo)
        self.btnNo.setDisabled(True)

        self.btnMerge = QPushButton("Merge", self)
        self.btnMerge.clicked.connect(self.mergeMaskAndImage)
        rightLayout.addWidget(self.btnMerge)
        self.btnMerge.setDisabled(True)

        self.toggleButton = QPushButton("Show/Hide Mask", self)
        self.toggleButton.clicked.connect(self.toggleMask)
        rightLayout.addWidget(self.toggleButton)
        self.toggleButton.setDisabled(True)

        self.btnSaveInfo = QPushButton("Save Progress", self)
        self.btnSaveInfo.clicked.connect(self.saveInfo)
        rightLayout.addWidget(self.btnSaveInfo)
        self.btnSaveInfo.setDisabled(True)

        self.btnloadInfo = QPushButton("Load Progress", self)
        self.btnloadInfo.clicked.connect(self.loadInfo)
        rightLayout.addWidget(self.btnloadInfo)
        self.btnloadInfo.setDisabled(True)

        self.coordinateLabel = QLabel(self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(30)
        self.coordinateLabel.setFont(font)
        self.coordinateLabel.setStyleSheet("color: black;")
        rightLayout.addWidget(self.coordinateLabel)

        sliderLayout = QHBoxLayout()
        self.sliderLabel = QLabel("Overall label opacity:", self)
        self.opacityValue = QLineEdit("50", self)
        self.opacityValue.setFixedWidth(50)
        self.transparencySlider = QSlider(Qt.Horizontal, self)
        self.transparencySlider.setMinimum(0)
        self.transparencySlider.setMaximum(100)
        self.transparencySlider.setValue(50)
        self.transparencySlider.setTickPosition(QSlider.TicksBelow)
        self.transparencySlider.setTickInterval(10)
        self.transparencySlider.valueChanged.connect(self.changeTransparency)
        self.transparencySlider.valueChanged.connect(self.updateOpacityValue)

        sliderLayout.addWidget(self.sliderLabel)
        sliderLayout.addWidget(self.opacityValue)
        sliderLayout.addWidget(self.transparencySlider)
        rightLayout.addLayout(sliderLayout)

        mainLayout.addWidget(splitter)
        self.setLayout(mainLayout)

        self.setWindowTitle("Image and Mask Viewer")
        self.setGeometry(300, 300, 1200, 800)

        self.show()

        self.imagePath = ""
        self.maskPath = ""
        self.currentObjectIndex = 0
        self.savedLabel = False
        self.objects = []
        self.objectState = {}

        self.objectState["Number object"] = []
        self.objectState["Object State"] = []
        self.objectState["Note"] = []

    def saveInfo(self):
        self.saveFilePath, _ = QFileDialog.getSaveFileName(
            None, "Save CSV", "", "CSV Files (*.csv);;All Files (*)"
        )

        if self.saveFilePath:
            try:
                with open(
                    self.saveFilePath, mode="w", newline="", encoding="utf-8-sig"
                ) as file:
                    writer = csv.DictWriter(file, fieldnames=self.objectState.keys())
                    writer.writeheader()
                    rows = [
                        dict(zip(self.objectState, t))
                        for t in zip(*self.objectState.values())
                    ]
                    rows.append(
                        {
                            "Number object": self.objects[self.currentObjectIndex],
                            "Object State": "Current index",
                            "Note": "",
                        }
                    )

                    writer.writerows(rows)
                QMessageBox.information(None, "Success", "File saved successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to save file: {e}")
        else:
            QMessageBox.warning(None, "Warning", "Save operation cancelled.")

    def loadInfo(self):
        self.loadFilePath, _ = QFileDialog.getOpenFileName(
            self, "Open file", "/home", "CSV Files (*.csv);;All Files (*)"
        )

        if self.loadFilePath:
            try:
                with open(self.loadFilePath, mode="r", encoding="utf-8-sig") as file:
                    reader = csv.DictReader(file)
                    rows = list(reader)

                    last_row = rows[-1]
                    rows = rows[:-1]

                    self.currentObjectIndex = int(float(last_row["Number object"]))
                    self.objectList.setCurrentRow(self.currentObjectIndex)
                    self.changeMask()

                    self.colorListItems(rows)
                    self.loadObjectState(rows)
                    self.updateProgressBar()

                QMessageBox.information(self, "Success", "File loaded successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
        else:
            QMessageBox.warning(None, "Warning", "Load operation cancelled.")

    def loadObjectState(self, rows):
        self.objectState.clear()
        for row in rows:
            self.objectState["Number object"].append(row["Number object"])
            self.objectState["Object State"].append(row["Object State"])
            self.objectState["Note"].append(row["Note"])

    def colorListItems(self, rows):
        for row in rows:
            numberObject = int(float(row["Number object"]))
            currentItem = self.objectList.findItems(
                f"Object {(numberObject)}: {self.objectPixelCount[numberObject]} pixels",
                Qt.MatchExactly,
            )
            if currentItem:
                if row["Object State"] == "Yes":
                    currentItem[0].setBackground(QColor("green"))
                elif row["Object State"] == "No":
                    currentItem[0].setBackground(QColor("Red"))

    def getReason(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Note")

        textEdit = QTextEdit(dialog)

        textEdit.keyPressEvent = lambda event: self.handleKeyPress(event, dialog, textEdit)

        btnBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        btnBox.accepted.connect(dialog.accept)
        btnBox.rejected.connect(dialog.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Please write reason for reject:"))
        layout.addWidget(textEdit)
        layout.addWidget(btnBox)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            reason = textEdit.toPlainText()
        else:
            reason = ""

        return reason

    def handleKeyPress(self, event, dialog, textEdit):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            dialog.accept()
        else:
            QTextEdit.keyPressEvent(textEdit, event)

    def insertState(self, label, note):
        numberObject = self.objects[self.currentObjectIndex]
        if numberObject in self.objectState["Number object"]:
            index = self.objectState["Number object"].index(numberObject)
            self.objectState["Object State"][index] = label
            self.objectState["Note"][index] = note
        else:
            self.objectState["Number object"].append(numberObject)
            self.objectState["Object State"].append(label)
            self.objectState["Note"].append(note)

    def markObjectYes(self):
        reason = ""
        self.insertState("Yes", reason)
        self.updateObjectListColor(self.currentObjectIndex, "green")
        self.updateProgressBar()

    def markObjectNo(self):
        reason = self.getReason()
        self.insertState("No", reason)
        self.updateObjectListColor(self.currentObjectIndex, "red")
        self.updateProgressBar()

    def loadImage(self):
        try:
            self.imagePath, _ = QFileDialog.getOpenFileName(
                self, "Open file", "/home", "Image files (*.tiff *.tif)"
            )
            self.maskPath, _ = QFileDialog.getOpenFileName(
                self, "Open file", "/home", "Mask files (*.tiff *.tif)"
            )

            self.basePixmap = QPixmap(self.imagePath)
            self.baseItem = QGraphicsPixmapItem(self.basePixmap)
            self.scene.addItem(self.baseItem)
            self.scene.setSceneRect(self.baseItem.boundingRect())
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

            self.extractObjects(self.maskPath)
            self.populateObjectList()
            self.displayAllObjectsWithLowOpacity()

            self.toggleButton.setDisabled(False)
            self.btnNext.setDisabled(False)
            self.btnPre.setDisabled(False)
            self.btnYes.setDisabled(False)
            self.btnNo.setDisabled(False)
            self.btnMerge.setDisabled(False)
            self.toggleButton.setDisabled(False)
            self.btnSaveInfo.setDisabled(False)
            self.btnloadInfo.setDisabled(False)

            self.labelNameImage.setText(self.imagePath)
            self.labelNameMask.setText(self.maskPath)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Load operation cancelled: {e}")

    def resizeEvent(self, event):
        if self.scene.items():
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def toggleMask(self):
        if self.maskVisible:
            if hasattr(self, "singleMaskItem"):
                self.singleMaskItem.hide()
            if hasattr(self, "maskItem"):
                self.maskItem.hide()
        else:
            if hasattr(self, "singleMaskItem"):
                self.singleMaskItem.show()
            elif hasattr(self, "maskItem"):
                self.maskItem.show()
        self.maskVisible = not self.maskVisible

    def extractObjects(self, maskPath):
        maskImage = Image.open(maskPath)
        self.maskArray = np.array(maskImage)
        uniqueObjects = np.unique(self.maskArray)
        self.objects = uniqueObjects
        self.objects = self.objects[1:]
        self.objectPixelCount = {obj: np.sum(self.maskArray == obj) for obj in self.objects}
        self.progressBar.setMaximum(len(self.objects))

    def populateObjectList(self):
        self.objectList.clear()
        for obj in self.objects:
            pixel_count = self.objectPixelCount[obj]
            item = QListWidgetItem(f"Object {int(obj)}: {pixel_count} pixels")
            self.objectList.addItem(item)

    def displayAllObjectsWithLowOpacity(self):
        # Create an empty RGBA image for the masks
        self.maskImageArray = np.zeros((self.maskArray.shape[0], self.maskArray.shape[1], 4), dtype=np.uint8)

        # Assign random colors to each object in the mask
        self.objectColors = {}
        for obj in self.objects:
            color = (np.random.randint(256), np.random.randint(256), np.random.randint(256))
            self.objectColors[obj] = color
            self.maskImageArray[self.maskArray == obj] = (*color, 75)  # RGBA with low opacity

        # Create an image from the mask array
        maskImage = Image.fromarray(self.maskImageArray, "RGBA")
        maskImage.save("all_objects_with_low_opacity.tiff")

        # Display the mask image in the QGraphicsView
        self.maskPixmap = QPixmap("all_objects_with_low_opacity.tiff")
        self.maskItem = QGraphicsPixmapItem(self.maskPixmap)
        self.scene.addItem(self.maskItem)
        self.maskItem.setOpacity(self.transparencySlider.value() / 100)
        self.maskVisible = True

    def mergeMaskAndImage(self):
        maskClone = np.where(self.maskArray != 0, 1, 0)
        img = Image.open(self.imagePath)
        imgArray = np.array(img)

        if len(imgArray.shape) == 3:
            for c in range(3):
                imgArray[:, :, c][maskClone == 1] = 0
        else:
            imgArray[maskClone == 1] = 0
        modifiedImage = Image.fromarray(imgArray)
        modifiedImage.save("output_image.tiff")

        if hasattr(self, "maskItem"):
            self.scene.removeItem(self.maskItem)
            del self.maskItem

        self.maskPixmap = QPixmap("output_image.tiff")
        self.maskItem = QGraphicsPixmapItem(self.maskPixmap)
        self.scene.addItem(self.maskItem)
        self.transparencySlider.setValue(100)
        self.maskVisible = True
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def changeMask(self):
        # Get the current object
        current_object = self.objects[self.currentObjectIndex]

        # Create a mask clone for the current object
        maskClone = np.where(self.maskArray == current_object, current_object, 0)

        # Create an RGBA image with the same size as the mask
        outputImage = np.zeros((maskClone.shape[0], maskClone.shape[1], 4), dtype=np.uint8)

        # Set the color of the current object
        color = self.objectColors[current_object]
        outputImage[maskClone != 0] = [*color, 255]  # Set RGBA with full opacity

        # Create an image from the mask array
        img = Image.fromarray(outputImage, "RGBA")
        img.save("output_image.tiff", compression="tiff_lzw")
        self.imageMaskClone = img

        # Remove existing mask items if present
        if hasattr(self, "maskItem"):
            self.scene.removeItem(self.maskItem)
            del self.maskItem
        if hasattr(self, "singleMaskItem"):
            self.scene.removeItem(self.singleMaskItem)
            del self.singleMaskItem

        # Display the new mask image
        self.singleMaskPixmap = QPixmap("output_image.tiff")
        self.singleMaskItem = QGraphicsPixmapItem(self.singleMaskPixmap)
        self.scene.addItem(self.singleMaskItem)
        self.singleMaskItem.setOpacity(self.transparencySlider.value() / 100)
        self.maskVisible = True

        # Scale to the object
        self.scaleToObject(maskClone)

    def previousObject(self):
        if self.currentObjectIndex > 0:
            self.currentObjectIndex -= 1
        self.objectList.setCurrentRow(self.currentObjectIndex)
        self.changeMask()

    def nextObject(self):
        if self.currentObjectIndex < len(self.objects) - 1:
            self.currentObjectIndex += 1
        self.objectList.setCurrentRow(self.currentObjectIndex)
        self.changeMask()

    def updateOpacityValue(self, value):
        self.opacityValue.setText(str(value))

    def changeTransparency(self, value):
        opacity = value / 100
        if hasattr(self, "maskItem"):
            self.maskItem.setOpacity(opacity)
        if hasattr(self, "singleMaskItem"):
            self.singleMaskItem.setOpacity(opacity)

    def scaleToObject(self, maskClone):
        indices = np.where(maskClone != 0)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        boundingRect = QRectF((minCol), minRow, (maxCol - minCol), (maxRow - minRow))
        self.view.fitInView(boundingRect, Qt.KeepAspectRatio)
        self.view.scale(1 / 4, 1 / 4)

        pointX = (minCol + maxCol) / 2
        pointY = (minRow + maxRow) / 2
        self.coordinateLabel.setText(f"{int(pointX)}, {int(pointY)}")

    def updateObjectListColor(self, index, color):
        item = self.objectList.item(index)
        self.savedLabel = False
        if item:
            item.setBackground(QColor(color))

    def onItemClicked(self, item):
        index = self.objectList.row(item)
        self.currentObjectIndex = index
        self.changeMask()

    def updateProgressBar(self):
        checked_count = len(self.objectState["Object State"])
        self.progressBar.setValue(checked_count)

        percentage = (checked_count / len(self.objects)) * 100
        self.progressBar.setFormat(f"{percentage:.2f}% Checked")

    def highlightObjectAtPoint(self, point):
        x, y = int(point.x()), int(point.y())
        if (
            x >= 0
            and y >= 0
            and x < self.maskArray.shape[1]
            and y < self.maskArray.shape[0]
            and self.maskVisible
        ):
            obj = self.maskArray[y, x]
            if obj != 0:
                self.highlightSingleObject(obj)

    def highlightSingleObject(self, obj):
        # Create a copy of the original mask image with low opacity
        highlightedMaskArray = self.maskImageArray.copy()

        # Increase the opacity of the hovered object
        mask_indices = self.maskArray == obj
        highlightedMaskArray[mask_indices, 3] = 255  # Set alpha channel to max

        # Create an image from the updated mask array
        highlightedMaskImage = Image.fromarray(highlightedMaskArray, "RGBA")
        highlightedMaskImage.save("highlighted_single_object.tiff", compression="tiff_lzw")

        if hasattr(self, "singleMaskItem"):
            self.scene.removeItem(self.singleMaskItem)
            del self.singleMaskItem

        self.singleMaskPixmap = QPixmap("highlighted_single_object.tiff")
        self.singleMaskItem = QGraphicsPixmapItem(self.singleMaskPixmap)
        self.scene.addItem(self.singleMaskItem)
        self.singleMaskItem.setOpacity(1.0)

    def closeEvent(self, event):
        if not self.savedLabel:
            reply = QMessageBox.question(
                self,
                "Message",
                "You have unsaved changes. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageViewer()
    sys.exit(app.exec_())
