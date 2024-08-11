import csv
import os

import numpy as np
import pandas as pd
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QKeySequence, QPixmap, QTextCursor
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGraphicsPixmapItem,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QSlider,
    QSplitter,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from custom_graphics_view import CustomGraphicsView
from tables import PandasModel
from worker import FindDisconnectedRegionsWorker, Worker


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

        self.btnFindDisconnected = QPushButton("Find Disconnected Regions", self)
        self.btnFindDisconnected.clicked.connect(self.findDisconnectedRegions)
        rightLayout.addWidget(self.btnFindDisconnected)
        self.btnFindDisconnected.setDisabled(True)

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

        # Create a menu bar
        menubar = QMenuBar(self)
        # Set the menu bar
        self.layout().setMenuBar(menubar)

        # Create a "File" menu
        fileMenu = menubar.addMenu("File")

        # Add action to preview the objectState
        previewObjectStateAction = QAction("Preview Object State", self)
        previewObjectStateAction.triggered.connect(self.previewObjectState)
        fileMenu.addAction(previewObjectStateAction)
        # Create the "Add Shortcuts" menu
        addShortcutsMenu = menubar.addMenu("Add Shortcuts")

        # Create the "Mark Object No With Predefined Reason" action
        markNoAction = QAction("Mark Object No With Predefined Reason", self)
        markNoAction.triggered.connect(self.createShortcutDialog)
        addShortcutsMenu.addAction(markNoAction)

        self.show()

        self.imagePath = ""
        self.maskPath = ""
        self.currentObjectIndex = 0
        self.savedLabel = False
        self.objects = []
        self.objectState = {}
        self.pixelDead = []

        self.objectState["Object Number"] = []
        self.objectState["Object State"] = []
        self.objectState["Note"] = []

        self.noteNonLabel = []

    # Method to open the dialog for creating a shortcut
    def createShortcutDialog(self):
        key_sequence, ok = QInputDialog.getText(
            self,
            "Shortcut Key",
            "Enter the shortcut key:",
        )
        if ok and key_sequence:
            reason, ok = QInputDialog.getText(
                self,
                "Predefined Reason",
                "Enter the reason:",
            )
            if ok and reason:
                self.registerShortcut(key_sequence, reason)
                QMessageBox.information(
                    self,
                    "Shortcut Added",
                    f'Shortcut "{key_sequence}" added with reason: "{reason}"',
                )

    def registerShortcut(self, key_sequence, reason):
        shortcut = QShortcut(QKeySequence(key_sequence), self)
        shortcut.activated.connect(lambda: self.markObjectNoWithReason(reason))

    def markObjectNoWithReason(self, reason):
        # Add coordinates before reason
        reason = f"({self.coordinateLabel.text()}) - " + reason
        self.insertState("No", reason)
        self.updateObjectListColor(self.currentObjectIndex, "red")
        self.updateQAProgressBar()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            self.nextObject()
        elif event.key() == Qt.Key_A:
            self.previousObject()
        elif event.key() == Qt.Key_I:
            self.markObjectYes()
        elif event.key() == Qt.Key_O:
            self.markObjectNo()
        elif event.key() == Qt.Key_H:
            self.toggleMask()
        else:
            super().keyPressEvent(event)

    def loadImage(self):
        self.imagePath, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "/home",
            "Image files (*.tiff *.tif)",
        )
        if not self.imagePath:
            return
        self.maskPath, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "/home",
            "Mask files (*.tiff *.tif)",
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

        # Clear the current mask
        if hasattr(self, "maskItem"):
            self.imageView.removeItem(self.maskItem)
        if hasattr(self, "singleMaskItem"):
            self.imageView.removeItem(self.singleMaskItem)
        if self.imageView.boundingBox:
            self.imageView.removeItem(self.imageView.boundingBox)

        # Clear object state and non-label notes
        self.objectState = {}

        self.objectState["Object Number"] = []
        self.objectState["Object State"] = []
        self.objectState["Note"] = []

        self.noteNonLabel = []
        self.pixelDead = []

        # Display the mask image
        self.maskPixmap = QPixmap("all_objects_with_low_opacity.tiff")
        self.maskItem = QGraphicsPixmapItem(self.maskPixmap)
        self.maskItem.setOpacity(self.transparencySlider.value() / 100)
        self.imageView.addItem(self.maskItem)

        self.populateObjectList()

        self.toggleButton.setDisabled(False)
        self.btnNext.setDisabled(False)
        self.btnPre.setDisabled(False)
        self.btnYes.setDisabled(False)
        self.btnNo.setDisabled(False)
        self.toggleButton.setDisabled(False)
        self.btnSaveInfo.setDisabled(False)
        self.btnloadInfo.setDisabled(False)
        self.btnNoForNonLabel.setDisabled(False)
        self.btnFindDisconnected.setDisabled(False)

        self.labelNameImage.setText(self.imagePath)
        self.labelNameMask.setText(self.maskPath)
        self.maskVisible = True
        self.imageView.setMouseTracking(True)

    def previewObjectState(self):
        # Convert objectState to a pandas DataFrame
        df = pd.DataFrame(self.objectState)

        # Append the `noteNonLabel` into the `Note` column of the DataFrame
        df_note_non_label = pd.DataFrame({"Note": self.noteNonLabel})

        df = pd.concat([df, df_note_non_label], axis=0)

        # Create a QDialog to display the DataFrame
        previewDialog = QDialog(self)
        previewDialog.setWindowTitle("Object State Preview")
        previewDialog.resize(800, 600)

        layout = QVBoxLayout(previewDialog)

        # Create a QTableView and set the PandasModel
        tableView = QTableView(previewDialog)
        model = PandasModel(df)
        tableView.setModel(model)

        # Set column width and row height
        tableView.horizontalHeader().setDefaultSectionSize(150)
        tableView.verticalHeader().setDefaultSectionSize(30)

        # Enable horizontal and vertical stretching
        tableView.horizontalHeader().setStretchLastSection(True)
        tableView.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Set the size policy to make the table view resizable
        tableView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(tableView)

        # Add an OK button to close the dialog
        btnBox = QDialogButtonBox(QDialogButtonBox.Ok, previewDialog)
        btnBox.accepted.connect(previewDialog.accept)
        layout.addWidget(btnBox)

        previewDialog.setLayout(layout)
        previewDialog.setSizeGripEnabled(True)  # Enable resizing
        previewDialog.exec_()

    def saveInfo(self):
        default_file_name = (
            "progress_" + os.path.splitext(os.path.basename(self.imagePath))[0] + ".csv"
        )
        self.saveFilePath, _ = QFileDialog.getSaveFileName(
            None,
            "Save CSV",
            default_file_name,
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
                            "Object Number": f"label_{self.objects[self.currentObjectIndex]}",
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

    def loadInfo(self):
        self.loadFilePath, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "/home",
            "CSV Files (*.csv);;All Files (*)",
        )

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
                        nonLabel = rows[(index_to_split + 1) :]
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
        if reason != "":
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
            if pixel_count <= 10:
                self.pixelDead.append(obj)

    def changeMask(self):
        # Get the current object
        current_object = self.objects[self.currentObjectIndex]

        # Create a mask clone for the current object
        maskClone = np.where(self.maskArray == current_object, current_object, 0)

        # Create an RGBA image with the same size as the mask
        outputImage = np.zeros(
            (maskClone.shape[0], maskClone.shape[1], 4),
            dtype=np.uint8,
        )

        # Set the color of the current object
        color = self.worker.objectColors[current_object]
        outputImage[maskClone != 0] = [*color, 255]  # Set RGBA with full opacity

        # Create an image from the mask array
        img = Image.fromarray(outputImage, "RGBA")
        img.save("output_image.tiff", compression="tiff_lzw")
        self.imageMaskClone = img

        # Remove existing mask items if present
        if hasattr(self, "maskItem"):
            self.imageView.removeItem(self.maskItem)
            del self.maskItem
        if hasattr(self, "singleMaskItem"):
            self.imageView.removeItem(self.singleMaskItem)
            del self.singleMaskItem

        # Display the new mask image
        self.singleMaskPixmap = QPixmap("output_image.tiff")
        self.singleMaskItem = QGraphicsPixmapItem(self.singleMaskPixmap)
        self.singleMaskItem.setOpacity(self.transparencySlider.value() / 100)
        self.imageView.addItem(self.singleMaskItem)
        self.maskVisible = True

        # Scale to the object
        self.scaleToObject(maskClone)

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
        if hasattr(self, "maskItem"):
            self.maskItem.setOpacity(opacity)
        if hasattr(self, "singleMaskItem"):
            self.singleMaskItem.setOpacity(opacity)

    def scaleToObject(self, maskClone):
        indices = np.where(maskClone)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        self.imageView.getView().setRange(
            xRange=(minCol, maxCol),
            yRange=(minRow, maxRow),
            padding=1,
        )

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
            self.imageView.drawBoundingBox(obj_id)

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
        # Create a copy of the original mask image with low opacity
        highlightedMaskArray = self.worker.maskImageArray.copy()

        # Find indices of the hovered object
        mask_indices = self.maskArray == obj

        # Set the opacity of the hovered object to max
        highlightedMaskArray[mask_indices, 3] = 255
        # Set the opacity of the other objects to min
        # highlightedMaskArray[~mask_indices, 3] = 0

        # Create an image from the updated mask array
        highlightedMaskImage = Image.fromarray(highlightedMaskArray, "RGBA")
        highlightedMaskImage.save(
            "highlighted_single_object.tiff",
            compression="tiff_lzw",
        )

        if hasattr(self, "singleMaskItem"):
            self.imageView.removeItem(self.singleMaskItem)
            del self.singleMaskItem

        self.singleMaskPixmap = QPixmap("highlighted_single_object.tiff")
        self.singleMaskItem = QGraphicsPixmapItem(self.singleMaskPixmap)
        self.singleMaskItem.setOpacity(self.transparencySlider.value() / 100)
        self.imageView.addItem(self.singleMaskItem)

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

    def findDisconnectedRegions(self):
        if self.maskArray is None:
            QMessageBox.warning(self, "Warning", "Please load an image and mask first.")
            return

        # Create and configure the progress dialog
        progressDialog = QProgressDialog(
            "Finding disconnected regions...",
            None,
            0,
            0,
            self,
        )
        progressDialog.setWindowModality(Qt.WindowModal)
        progressDialog.setWindowTitle("Progress")
        progressDialog.show()

        # Create the worker thread
        self.region_analysis_worker = FindDisconnectedRegionsWorker(
            self.maskArray,
            self.pixelDead,
        )
        self.region_analysis_worker.progress.connect(progressDialog.setValue)
        self.region_analysis_worker.finished.connect(
            self.onFindDisconnectedRegionsFinished,
        )

        # Start the worker thread
        self.region_analysis_worker.start()

        # Run the event loop until the worker is finished
        while self.region_analysis_worker.isRunning():
            QApplication.processEvents()

        progressDialog.close()

    def onFindDisconnectedRegionsFinished(self, disconnected_regions):
        for obj_id, info in disconnected_regions.items():
            count = info["count"]
            centroids = info["centroids"]
            reason = ", ".join(f"({x}, {y})" for x, y in centroids)

            if count > 1:
                reason = reason + " các toạ độ trùng label"
            else:
                reason = reason + " toạ độ label thừa chưa xoá"
            tmp = self.currentObjectIndex
            index = self.objects.tolist().index(obj_id)
            self.currentObjectIndex = index
            self.insertState("No", reason)
            self.updateObjectListColor(index, "red")
            self.updateQAProgressBar()
            self.currentObjectIndex = tmp

        QMessageBox.information(
            self,
            "Info",
            "Disconnected regions analysis completed.",
        )
