import sys
from PyQt5.QtWidgets import QApplication
import pyqtgraph
from image_viewer import ImageViewer

pyqtgraph.setConfigOption('imageAxisOrder', 'row-major')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageViewer()
    ex.show()
    ex.imageView.setFocus()
    sys.exit(app.exec_())
