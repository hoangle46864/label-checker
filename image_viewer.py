from __future__ import annotations

import csv
import os
import random

import numpy as np
from PIL import Image
from PyQt5.QtCore import QRectF, Qt, QThread
from PyQt5.QtGui import QColor, QFont, QTextCursor
from PyQt5.QtWidgets import (
    QAction,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from edit_hot_key_dialog import EditHotkeysDialog
from image_grid_widget import ImageGridWidget
from worker import Worker


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)

        splitter = QSplitter(Qt.Horizontal)
        leftWidget = QWidget()
        leftLayout = QVBoxLayout(leftWidget)
        rightWidget = QWidget()
        rightLayout = QVBoxLayout(rightWidget)
        splitter.addWidget(leftWidget)
        splitter.addWidget(rightWidget)
        splitter.setStretchFactor(0, 4)

        self.setupMenus()
        self.setupLeftPanel(leftLayout)
        self.setupRightPanel(rightLayout)

        mainLayout.addWidget(splitter)

        self.setWindowTitle("Image and Mask Viewer")
        self.setGeometry(300, 300, 1200, 800)

        self.setupVariable()
        self.setupHotKeyDefault()

        # self.openImage(1)
        # self.openImage(2)
        # self.openImage(3)
        # self.openMask()

    def setupMenus(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("&File")
        doubleCheckMenu = menuBar.addMenu("&Double Check")
        editMenu = menuBar.addMenu("&Edit")

        openImageAction1 = QAction("&Open Image Channel 1", self)
        openImageAction2 = QAction("&Open Image Channel 2", self)
        openImageAction3 = QAction("&Open Image Channel 3", self)
        openMaskAction = QAction("&Open Mask", self)
        saveProgressAction = QAction("&Save Progress", self)
        loadProgressAction = QAction("&Load Progress", self)

        fileMenu.addAction(openImageAction1)
        fileMenu.addAction(openImageAction2)
        fileMenu.addAction(openImageAction3)
        fileMenu.addAction(openMaskAction)
        fileMenu.addSeparator()
        fileMenu.addAction(saveProgressAction)
        fileMenu.addAction(loadProgressAction)

        openImageAction1.triggered.connect(lambda: self.openImage(1))
        openImageAction2.triggered.connect(lambda: self.openImage(2))
        openImageAction3.triggered.connect(lambda: self.openImage(3))
        openMaskAction.triggered.connect(self.openMask)
        saveProgressAction.triggered.connect(self.saveProgress)
        loadProgressAction.triggered.connect(self.loadProgress)

        turnOnDoubleCheckMode = QAction("&On double check Mode", self)
        saveDoubleCheckAction = QAction("&Save Double Check", self)

        doubleCheckMenu.addAction(turnOnDoubleCheckMode)
        doubleCheckMenu.addAction(saveDoubleCheckAction)

        turnOnDoubleCheckMode.setCheckable(True)
        turnOnDoubleCheckMode.triggered.connect(self.startDoubleCheck)
        saveDoubleCheckAction.triggered.connect(self.saveDoubleCheckProgress)

        editHotKeyAction = QAction("&Edit Hot Key", self)

        editMenu.addAction(editHotKeyAction)

        editHotKeyAction.triggered.connect(self.editHotKey)

    def setupLeftPanel(self, leftLayout):
        self.labelNameImage = QLabel("Image: Not loaded")
        leftLayout.addWidget(self.labelNameImage)

        self.imageGridWidget = ImageGridWidget(self)
        self.imageGridWidget.pointTracked.connect(self.updateCoordinates)
        leftLayout.addWidget(self.imageGridWidget)

    def setupRightPanel(self, rightLayout):
        self.loadingProgressBar = QProgressBar(self)
        self.loadingProgressBar.setMaximum(100)
        self.loadingProgressBar.setValue(0)
        self.loadingProgressBar.setFormat("%p%")
        rightLayout.addWidget(self.loadingProgressBar)

        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(0)
        self.progressBar.setFormat("%p%")
        rightLayout.addWidget(self.progressBar)

        self.objectList = QListWidget()
        rightLayout.addWidget(self.objectList)
        self.objectList.itemClicked.connect(self.onItemClicked)

        self.btnNext = QPushButton("Next Object")
        self.btnNext.clicked.connect(self.nextObject)
        rightLayout.addWidget(self.btnNext)

        self.btnPre = QPushButton("Previous Object")
        self.btnPre.clicked.connect(self.previousObject)
        rightLayout.addWidget(self.btnPre)

        self.btnYes = QPushButton("Yes")
        self.btnYes.clicked.connect(self.markObjectYes)
        rightLayout.addWidget(self.btnYes)

        self.btnNo = QPushButton("No")
        self.btnNo.clicked.connect(self.markObjectNo)
        rightLayout.addWidget(self.btnNo)

        self.btnNoForNonLabel = QPushButton("No for non-label", self)
        self.btnNoForNonLabel.clicked.connect(self.noForNonLabel)
        rightLayout.addWidget(self.btnNoForNonLabel)

        self.toggleButton = QPushButton("Show/Hide Mask", self)
        self.toggleButton.clicked.connect(self.toggleMask)
        rightLayout.addWidget(self.toggleButton)

        self.coordinateLabel = QLabel(self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(30)
        self.coordinateLabel.setFont(font)
        self.coordinateLabel.setStyleSheet("color: black;")
        rightLayout.addWidget(self.coordinateLabel)

        sliderLayout = QHBoxLayout()
        self.sliderLabel = QLabel("Overall label opacity:", self)
        self.opacityValue = QLineEdit("100", self)
        self.opacityValue.setFixedWidth(50)
        self.transparencySlider = QSlider(Qt.Horizontal, self)
        self.transparencySlider.setMinimum(0)
        self.transparencySlider.setMaximum(100)
        self.transparencySlider.setValue(100)
        self.transparencySlider.setTickPosition(QSlider.TicksBelow)
        self.transparencySlider.setTickInterval(10)
        self.transparencySlider.valueChanged.connect(self.changeTransparency)
        self.transparencySlider.valueChanged.connect(self.updateOpacityValue)

        sliderLayout.addWidget(self.sliderLabel)
        sliderLayout.addWidget(self.opacityValue)
        sliderLayout.addWidget(self.transparencySlider)
        rightLayout.addLayout(sliderLayout)

    def setupVariable(self):
        self.channelPath = ["0", "1", "2", "3"]
        self.maskPath = ""
        self.imageName = ""

        self.modeDoubleCheck = False
        self.currentObjectIndex = 0
        self.savedLabel = False
        self.objects = []
        self.objects2 = []

        self.objectState = {}

        self.objectState["Object Number"] = []
        self.objectState["Object State"] = []
        self.objectState["Note"] = []

        self.objectStateDoubleCheck = {}

        self.objectStateDoubleCheck["Object Number"] = []
        self.objectStateDoubleCheck["Object State 1"] = []
        self.objectStateDoubleCheck["Object State 2"] = []
        self.objectStateDoubleCheck["Note"] = []

        self.noteNonLabel = []
        self.noteNonLabelDoubleCheck = []

    def openImage(self, num):
        try:
            filePath, _ = QFileDialog.getOpenFileName(
                self,
                "Open Image File",
                "/home",
                "Image files (*.tiff *.tif)",
            )
            # if num == 1:
            #     filePath = 'D://test-gui/Demo Images//Images//Channel_1//r01c02f02.tiff'
            # elif num == 2:
            #     filePath = 'D://test-gui//Demo Images//Images//Channel_2//r01c02f02.tiff'
            # else:
            #     filePath = 'D://test-gui//Demo Images//Images//Channel_3//r01c02f02.tiff'

            if not filePath:
                QMessageBox.information(self, "Information", "No file selected.")
                return

            tempImageName = os.path.basename(filePath)

            if self.imageName == "":
                self.imageName = tempImageName
            elif self.imageName != tempImageName:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Selected file name does not match the expected: " + self.imageName,
                )
                return

            self.channelPath[num] = filePath
            self.imageGridWidget.openImageAtPath(filePath, num, self.channelPath)
            self.labelNameImage.setText(tempImageName)

        except Exception as e:
            QMessageBox.critical(self, "Error", "Failed to load image: " + str(e))

    def openMask(self):
        try:
            filePath, _ = QFileDialog.getOpenFileName(
                self,
                "Open Image File",
                "/home",
                "Image files (*.tiff *.tif)",
            )
            # filePath = 'D://test-gui//Demo Images//Images//Mask//r01c02f02.tiff'
            if not filePath:
                QMessageBox.information(self, "Information", "No file selected.")
                return

            tempMaskName = os.path.basename(filePath)

            if self.imageName == "" or self.imageName != tempMaskName:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Selected file name does not match the expected: " + self.imageName,
                )
                return

            self.maskPath = filePath
            self.extractObjects(self.maskPath)

            try:
                # Create the worker thread
                self.worker = Worker(self.maskArray, self.objects)

                # Connect the signals and slots
                self.worker.finished.connect(self.loadingFinished)
                self.worker.progress.connect(self.updateLoadingProgressBar)

                # Ensure worker is properly cleaned up
                self.worker.finished.connect(self.worker.deleteLater)

                # Start the worker thread
                self.worker.start()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
                if hasattr(self, "worker") and self.worker.isRunning():
                    self.worker.quit()
                    self.worker.wait()

        except Exception as e:
            QMessageBox.critical(self, "Error", "Failed to load Mask: " + str(e))

    def updateLoadingProgressBar(self, value):
        self.loadingProgressBar.setValue(value)

    def loadingFinished(self):
        self.loadingProgressBar.setVisible(False)
        self.populateObjectList()
        self.imageGridWidget.changeMask("all_objects_with_low_opacity.tiff")
        self.imageGridWidget.toggleMouseTracking()

    def extractObjects(self, maskPath):
        maskImage = Image.open(maskPath)
        self.maskArray = np.array(maskImage)
        uniqueObjects = np.unique(self.maskArray)
        self.objects = uniqueObjects
        self.objects = self.objects[1:]
        self.objectPixelCount = {
            obj: np.sum(self.maskArray == obj) for obj in self.objects
        }
        self.progressBar.setMaximum(len(self.objects))

    def populateObjectList(self):
        self.objectList.clear()
        for obj in self.objects:
            pixelCount = self.objectPixelCount[obj]
            item = QListWidgetItem(f"Object {int(obj)}: {pixelCount} pixels")
            self.objectList.addItem(item)

    def changeMask(self):
        if not self.modeDoubleCheck:
            maskClone = np.where(
                self.maskArray == self.objects[self.currentObjectIndex],
                self.objects[self.currentObjectIndex],
                0,
            )
            outputImage = np.zeros(
                (maskClone.shape[0], maskClone.shape[1], 4),
                dtype=np.uint8,
            )
            color = self.worker.objectColors[self.objects[self.currentObjectIndex]]
            outputImage[maskClone != 0] = [*color, 255]
        else:
            maskClone = np.where(
                self.maskArray == self.objectsForDoubleCheck[self.currentObjectIndex],
                self.objectsForDoubleCheck[self.currentObjectIndex],
                0,
            )
            outputImage = np.zeros(
                (maskClone.shape[0], maskClone.shape[1], 4),
                dtype=np.uint8,
            )
            color = self.worker.objectColors[
                self.objectsForDoubleCheck[self.currentObjectIndex]
            ]
            outputImage[maskClone != 0] = [*color, 255]

        img = Image.fromarray(outputImage, "RGBA")
        img.save("output_image.tiff", compression="tiff_lzw")
        self.imageMaskClone = img

        self.imageGridWidget.changeMask("output_image.tiff", maskClone)

        self.scaleToObject(maskClone)
        self.imageGridWidget.changeTransparency(self.transparencySlider.value() / 100)

    def nextObject(self):
        if self.modeDoubleCheck:
            if self.currentObjectIndex < len(self.objectsForDoubleCheck) - 1:
                self.currentObjectIndex += 1
        else:
            if self.currentObjectIndex < len(self.objects) - 1:
                self.currentObjectIndex += 1

        self.objectList.setCurrentRow(self.currentObjectIndex)
        self.changeMask()

    def previousObject(self):
        if self.currentObjectIndex > 0:
            self.currentObjectIndex -= 1
        self.objectList.setCurrentRow(self.currentObjectIndex)
        self.changeMask()

    def scaleToObject(self, maskClone):
        indices = np.where(maskClone != 0)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        boundingRect = QRectF((minCol), minRow, (maxCol - minCol), (maxRow - minRow))
        self.imageGridWidget.scaleToObject(boundingRect)

        pointX = (minCol + maxCol) / 2
        pointY = (minRow + maxRow) / 2
        self.coordinateLabel.setText(f"{int(pointX)}, {int(pointY)}")

    def onItemClicked(self, item):
        index = self.objectList.row(item)
        self.currentObjectIndex = index
        self.changeMask()

    def toggleMask(self):
        self.imageGridWidget.toggleMask()

    def changeTransparency(self, value):
        opacity = value / 100
        self.imageGridWidget.changeTransparency(opacity)

    def updateOpacityValue(self, value):
        self.opacityValue.setText(str(value))

    def getReason(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Note")

        textEdit = QTextEdit(dialog)
        textEdit.setPlainText(f"({self.coordinateLabel.text()}) - ")
        textEdit.moveCursor(QTextCursor.End)

        textEdit.keyPressEvent = lambda event: self.handleKeyPress(
            event,
            dialog,
            textEdit,
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

    def insertState(self, label, note, flag):
        if not flag:
            self.insertStateNormal(label, note)
        else:
            self.insertStateDoubleCheck(label, note)

    def insertStateNormal(self, label, note):
        object_number = self.objects[self.currentObjectIndex]
        label_object_number = f"label_{int(object_number)}"
        if label_object_number in self.objectState["Object Number"]:
            index = self.objectState["Object Number"].index(label_object_number)
            self.objectState["Object State"][index] = label
            self.objectState["Note"][index] = note
        else:
            self.objectState["Object Number"].append(label_object_number)
            self.objectState["Object State"].append(label)
            self.objectState["Note"].append(note)

    def insertStateDoubleCheck(self, label, note):
        object_number = self.objectsForDoubleCheck[self.currentObjectIndex]
        label_object_number = f"label_{int(object_number)}"

        if label_object_number in self.objectState["Object Number"]:
            index = self.objectState["Object Number"].index(label_object_number)
            objectState1 = self.objectState["Object State"][index]
        else:
            objectState1 = None

        if label_object_number in self.objectStateDoubleCheck["Object Number"]:
            index = self.objectStateDoubleCheck["Object Number"].index(
                label_object_number,
            )
            self.objectStateDoubleCheck["Object State 2"][index] = label
            self.objectStateDoubleCheck["Note"][index] = note
        else:
            self.objectStateDoubleCheck["Object Number"].append(label_object_number)
            self.objectStateDoubleCheck["Object State 1"].append(objectState1)
            self.objectStateDoubleCheck["Object State 2"].append(label)
            self.objectStateDoubleCheck["Note"].append(note)

    def markObjectYes(self):
        reason = ""
        self.updateObjectListColor(self.currentObjectIndex, "green")
        self.updateProgressBar()
        self.insertState("Yes", reason, self.modeDoubleCheck)

    def markObjectNo(self):
        reason = self.getReason()
        self.insertState("No", reason, self.modeDoubleCheck)
        self.updateObjectListColor(self.currentObjectIndex, "red")
        self.updateProgressBar()

    def noForNonLabel(self):
        reason = self.getReason()
        if not self.modeDoubleCheck:
            self.noteNonLabel.append(reason)
        else:
            self.noteNonLabelDoubleCheck.append(reason)

    def updateObjectListColor(self, index, color):
        item = self.objectList.item(index)
        self.savedLabel = False
        if item:
            item.setBackground(QColor(color))

    def updateProgressBar(self):
        checked_count = len(self.objectState["Object State"])
        self.progressBar.setValue(checked_count)

        percentage = (checked_count / len(self.objects)) * 100
        self.progressBar.setFormat(f"{percentage:.2f}% Checked")

    def saveProgress(self):
        tempName = self.imageName.split(".", 1)
        self.saveFilePath, _ = QFileDialog.getSaveFileName(
            None,
            "Save CSV",
            tempName[0],
            "CSV Files (*.csv);;All Files (*)",
        )

        if self.saveFilePath:
            try:
                with open(
                    self.saveFilePath,
                    mode="w",
                    newline="",
                    encoding="utf-8-sig",
                ) as file:
                    writer = csv.DictWriter(file, fieldnames=self.objectState.keys())
                    writer.writeheader()
                    rows = [
                        dict(zip(self.objectState, t))
                        for t in zip(*self.objectState.values())
                    ]
                    rows.append(
                        {
                            "Object Number": f"label_{int(self.objects[self.currentObjectIndex])}",
                            "Object State": "Current index",
                            "Note": "",
                        },
                    )
                    for note in self.noteNonLabel:
                        rows.append(
                            {
                                "Object Number": None,
                                "Object State": None,
                                "Note": note,
                            },
                        )

                    writer.writerows(rows)
                QMessageBox.information(None, "Success", "File saved successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to save file: {e}")
        else:
            QMessageBox.warning(None, "Warning", "Save operation cancelled.")

    def loadProgress(self):
        self.loadFilePath, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "/home",
            "CSV Files (*.csv);;All Files (*)",
        )
        tempLoadName = os.path.basename(self.loadFilePath).split(".", 1)[0]
        tempName = self.imageName.split(".", 1)[0]

        if tempLoadName != tempName:
            QMessageBox.warning(
                self,
                "Warning",
                "Selected file name does not match the expected: " + self.imageName,
            )
            return

        if self.loadFilePath:
            try:
                with open(self.loadFilePath, encoding="utf-8-sig") as file:
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
                        .strip(),
                    )
                    self.selectObjectById(currentItem)

                    haveLabel = rows[:index_to_split]

                    self.colorListItems(haveLabel)
                    self.loadObjectState(haveLabel)
                    self.updateQAProgressBar()

                    if index_to_split < len(rows):
                        self.noteNonLabel.clear()
                        nonLabel = rows[index_to_split + 1 :]
                        for row in nonLabel:
                            self.noteNonLabel.append(row["Note"])

                QMessageBox.information(self, "Success", "File loaded successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
        else:
            QMessageBox.warning(None, "Warning", "Load operation cancelled.")

    def updateQAProgressBar(self):
        checked_count = len(self.objectState["Object State"])
        self.progressBar.setValue(checked_count)

        percentage = (checked_count / len(self.objects)) * 100
        self.progressBar.setFormat(f"{percentage:.2f}% Checked")

    def selectObjectById(self, obj_id):
        if obj_id in self.objects:
            index = self.objects.tolist().index(obj_id)
            self.objectList.setCurrentRow(index)
            self.onItemClicked(self.objectList.item(index))
            self.changeMask()

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

    def updateCoordinates(self, x, y):
        self.coordinateLabel.setText(f"{x}, {y}")

    def highlightObjectAtPoint(self, point):
        x, y = int(point.x()), int(point.y())
        if (
            x >= 0
            and y >= 0
            and x < self.maskArray.shape[1]
            and y < self.maskArray.shape[0]
            and self.imageGridWidget.maskVisible
        ):
            obj = self.maskArray[y, x]
            if obj != 0:
                self.highlightSingleObject(obj)

    def highlightSingleObject(self, obj):
        highlightedMaskArray = self.worker.maskImageArray.copy()

        # Increase the opacity of the hovered object
        mask_indices = self.maskArray == obj
        highlightedMaskArray[mask_indices, 3] = 255  # Set alpha channel to max

        # Create an image from the updated mask array
        highlightedMaskImage = Image.fromarray(highlightedMaskArray, "RGBA")
        highlightedMaskImage.save(
            "highlighted_single_object.tiff",
            compression="tiff_lzw",
        )

        self.imageGridWidget.addHighlight("highlighted_single_object.tiff")

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

    def startDoubleCheck(self):
        self.selectRandomObjectsForDoubleCheck()
        self.modeDoubleCheck = True

    def selectRandomObjectsForDoubleCheck(self, percentage=5):
        object_list = list(self.objects)
        total_objects = len(object_list)
        number_to_select = max(1, int((percentage / 100) * total_objects))
        self.objectsForDoubleCheck = random.sample(object_list, number_to_select)
        self.objectsForDoubleCheck = [int(obj) for obj in self.objectsForDoubleCheck]
        self.populateObjectListForDoubleCheck()

    def populateObjectListForDoubleCheck(self):
        self.objectList.clear()
        for obj in self.objectsForDoubleCheck:
            pixelCount = self.objectPixelCount[obj]
            item = QListWidgetItem(f"Object {int(obj)}: {pixelCount} pixels")
            self.objectList.addItem(item)

    def saveDoubleCheckProgress(self):
        tempName = self.imageName.split(".", 1)
        self.saveFilePathDoubleCheck, _ = QFileDialog.getSaveFileName(
            None,
            "Save CSV",
            tempName[0] + "_double_check",
            "CSV Files (*.csv);;All Files (*)",
        )

        if self.saveFilePathDoubleCheck:
            try:
                with open(
                    self.saveFilePathDoubleCheck,
                    mode="w",
                    newline="",
                    encoding="utf-8-sig",
                ) as file:
                    writer = csv.DictWriter(
                        file,
                        fieldnames=self.objectStateDoubleCheck.keys(),
                    )
                    writer.writeheader()
                    rows = [
                        dict(zip(self.objectStateDoubleCheck, t))
                        for t in zip(*self.objectStateDoubleCheck.values())
                    ]

                    for note in self.noteNonLabelDoubleCheck:
                        rows.append(
                            {
                                "Object Number": None,
                                "Object State 1": None,
                                "Object State 2": None,
                                "Note": note,
                            },
                        )

                    writer.writerows(rows)
                QMessageBox.information(None, "Success", "File saved successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to save file: {e}")
        else:
            QMessageBox.warning(None, "Warning", "Save operation cancelled.")

    def setupHotKeyDefault(self):
        self.hotkeys = {
            "Next": Qt.Key_D,
            "Previous": Qt.Key_A,
            "Yes": Qt.Key_I,
            "No": Qt.Key_O,
            "Toggle": Qt.Key_H,
            "Zoom In": Qt.Key_E,
            "Zoom Out": Qt.Key_Q,
        }

    def editHotKey(self):
        dlg = EditHotkeysDialog(self.hotkeys, self)
        if dlg.exec_():
            QMessageBox.information(self, "Info", "Hotkeys updated successfully.")
