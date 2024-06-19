import os
from PyQt5.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
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
from PyQt5.QtGui import QPixmap, QFont, QColor, QTextCursor
from PyQt5.QtCore import Qt, QRectF, QThread
import csv
import numpy as np
from PIL import Image
from custom_graphics_view import CustomGraphicsView
from worker import Worker


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

        # Progress bar for loading and processing
        self.loadingProgressBar = QProgressBar(self)
        rightLayout.addWidget(self.loadingProgressBar)
        self.loadingProgressBar.setMaximum(100)
        self.loadingProgressBar.setValue(0)
        self.loadingProgressBar.setFormat("%p%")

        # QA progress bar
        self.qaProgressBar = QProgressBar(self)
        rightLayout.addWidget(self.qaProgressBar)
        self.qaProgressBar.setMaximum(0)
        self.qaProgressBar.setValue(0)
        self.qaProgressBar.setFormat("%p%")

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

        self.btnNoForNonLabel = QPushButton("No for non-label", self)
        self.btnNoForNonLabel.clicked.connect(self.noForNonLabel)
        rightLayout.addWidget(self.btnNoForNonLabel)
        self.btnNoForNonLabel.setDisabled(True)

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

        self.objectState["Object Number"] = []
        self.objectState["Object State"] = []
        self.objectState["Note"] = []
        
        self.noteNonLabel = []

    def loadImage(self):
        self.imagePath, _ = QFileDialog.getOpenFileName(
            self, "Open file", "/home", "Image files (*.tiff *.tif)"
        )
        if not self.imagePath:
            return
        self.maskPath, _ = QFileDialog.getOpenFileName(
            self, "Open file", "/home", "Mask files (*.tiff *.tif)"
        )
        if not self.maskPath:
            return

        # Display the base image in the QGraphicsView
        try:
            # Initialize the QGraphicsScene
            self.basePixmap = QPixmap(self.imagePath)
            self.baseItem = QGraphicsPixmapItem(self.basePixmap)
            self.scene.addItem(self.baseItem)
            self.scene.setSceneRect(self.baseItem.boundingRect())
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

            # Initialize loading progress bar
            self.loadingProgressBar.setMaximum(100)
            self.loadingProgressBar.setValue(0)
            self.loadingProgressBar.setVisible(True)

            # Initialize QA progress bar
            self.qaProgressBar.setMaximum(0)
            self.qaProgressBar.setValue(0)
            self.qaProgressBar.setFormat("%p%")

            # Extract objects from the mask
            self.extractObjects(self.maskPath)

            # Create and start the worker thread
            self.thread = QThread()
            self.worker = Worker(self.maskArray, self.objects)
            self.worker.moveToThread(self.thread)

            # Connect signals and slots
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.updateLoadingProgressBar)
            self.thread.finished.connect(self.loadingFinished)

            # Start the worker thread
            self.thread.start()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load image: {e}")

    def updateQAProgressBar(self):
        checked_count = len(self.objectState["Object State"])
        self.qaProgressBar.setValue(checked_count)

        percentage = (checked_count / len(self.objects)) * 100
        self.qaProgressBar.setFormat(f"{percentage:.2f}% Checked")

    def updateLoadingProgressBar(self, value):
        self.loadingProgressBar.setValue(value)

    def loadingFinished(self):
        self.loadingProgressBar.setVisible(False)

        # Display the mask image in the QGraphicsView
        self.maskPixmap = QPixmap("all_objects_with_low_opacity.tiff")
        self.maskItem = QGraphicsPixmapItem(self.maskPixmap)
        self.scene.addItem(self.maskItem)
        self.maskItem.setOpacity(0.5)

        self.populateObjectList()

        self.toggleButton.setDisabled(False)
        self.btnNext.setDisabled(False)
        self.btnPre.setDisabled(False)
        self.btnYes.setDisabled(False)
        self.btnNo.setDisabled(False)
        self.btnMerge.setDisabled(False)
        self.toggleButton.setDisabled(False)
        self.btnSaveInfo.setDisabled(False)
        self.btnloadInfo.setDisabled(False)
        self.btnNoForNonLabel.setDisabled(False)

        self.labelNameImage.setText(self.imagePath)
        self.labelNameMask.setText(self.maskPath)
        self.view.setMouseTracking(True)
        self.maskVisible = True

    def saveInfo(self):
        default_file_name = "progress_" + os.path.splitext(os.path.basename(self.imagePath))[0] + ".csv"
        self.saveFilePath, _ = QFileDialog.getSaveFileName(
            None, "Save CSV", default_file_name, "CSV Files (*.csv);;All Files (*)"
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
                            "Object Number": f"label_{self.objects[self.currentObjectIndex]}",
                            "Object State": "Current index",
                            "Note": "",
                        }
                    )
                    for note in self.noteNonLabel:
                        rows.append(
                            {
                                "Object Number": None,
                                "Object State": None,
                                "Note": note,  
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

                    index_to_split = None
                    for i, row in enumerate(rows):
                        if row["Object State"] == "Current index":
                            index_to_split = i
                            break
                    
                    currentItem = int(rows[index_to_split].get("Object Number", "").replace("label_", "").strip())
                    self.selectObjectById(currentItem)

                    haveLabel = rows[:index_to_split]

                    self.colorListItems(haveLabel)
                    self.loadObjectState(haveLabel)
                    self.updateQAProgressBar()

                    if index_to_split < len(rows):
                        self.noteNonLabel.clear()
                        nonLabel = rows[index_to_split + 1:]
                        for row in nonLabel:
                            self.noteNonLabel.append(row["Note"])

                QMessageBox.information(self, "Success", "File loaded successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
        else:
            QMessageBox.warning(None, "Warning", "Load operation cancelled.")

    def loadObjectState(self, rows):
        self.objectState = {
            "Object Number": [],
            "Object State": [],
            "Note": []
        }
        for row in rows:
            self.objectState["Object Number"].append(row["Object Number"])
            self.objectState["Object State"].append(row["Object State"])
            self.objectState["Note"].append(row["Note"])

    def colorListItems(self, rows):
        for row in rows:
            numberObject = int(row["Object Number"].replace("label_", ""))
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
        textEdit.setPlainText(f"({self.coordinateLabel.text()}) - ")
        textEdit.moveCursor(QTextCursor.End)

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
        object_number = self.objects[self.currentObjectIndex]
        label_object_number = f"label_{object_number}"
        if label_object_number in self.objectState["Object Number"]:
            index = self.objectState["Object Number"].index(label_object_number)
            self.objectState["Object State"][index] = label
            self.objectState["Note"][index] = note
        else:
            self.objectState["Object Number"].append(label_object_number)
            self.objectState["Object State"].append(label)
            self.objectState["Note"].append(note)

    def noForNonLabel(self):
        reason = self.getReason()
        self.noteNonLabel.append(reason)

    def markObjectYes(self):
        reason = ""
        self.insertState("Yes", reason)
        self.updateObjectListColor(self.currentObjectIndex, "green")
        self.updateQAProgressBar()

    def markObjectNo(self):
        reason = self.getReason()
        self.insertState("No", reason)
        self.updateObjectListColor(self.currentObjectIndex, "red")
        self.updateQAProgressBar()

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
        self.qaProgressBar.setMaximum(len(self.objects))

    def populateObjectList(self):
        self.objectList.clear()
        for obj in self.objects:
            pixel_count = self.objectPixelCount[obj]
            item = QListWidgetItem(f"Object {int(obj)}: {pixel_count} pixels")
            self.objectList.addItem(item)

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
        color = self.worker.objectColors[current_object]
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
        self.view.drawBoundingBox(self.objects[self.currentObjectIndex])

    def nextObject(self):
        if self.currentObjectIndex < len(self.objects) - 1:
            self.currentObjectIndex += 1
        self.objectList.setCurrentRow(self.currentObjectIndex)
        self.changeMask()
        self.view.drawBoundingBox(self.objects[self.currentObjectIndex])

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

    def selectObjectById(self, obj_id):
        if obj_id in self.objects:
            index = self.objects.tolist().index(obj_id)
            self.objectList.setCurrentRow(index)
            self.onItemClicked(self.objectList.item(index))
            self.view.drawBoundingBox(obj_id)

    def onItemClicked(self, item):
        index = self.objectList.row(item)
        self.currentObjectIndex = index
        self.changeMask()
        self.view.drawBoundingBox(self.objects[index])

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
        highlightedMaskArray = self.worker.maskImageArray.copy()

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
