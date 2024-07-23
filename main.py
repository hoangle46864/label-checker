from __future__ import annotations

from PyQt5.QtWidgets import QApplication

from image_viewer import ImageViewer

if __name__ == "__main__":
    app = QApplication([])
    window = ImageViewer()
    window.show()
    app.exec_()
