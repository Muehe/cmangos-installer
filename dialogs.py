from PyQt5.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit

def test():
    dialog = QDialog()
    layout = QFormLayout()
    layout.addRow("asdasda")
    dialog.setLayout(layout)
    dialog.exec_()

class BusyDialog(QDialog):
    def __init__(self, title, text, parent):
        #QDialog.__init__(self)
        super().__init__(parent)
        self.setModal(False)
        self.setWindowTitle(title)
        self.text = QLabel(text, self)
        self.resize(200,100)
        self.raise_()
        self.show()
