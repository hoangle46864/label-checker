from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QHBoxLayout, QDialog, QTextEdit, QDialogButtonBox, QLabel
from PyQt5.QtGui import QPixmap, QFont
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
        mainLayout = QHBoxLayout()

        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        mainLayout.addWidget(self.view)

        buttonLayout = QVBoxLayout()

        btnLoad = QPushButton('Load Image', self)
        btnLoad.clicked.connect(self.loadImage)
        buttonLayout.addWidget(btnLoad)

        btnNext = QPushButton('Next Object', self)
        btnNext.clicked.connect(self.nextObject)
        buttonLayout.addWidget(btnNext)

        btnPre = QPushButton('Previous Object', self)
        btnPre.clicked.connect(self.previousObject)
        buttonLayout.addWidget(btnPre)

        btnYes = QPushButton('Yes', self)
        btnYes.clicked.connect(self.markObjectYes)
        buttonLayout.addWidget(btnYes)

        btnNo = QPushButton('No', self)
        btnNo.clicked.connect(self.markObjectNo)
        buttonLayout.addWidget(btnNo)
        
        btnMerge = QPushButton('Merge', self)
        btnMerge.clicked.connect(self.mergeMaskAndImage)
        buttonLayout.addWidget(btnMerge)

        toggleButton = QPushButton('Show/Hide Mask', self)
        toggleButton.clicked.connect(self.toggleMask)
        buttonLayout.addWidget(toggleButton)
        
        btnSaveInfo = QPushButton('Save', self)
        btnSaveInfo.clicked.connect(self.saveInfo)
        buttonLayout.addWidget(btnSaveInfo)
        
        exitButton = QPushButton('close', self)
        exitButton.clicked.connect(self.close)
        buttonLayout.addWidget(exitButton)

        self.objectLabel = QLabel(self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(30) 
        self.objectLabel.setFont(font)
        self.objectLabel.setStyleSheet("color: black;")
        buttonLayout.addWidget(self.objectLabel)

        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)
        self.setWindowTitle('Image and Mask Viewer')
        self.setGeometry(300, 300, 800, 600)

        self.show()
        
        self.imagePath = ''
        self.maskPath = ''
        self.currentObjectIndex = 0
        self.objects = []
        self.objectState = {}
        
        self.objectState['Number object'] = []
        self.objectState['Object State'] = []
        self.objectState['Note'] = []
    
    def saveInfo(self):
        with open("output.csv", mode='w', newline='', encoding='utf-8-sig') as file:

            writer = csv.DictWriter(file, fieldnames=self.objectState.keys())
            writer.writeheader()
            
            rows = [dict(zip(self.objectState, t)) for t in zip(*self.objectState.values())]
            writer.writerows(rows)
    
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
    
    def markObjectNo(self):
        reason = self.getReason()
        self.insertState("No", reason)

        
    def loadImage(self):
#        self.imagePath, _ = QFileDialog.getOpenFileName(self, 'Open file', '/home', "Image files (*.tiff *.tif)")
#        self.maskPath, _ = QFileDialog.getOpenFileName(self, 'Open file', '/home', "Mask files (*.tiff *.tif)")

        self.imagePath = "mask12.tiff"
        self.maskPath = "bac12.tiff"
        
        self.basePixmap = QPixmap(self.imagePath)
        self.baseItem = QGraphicsPixmapItem(self.basePixmap)
        self.scene.addItem(self.baseItem)
        self.scene.setSceneRect(self.baseItem.boundingRect())
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio) 
        
        self.extractObjects(self.maskPath)
            
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
        self.maskVisible = True
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio) 
        
    def changeMask(self):
        maskClone = np.where(self.maskArray == self.objects[self.currentObjectIndex], self.objects[self.currentObjectIndex], 0)

        outputImage = np.zeros((maskClone.shape[0], maskClone.shape[1], 3), dtype=np.uint8)
        outputImage[maskClone != 0] = [255, 0, 0]
        img = Image.fromarray(outputImage, 'RGB')
        img.save('output_image.tiff')
        self.imageMaskClone = Image.fromarray(outputImage, 'RGB')
        
        if hasattr(self, 'maskItem'):
            self.scene.removeItem(self.maskItem)
            del self.maskItem

        self.maskPixmap = QPixmap('output_image.tiff')
        self.maskItem = QGraphicsPixmapItem(self.maskPixmap)
        self.maskItem.setOpacity(0.5)
        self.scene.addItem(self.maskItem)
        self.maskVisible = True
        
        self.scaleToObject(maskClone)
        self.objectLabel.setText(f"{int(self.objects[self.currentObjectIndex])}")


    def previousObject(self):
        if self.currentObjectIndex > 1:
            self.currentObjectIndex -= 1
        self.changeMask()

    def nextObject(self):
        if self.objects[self.currentObjectIndex] < self.objects[len(self.objects) - 1]:
            self.currentObjectIndex += 1
        self.changeMask()

    def scaleToObject(self, maskClone):
        indices = np.where(maskClone != 0)
        if len(indices[0]) == 0 or len(indices[1]) == 0:
            return
        minRow, maxRow = indices[0].min(), indices[0].max()
        minCol, maxCol = indices[1].min(), indices[1].max()
        boundingRect = QRectF(minCol, minRow, maxCol - minCol, maxRow - minRow)
        self.view.fitInView(boundingRect, Qt.KeepAspectRatio)
        self.view.scale(1/2, 1/2)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    sys.exit(app.exec_())