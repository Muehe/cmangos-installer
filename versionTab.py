from PyQt5.QtWidgets import QApplication, qApp, QWidget, QVBoxLayout, QLabel, QGroupBox, QPushButton, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from time import sleep

from versionStatus import *
from installer import *
from dialogs import *

from os import makedirs
from os.path import exists

class VersionTab(QWidget):
    def __init__(self, version, user, pw, parent):
        super().__init__()
        self.version = version
        self.user = user
        self.pw = pw
        self. parent = parent
        self.status = VersionStatus(version)

        self.statusTab = QGroupBox()
        self.statusTab.layout = QVBoxLayout()
        self.statusTab.labels = {}
        for label in self.status.directories:
            self.statusTab.labels[label] = QLabel('')
            self.statusTab.layout.addWidget(self.statusTab.labels[label])
        self.statusTab.setLayout(self.statusTab.layout)
        self.__updateStatusPage()

        self.installer = Installer(version, user, pw)
        self.tabLayout = QVBoxLayout()
        self.buttons = {}
        """
        btn = QPushButton('Create base dir')
        btn.clicked.connect(self.__createBaseDir)
        self.buttons['base'] = btn
        if not exists(self.version):
            self.tabLayout.addWidget(btn)
        """
        btn = QPushButton('Copy Client')
        btn.clicked.connect(self.__client)
        btn.setToolTip('Specify a directory to copy the client from.')
        self.buttons['client'] = btn
        if not self.status.directories['client']:
            self.tabLayout.addWidget(btn)
        btn = QPushButton('Install Server')
        btn.clicked.connect(self.__server)
        btn.setToolTip('Clone and compile the core, then apply config options.')
        self.buttons['server'] = btn
        if not self.status.install['server']:
            self.tabLayout.addWidget(btn)
        btn = QPushButton('Apply Config')
        btn.clicked.connect(self.__client)
        self.buttons['config'] = btn
        if self.status.install['server'] and not self.status.install['config']:
            self.tabLayout.addWidget(btn)
        btn = QPushButton('Copy Map Files')
        btn.clicked.connect(self.__client)
        self.buttons['maps'] = btn
        if not self.status.install['maps'] or not self.status.install['mmaps']:
            self.tabLayout.addWidget(btn)
        btn = QPushButton('Create Map Files')
        btn.clicked.connect(self.__database)
        self.buttons['mmaps'] = btn
        if not self.status.install['maps'] or not self.status.install['mmaps']:
            self.tabLayout.addWidget(btn)
            if not self.status.directories['client']:
                btn.setEnabled(False)
                btn.setToolTip('Client directory needed.')
        #for button in self.buttons:
            #self.tabLayout.addWidget(self.buttons[button])
        self.tabLayout.setAlignment(Qt.AlignTop)
        self.setLayout(self.tabLayout)

    def __client(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        path = dialog.getExistingDirectory(self, '{} client source path'.format(self.version))
        if (path == ''):
            return
        #msg = QDialog(self.parent)
        #layout = QVBoxLayout()
        #layout.addWidget(QLabel('The {} client is being copied.\n\nPlease wait...'.format(self.version)))
        #msg.setLayout(layout)
        #msg.setWindowTitle('Copying')
        #msg.setText('{} client is being copied...'.format(self.version))
        #msg.setWindowModality(Qt.NonModal)
        #msg.setStandardButtons(QMessageBox.NoButton)
        #msg.resize(200,100)
        #msg.show()
        #qApp.processEvents()
        #msg = BusyDialog('test', '12345', self)
        #msg.exec_()
        self.parent.setWindowTitle('Copying. Please wait...')
        self.parent.setDisabled(True)
        self.parent.blockSignals(True)
        QApplication.processEvents()
        sleep(5)
        #self.installer.copyClient(path)
        self.parent.blockSignals(False)
        self.parent.setEnabled(True)
        self.parent.setWindowTitle('CMangos Control Center')
        #msg.close()

    def __server(self):
        self.installer.cloneCore()
        self.installer.compileCore()
        self.installer.applyCoreConfig(self.user, self.pw)
        self.installer.applyRealmConfig(self.user, self.pw)

    def __database(self):
        dialog = QDialog(self)
        layout = QFormLayout()
        layout.addRow(QLabel('MySQL Root Password:'))
        root = QLineEdit('')
        root.setEchoMode(QLineEdit.Password)
        layout.addRow(root)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        layout.addRow(buttonBox)
        dialog.setLayout(layout)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        if(dialog.exec_()):
            print(root.text())

    def __getStatusChar(self, value):
        if self.status.directories[value]:
            return '☑'
        else:
            return '☐'

    def __updateLabel(self, label, text):
        char = self.__getStatusChar(label)
        self.statusTab.labels[label].setText(text.format(char))

    def __updateStatusPage(self):
        self.status.update()
        labels = self.statusTab.labels
        self.__updateLabel(self.version, '{} base directory')
        self.__updateLabel('build', '    {} build directory')
        self.__updateLabel('client', '    {} client directory')
        self.__updateLabel('server', '    {} server directory')
        self.__updateLabel('mangos-{}'.format(self.version), '    {} core directory')
        self.__updateLabel('mangos-{}/.git'.format(self.version), '        {} core git files')
        self.__updateLabel('{}-db'.format(self.version), '    {} db directory')
        self.__updateLabel('{}-db/.git'.format(self.version), '        {} db git files')
