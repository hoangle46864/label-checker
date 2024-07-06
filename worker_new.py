from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
from custom_image_item import CustomImageItem


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    objectImagesReady = pyqtSignal(dict)

    def __init__(self, parent, maskArray, objects, initialOpacity=0.5):
        super().__init__()
        self.parent = parent
        self.maskArray = maskArray
        self.objects = objects
        self.initialOpacity = initialOpacity

    def generate_unique_color(self, index):
        np.random.seed(index)
        return np.random.randint(0, 255, size=3)

    def run(self):
        height, width = self.maskArray.shape
        self.objectImages = {}

        for i, obj in enumerate(self.objects):
            maskClone = np.where(self.maskArray == obj, 255, 0).astype(np.uint8)
            color = self.generate_unique_color(i)
            coloredMask = np.zeros((height, width, 4), dtype=np.uint8)
            coloredMask[maskClone == 255] = [color[0], color[1], color[2], 255]  # Use full opacity for color channel

            # Create the CustomImageItem for this object
            objImage = CustomImageItem(parent=self.parent, image=coloredMask, mask=maskClone)
            objImage.setOpacity(self.initialOpacity)
            objImage.setVisible(True)
            self.objectImages[obj] = objImage

            self.progress.emit(int((i + 1) / len(self.objects) * 100))

        self.objectImagesReady.emit(self.objectImages)
        self.finished.emit()
