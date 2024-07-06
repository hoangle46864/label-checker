from image_viewer import ImageViewer
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication([])
    window = ImageViewer()
    window.show()
    app.exec_()