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
    QSplitter)
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

        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        leftLayout.addWidget(self.view)

        self.objectList = QListWidget(self)
        rightLayout.addWidget(self.objectList)
        self.objectList.itemClicked.connect(self.onItemClicked)

        self.btnLoad = QPushButton('Load Image', self)
        self.btnLoad.clicked.connect(self.loadImage)
        rightLayout.addWidget(self.btnLoad)

        self.btnNext = QPushButton('Next Object', self)
        self.btnNext.clicked.connect(self.nextObject)
        rightLayout.addWidget(self.btnNext)
        self.btnNext.setDisabled(True)

        self.btnPre = QPushButton('Previous Object', self)
        self.btnPre.clicked.connect(self.previousObject)
        rightLayout.addWidget(self.btnPre)
        self.btnPre.setDisabled(True)

        self.btnYes = QPushButton('Yes', self)
        self.btnYes.clicked.connect(self.markObjectYes)
        rightLayout.addWidget(self.btnYes)
        self.btnYes.setDisabled(True)

        self.btnNo = QPushButton('No', self)
        self.btnNo.clicked.connect(self.markObjectNo)
        rightLayout.addWidget(self.btnNo)
        self.btnNo.setDisabled(True)
        
        self.btnMerge = QPushButton('Merge', self)
        self.btnMerge.clicked.connect(self.mergeMaskAndImage)
        rightLayout.addWidget(self.btnMerge)
        self.btnMerge.setDisabled(True)

        self.toggleButton = QPushButton('Show/Hide Mask', self)
        self.toggleButton.clicked.connect(self.toggleMask)
        rightLayout.addWidget(self.toggleButton)
        self.toggleButton.setDisabled(True)
        
        self.btnSaveInfo = QPushButton('Save Progress', self)
        self.btnSaveInfo.clicked.connect(self.saveInfo)
        rightLayout.addWidget(self.btnSaveInfo)
        self.btnSaveInfo.setDisabled(True)
        
        self.btnloadInfo = QPushButton('Load Progress', self)
        self.btnloadInfo.clicked.connect(self.loadInfo)
        rightLayout.addWidget(self.btnloadInfo)
        self.btnloadInfo.setDisabled(True)

        self.objectLabel = QLabel(self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(30)
        self.objectLabel.setFont(font)
        self.objectLabel.setStyleSheet("color: black;")
        rightLayout.addWidget(self.objectLabel)

        sliderLayout = QHBoxLayout()
        self.sliderLabel = QLabel('Overall label opacity:', self)
        self.opacityValue = QLineEdit('100', self)
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

        mainLayout.addWidget(splitter)
        self.setLayout(mainLayout)

        self.setWindowTitle('Image and Mask Viewer')
        self.setGeometry(300, 300, 1200, 800)

        self.show()

        self.imagePath = ''
        self.maskPath = ''
        self.currentObjectIndex = 0
        self.savedLabel = False
        self.objects = []
        self.objectState = {}

        self.objectState['Number object'] = []
        self.objectState['Object State'] = []
        self.objectState['Note'] = []

    def saveInfo(self):
        self.saveFilePath, _ = QFileDialog.getSaveFileName(None, "Save CSV", "", "CSV Files (*.csv);;All Files (*)")
        
        if self.saveFilePath:
            try:
                with open(self.saveFilePath, mode='w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.DictWriter(file, fieldnames=self.objectState.keys())
                    writer.writeheader()
                    rows = [dict(zip(self.objectState, t)) for t in zip(*self.objectState.values())]
                    rows.append({'Number object': self.objects[self.currentObjectIndex], 'Object State': 'Current index', 'Note': ''})
                    
                    writer.writerows(rows)
                QMessageBox.information(None, "Success", "File saved successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to save file: {e}")
        else:
            QMessageBox.warning(None, "Warning", "Save operation cancelled.")

    def loadInfo(self):
        self.loadFilePath, _ = QFileDialog.getOpenFileName(self, 'Open file', '/home', "CSV Files (*.csv);;All Files (*)")

        if self.loadFilePath:
            try:
                with open(self.loadFilePath, mode='r', encoding='utf-8-sig') as file:
                    reader = csv.DictReader(file)
                    rows = list(reader)
                    
                    last_row = rows[-1]
                    rows = rows[:-1]
                    
                    self.currentObjectIndex = int(float(last_row['Number object']))
                    self.objectList.setCurrentRow(self.currentObjectIndex)
                    self.changeMask()
                    
                    self.colorListItems(rows)

                QMessageBox.information(self, "Success", "File loaded successfully.")
                self.savedLabel = True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
        else:
            QMessageBox.warning(self, "Warning", "Load operation cancelled.")
    
    def colorListItems(self, rows):
        for row in rows:
            numberObject = int(float(row['Number object']))
            currentItem = self.objectList.findItems(f"Object {numberObject}", Qt.MatchExactly)
            if currentItem:
                if row['Object State'] == "Yes":
                    currentItem[0].setBackground(Qt.green)
                elif row['Object State'] == "No":
                    currentItem[0].setBackground(Qt.red)

    def getReason(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Note')
        
        textEdit = QTextEdit(dialog)
        
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

    def insertState(self, label, note):
        self.objectState['Number object'].append(self.objects[self.currentObjectIndex])
        self.objectState['Object State'].append(label)
        self.objectState['Note'].append(note)

    def markObjectYes(self):
        reason = ""
        self.insertState("Yes", reason)
        self.updateObjectListColor(self.currentObjectIndex, 'green')
    
    def markObjectNo(self):
        reason = self.getReason()
        self.insertState("No", reason)
        self.updateObjectListColor(self.currentObjectIndex, 'red')

    def loadImage(self):
        self.imagePath, _ = QFileDialog.getOpenFileName(self, 'Open file', '/home', "Image files (*.tiff *.tif)")
        self.maskPath, _ = QFileDialog.getOpenFileName(self, 'Open file', '/home', "Mask files (*.tiff *.tif)")

        # self.imagePath = "mask12.tiff"
        # self.maskPath = "bac12.tiff"
        
        self.basePixmap = QPixmap(self.imagePath)
        self.baseItem = QGraphicsPixmapItem(self.basePixmap)
        self.scene.addItem(self.baseItem)
        self.scene.setSceneRect(self.baseItem.boundingRect())
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio) 
        
        self.extractObjects(self.maskPath)
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
            
    def resizeEvent(self, event):
        if self.scene.items():
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def toggleMask(self):
        if self.maskVisible:
            self.maskItem.hide()
        else:
            self.maskItem.show()
        self.maskVisible = not self.maskVisible
        
    def extractObjects(self, maskPath):
        maskImage = Image.open(maskPath)
        self.maskArray = np.array(maskImage)
        uniqueObjects = np.unique(self.maskArray)
        self.objects = uniqueObjects

    def populateObjectList(self):
        self.objectList.clear()
        for obj in self.objects:
            item = QListWidgetItem(f"Object {int(obj)}")
            self.objectList.addItem(item)
        
    def mergeMaskAndImage(self):
        maskClone = np.where(self.maskArray != 0, 1, 0)
        img = Image.open(self.imagePath)
        imgArray = np.array(img)

        if len(imgArray.shape) == 3:
            for c in range(3):
                imgArray[:,:,c][maskClone == 1] = 0
        else:
            imgArray[maskClone == 1] = 0
        modifiedImage = Image.fromarray(imgArray)
        modifiedImage.save('output_image.tiff')

        if hasattr(self, 'maskItem'):
            self.scene.removeItem(self.maskItem)
            del self.maskItem

        self.maskPixmap = QPixmap('output_image.tiff')
        self.maskItem = QGraphicsPixmapItem(self.maskPixmap)
        self.scene.addItem(self.maskItem)
        self.transparencySlider.setValue(100)
        self.maskVisible = True
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio) 
        
    def changeMask(self):
        maskClone = np.where(self.maskArray == self.objects[self.currentObjectIndex], self.objects[self.currentObjectIndex], 0)

        outputImage = np.zeros((maskClone.shape[0], maskClone.shape[1], 4), dtype=np.uint8)
        outputImage[maskClone != 0] = [255, 0, 0, 255]
        outputImage[maskClone == 0] = [0, 0, 0, 0]
        
        img = Image.fromarray(outputImage, 'RGBA')
        img.save('output_image.tiff', compression='tiff_lzw')
        self.imageMaskClone = img

        if hasattr(self, 'maskItem'):
            self.scene.removeItem(self.maskItem)
            del self.maskItem

        self.maskPixmap = QPixmap('output_image.tiff')
        self.maskItem = QGraphicsPixmapItem(self.maskPixmap)
        self.maskItem.setOpacity(0.5)
        self.transparencySlider.setValue(50)

        self.scene.addItem(self.maskItem)
        self.maskVisible = True

        self.scaleToObject(maskClone)
        self.objectLabel.setText(f"{int(self.objects[self.currentObjectIndex])}")

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
        if hasattr(self, 'maskItem'):
            self.maskItem.setOpacity(opacity)

    def scaleToObject(self, maskClone):
        indices = np.where(maskClone != 0)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        boundingRect = QRectF(minCol, minRow, maxCol - minCol, maxRow - minRow)
        self.view.fitInView(boundingRect, Qt.KeepAspectRatio)
        self.view.scale(1/2, 1/2)

    def updateObjectListColor(self, index, color):
        item = self.objectList.item(index)
        self.savedLabel = False
        if item:
            item.setBackground(QColor(color))
            
    def onItemClicked(self, item):
        index = self.objectList.row(item)
        self.currentObjectIndex = index
        self.changeMask()

    def closeEvent(self, event):
        if not self.savedLabel:
            reply = QMessageBox.question(self, 'Message', 
                "You have unsaved changes. Are you sure you want to quit?", 
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    sys.exit(app.exec_())