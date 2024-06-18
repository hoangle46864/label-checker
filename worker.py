from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
from PIL import Image


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, maskArray, objects):
        super().__init__()
        self.maskArray = maskArray
        self.objects = objects
        self.objectColors = {}

    def run(self):
        height, width = self.maskArray.shape
        self.maskImageArray = np.zeros((height, width, 4), dtype=np.uint8)

        for i, obj in enumerate(self.objects):
            color = (np.random.randint(256), np.random.randint(256), np.random.randint(256))
            self.objectColors[obj] = color
            self.maskImageArray[self.maskArray == obj] = (*color, 128)  # RGBA with low opacity
            self.progress.emit(int((i + 1) / len(self.objects) * 100))

        maskImage = Image.fromarray(self.maskImageArray, "RGBA")
        maskImage.save("all_objects_with_low_opacity.tiff")

        self.finished.emit()
