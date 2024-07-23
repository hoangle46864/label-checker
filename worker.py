from __future__ import annotations

import numpy as np
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal


class Worker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, maskArray, objects, parent=None):
        super().__init__(parent)
        if maskArray is None or objects is None:
            raise ValueError("Mask array and objects cannot be None")
        self.maskArray = maskArray
        self.objects = objects
        self.objectColors = {}
        self.maskImageArray = None

    def run(self):
        height, width = self.maskArray.shape

        unique_labels = np.unique(self.maskArray).astype(int)
        unique_labels = unique_labels[unique_labels != 0]  # Remove background label 0

        if unique_labels.size == 0:
            # Return a blank RGBA image if there are no unique labels
            self.maskImageArray = np.zeros((height, width, 4), dtype=np.uint8)
        else:
            # Generate random colors for each unique label
            max_label = int(unique_labels.max())  # Convert to integer
            colors = np.random.randint(0, 256, size=(max_label + 1, 3), dtype=np.uint8)

            # Ensure the background (label 0) is black
            colors[0] = [0, 0, 0]

            # Store the color for each object from the colors array
            for i, obj in enumerate(self.objects):
                obj = int(obj)
                self.objectColors[obj] = colors[obj]
                self.progress.emit(int((i + 1) / len(self.objects) * 100))

            alpha_channel = np.full((colors.shape[0], 1), 128, dtype=np.uint8)
            alpha_channel[0] = 0
            color_map = np.concatenate((colors, alpha_channel), axis=1)

            # Create a color-mapped image
            self.maskImageArray = color_map[self.maskArray.astype(int)]

        maskImage = Image.fromarray(self.maskImageArray, "RGBA")
        maskImage.save("all_objects_with_low_opacity.tiff")

        self.finished.emit()
