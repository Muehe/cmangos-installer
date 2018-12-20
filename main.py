#!/usr/bin/python3

"""This file: UI, Launcher

Compatible with Py3.5+

Required libraries:
  - Python-MySQLClient
  - PyQt5
"""

# TODO:
# - Replace os / sys with pathlib where appropriate.
# - Decide if PyMySQL is okay or maybe MySQL-Connector-Python is better suits things. Don't rush that one.
# - Cleanup styling, naming.
# - Figure out Qt parts of it.
# - Will it be beneficial to move UI layout in .ui file and loading it?
# - Reorder class methods.
# - Maybe our modules can be imported in a more verbose way?
# - Get rid of unfinished code, explain credientals popup.

# Standard libs
import os
import sys
import subprocess

# Foreign libs
import MySQLdb as mysql

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QVBoxLayout, QGridLayout, QPushButton, QTabWidget, QMessageBox, QDialog
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QObject, pyqtSlot

# Our modules
from status import *
from versionTab import *
from installer import *


DEVNULL = open(os.devnull, 'w')


class Cmangos(QWidget):
    """Produce main window, load it's layout', bind handlers."""

    def __init__(self):
        super().__init__()
        self.__getLogin()
        self.status = Status(self)
        self.installer = Installer('')
        self.mainLayout = QGridLayout()

        self.statusTexts = {
            'mysql_client': 'MySQL client found',
            'mysql_server': 'MySQL server found',
            'mysql_running': 'MySQL server status',
            'mysql_connection': 'MySQL user login',
        }

        self.setWindowTitle('CMaNGOS Control Center')
        self.setWindowIcon(QIcon('cmangos.ico'))

        self.__initUI()

    def __getLogin(self):
    """Ask user for credientals to DB."""

        dialog = QDialog(self)
        layout = QFormLayout()
        layout.addRow(QLabel('User:'))

        try:
            getattr(self, 'user')
            name = self.user
        except:
            name = 'mangos'

        user = QLineEdit(name)
        layout.addRow(user)
        layout.addRow(QLabel('Password:'))

        try:
            getattr(self, 'pw')
            p = self.pw
        except:
            p = 'mangos'

        pw = QLineEdit(p)
        pw.setEchoMode(QLineEdit.Password)
        layout.addRow(pw)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        layout.addRow(buttonBox)

        dialog.setLayout(layout)

        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        dialog.setWindowTitle('MySQL')
        dialog.move(self.pos())

        if(dialog.exec_()):
            self.user = user.text()
            self.pw = pw.text()
        else:
            self.user = name
            self.pw = p

    def __update(self):
        stat = self.status
        stat.update()
        labels = self.statusLabels
        texts = self.statusTexts

        for label in labels:
            labels[label].setText(
                ('☑ ' if stat.stats[label] else '☐ ')
                +
                (label if label not in texts else texts[label])
            )

        if not stat.stats['mysql_connection']:
            self.createButton.show()
        else:
            self.createButton.hide()

        try:
            for tab in self.tabWidgets:
                tab.update()
        except:
            return

    def __initStatusLabel(self, status):
        f = QFont('DejaVu Sans Mono', 10)
        self.statusLabels[status] = QLabel('')
        self.statusLabels[status].setFont(f)
        self.statusLayout.addWidget(self.statusLabels[status])

    @pyqtSlot(int)
    def currentChangedTab(self, index):
        self.tabStatus.setCurrentIndex(index)

    @pyqtSlot(int)
    def currentChangedStatus(self, index):
        self.tabs.setCurrentIndex(index)

    def __create(self):
        """Handle <Create User> button event."""

        if self.user == None or self.pw == None:
            return

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
            self.setWindowTitle('Creatin user... ')
            self.setDisabled(True)
            self.blockSignals(True)
            QApplication.processEvents()

            try:
                self.installer.createUser(root.text(), self.user, self.pw)
                msg = QMessageBox()
                msg.setText('User `{}` successfully created.'.format(self.user))
                msg.exec_()
                self.createButton.hide()
                self.__update()
            except:
                msg = QMessageBox()
                msg.setText('Failed creating user `{}`.'.format(self.user))
                msg.exec_()

                self.blockSignals(False)
            self.setEnabled(True)
            self.setWindowTitle('CMangos Control Center')

    def __resetLogin(self):
        self.__getLogin()
        self.__update()

    def __initUI(self):
        """Load layout, set size, bind event handlers, show the window."""

        self.statusBox = QGroupBox('MySQL status', self)
        self.statusLabels = {}
        self.statusLayout = QVBoxLayout()

        for label in self.statusTexts:
            self.__initStatusLabel(label)

        # Update Event
        btn = QPushButton('🔄 Refresh')
        btn.clicked.connect(self.__update)
        self.statusLayout.addWidget(btn)

        # Reset Login Event
        btn = QPushButton('Set User Login')
        btn.clicked.connect(self.__resetLogin)
        self.statusLayout.addWidget(btn)

        # Create User Event
        self.createButton = QPushButton('Create User')
        self.createButton.clicked.connect(self.__create)
        self.statusLayout.addWidget(self.createButton)

        self.statusBox.setLayout(self.statusLayout)
        self.__update()

        self.tabs = QTabWidget()
        self.tabWidgets = []
        self.tabWidgets.append(VersionTab('classic', self))
        self.tabWidgets.append(VersionTab('tbc', self))
        self.tabWidgets.append(VersionTab('wotlk', self))
        self.tabs.addTab(self.tabWidgets[0], 'Classic')
        self.tabs.addTab(self.tabWidgets[1], 'TBC')
        self.tabs.addTab(self.tabWidgets[2], 'WotLK')

        self.tabStatus = QTabWidget()
        self.tabStatus.addTab(self.tabWidgets[0].statusTab, 'Classic')
        self.tabStatus.addTab(self.tabWidgets[1].statusTab, 'TBC')
        self.tabStatus.addTab(self.tabWidgets[2].statusTab, 'WotLK')
        self.tabStatus.tabBar().hide()
        self.tabStatus.setDocumentMode(True)

        # Change Tab Event
        self.tabs.currentChanged.connect(self.currentChangedTab)
        self.tabStatus.currentChanged.connect(self.currentChangedStatus)

        self.mainLayout.addWidget(self.statusBox, 0, 0)
        self.mainLayout.addWidget(self.tabs, 1, 0)
        self.mainLayout.addWidget(self.tabStatus, 0, 1, 0, 2)
        self.setLayout(self.mainLayout)

        self.setFixedSize(self.mainLayout.sizeHint())
        self.show()


# C-like execution model and avoid letting others to load us as a module.
if __name__ == '__main__':
    app = QApplication(sys.argv)

    if sys.platform != 'linux':
        box = QMessageBox()
        box.setText('Warning: This program has only been tested on Linux!')
        box.exec_()

    w = Cmangos()
    sys.exit(app.exec_())
