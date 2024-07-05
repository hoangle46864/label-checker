from PyQt5.QtWidgets import QLineEdit, QDialog, QFormLayout, QPushButton, QVBoxLayout
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

class KeySequenceEdit(QLineEdit):
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Backspace:
            self.clear()
        elif key == Qt.Key_Escape:
            self.setText("")
        else:
            mod = int(event.modifiers())
            keySequence = QKeySequence(mod | key)
            self.setText(keySequence.toString())
        event.accept()
        
class EditHotkeysDialog(QDialog):
    def __init__(self, hotkeys, parent=None):
        super().__init__(parent)
        self.hotkeys = hotkeys
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Edit Hotkeys")
        layout = QVBoxLayout()
        self.formLayout = QFormLayout()

        self.inputs = {}
        for key, value in self.hotkeys.items():
            self.inputs[key] = KeySequenceEdit()
            self.inputs[key].setText(QKeySequence(value).toString())
            self.formLayout.addRow(f"{key}:", self.inputs[key])

        layout.addLayout(self.formLayout)
        saveBtn = QPushButton("Save", self)
        saveBtn.clicked.connect(self.saveHotkeys)
        layout.addWidget(saveBtn)

        self.setLayout(layout)

    def saveHotkeys(self):
        for key, line_edit in self.inputs.items():
            keySequence = QKeySequence(line_edit.text())
            if keySequence.count() > 0:
                self.hotkeys[key] = keySequence[0]
            else:
                self.hotkeys[key] = None
        self.accept()