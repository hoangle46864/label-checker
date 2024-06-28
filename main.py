import sys
from PyQt5.QtWidgets import QApplication
from image_viewer import ImageViewer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageViewer()
    sys.exit(app.exec_())
