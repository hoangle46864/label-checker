import os
from PyQt5.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
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
from PyQt5.QtGui import QFont, QColor, QTextCursor
from PyQt5.QtCore import Qt, QThread
import csv
import numpy as np
from PIL import Image
# import pyqtgraph as pg
from custom_graphics_view_new import CustomGraphicsView
from worker_new import Worker


class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        mainLayout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        leftWidget = QWidget()
        leftLayout = QVBoxLayout()

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

        self.imageView = CustomGraphicsView(self)
        leftLayout.addWidget(self.imageView)
        leftWidget.setLayout(leftLayout)

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

        # self.btnMerge = QPushButton("Merge", self)
        # self.btnMerge.clicked.connect(self.mergeMaskAndImage)
        # rightLayout.addWidget(self.btnMerge)
        # self.btnMerge.setDisabled(True)

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

        # Display the base image in the ImageView
        try:
            self.baseImage = np.array(Image.open(self.imagePath))
            self.imageView.setImage(self.baseImage)

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

            # Get the initial opacity value from the slider
            initialOpacity = self.transparencySlider.value() / 100

            # Create and start the worker thread
            self.thread = QThread()
            self.worker = Worker(self, self.maskArray, self.objects, initialOpacity)
            self.worker.moveToThread(self.thread)

            # Connect signals and slots
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.updateLoadingProgressBar)
            self.worker.objectImagesReady.connect(self.setObjectImages)
            self.thread.finished.connect(self.loadingFinished)

            # Start the worker thread
            self.thread.start()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load image: {e}")

    def setObjectImages(self, objectImages):
        self.objectImages = objectImages
        for obj, item in self.objectImages.items():
            self.imageView.addItem(item)
            item.setAcceptHoverEvents(True)

    def updateQAProgressBar(self):
        checked_count = len(self.objectState["Object State"])
        self.qaProgressBar.setValue(checked_count)

        percentage = (checked_count / len(self.objects)) * 100
        self.qaProgressBar.setFormat(f"{percentage:.2f}% Checked")

    def updateLoadingProgressBar(self, value):
        self.loadingProgressBar.setValue(value)

    def loadingFinished(self):
        self.loadingProgressBar.setVisible(False)
        self.populateObjectList()

        self.toggleButton.setDisabled(False)
        self.btnNext.setDisabled(False)
        self.btnPre.setDisabled(False)
        self.btnYes.setDisabled(False)
        self.btnNo.setDisabled(False)
        # self.btnMerge.setDisabled(False)
        self.toggleButton.setDisabled(False)
        self.btnSaveInfo.setDisabled(False)
        self.btnloadInfo.setDisabled(False)
        self.btnNoForNonLabel.setDisabled(False)

        self.labelNameImage.setText(self.imagePath)
        self.labelNameMask.setText(self.maskPath)
        self.maskVisible = True
        self.imageView.setMouseTracking(True)

    def saveInfo(self):
        default_file_name = (
            "progress_" + os.path.splitext(os.path.basename(self.imagePath))[0] + ".csv"
        )
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

                    currentItem = int(
                        rows[index_to_split]
                        .get("Object Number", "")
                        .replace("label_", "")
                        .strip()
                    )
                    self.selectObjectById(currentItem)

                    haveLabel = rows[:index_to_split]

                    self.colorListItems(haveLabel)
                    self.loadObjectState(haveLabel)
                    self.updateQAProgressBar()

                    if index_to_split < len(rows):
                        self.noteNonLabel.clear()
                        nonLabel = rows[(index_to_split + 1):]
                        for row in nonLabel:
                            self.noteNonLabel.append(row["Note"])

                QMessageBox.information(self, "Success", "File loaded successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
        else:
            QMessageBox.warning(None, "Warning", "Load operation cancelled.")

    def loadObjectState(self, rows):
        self.objectState = {"Object Number": [], "Object State": [], "Note": []}
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

        textEdit.keyPressEvent = lambda event: self.handleKeyPress(
            event, dialog, textEdit
        )

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

    def toggleMask(self):
        self.maskVisible = not self.maskVisible
        for obj, item in self.objectImages.items():
            item.setVisible(self.maskVisible)

    def extractObjects(self, maskPath):
        maskImage = Image.open(maskPath)
        self.maskArray = np.array(maskImage)
        uniqueObjects = np.unique(self.maskArray)
        self.objects = uniqueObjects
        self.objects = self.objects[1:]
        self.objectPixelCount = {
            obj: np.sum(self.maskArray == obj) for obj in self.objects
        }
        self.qaProgressBar.setMaximum(len(self.objects))

    def populateObjectList(self):
        self.objectList.clear()
        for obj in self.objects:
            pixel_count = self.objectPixelCount[obj]
            item = QListWidgetItem(f"Object {int(obj)}: {pixel_count} pixels")
            self.objectList.addItem(item)

    def changeMask(self):
        current_object = self.objects[self.currentObjectIndex]
        self.objectImages[current_object].setVisible(self.maskVisible)
        self.scaleToObject(current_object)

    def previousObject(self):
        if self.currentObjectIndex > 0:
            self.currentObjectIndex -= 1
        self.objectList.setCurrentRow(self.currentObjectIndex)
        self.changeMask()
        self.imageView.drawBoundingBox(self.objects[self.currentObjectIndex])

    def nextObject(self):
        if self.currentObjectIndex < len(self.objects) - 1:
            self.currentObjectIndex += 1
        self.objectList.setCurrentRow(self.currentObjectIndex)
        self.changeMask()
        self.imageView.drawBoundingBox(self.objects[self.currentObjectIndex])

    def updateOpacityValue(self, value):
        self.opacityValue.setText(str(value))

    def changeTransparency(self, value):
        opacity = value / 100
        for item in self.objectImages.values():
            item.setOpacity(opacity)

    def scaleToObject(self, obj_id):
        maskClone = self.maskArray == obj_id
        indices = np.where(maskClone)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        self.imageView.getView().setRange(xRange=(minCol, maxCol), yRange=(minRow, maxRow), padding=1)

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

    def onItemClicked(self, item):
        index = self.objectList.row(item)
        self.currentObjectIndex = index
        self.changeMask()
        self.imageView.drawBoundingBox(self.objects[index])

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
            # print(f"Highlighting object: {obj}")
            if obj != 0:
                self.highlightSingleObject(obj)

    def highlightSingleObject(self, obj):
        # Remove transparency from all objects
        for _, item in self.objectImages.items():
            item.highlighted = False
            item.setOpacity(self.transparencySlider.value() / 100)
            item.update()

        # Highlighted current object
        highlighted_item = self.objectImages[obj]
        highlighted_item.highlighted = True
        highlighted_item.setOpacity(1.0)
        highlighted_item.update()
        # self.imageView.drawBoundingBox(obj)

    def clearHighlight(self):
        # Remove highlight from all objects
        for _, item in self.objectImages.items():
            item.highlighted = False
            item.setOpacity(self.transparencySlider.value() / 100)
            item.update()

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
