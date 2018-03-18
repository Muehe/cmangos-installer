#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import MySQLdb as mysql

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QVBoxLayout, QGridLayout, QPushButton, QTabWidget, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QObject, pyqtSlot


from status import *
from versionTab import *

DEVNULL = open(os.devnull, 'w')

class Cmangos(QWidget):
    def __init__(self):
        super().__init__()
        self.status = Status()
        self.mainLayout = QGridLayout()
        self.statusTexts = {
            'mysql_client': 'MySQL client found',
            'mysql_server': 'MySQL server found',
            'mysql_running': 'MySQL server status',
        }
        self.move(2220,300) # TODO Sane value on first screen
        self.setWindowTitle('CMaNGOS Control Center')
        self.__getLogin()
        self.__initUI()

    def __getLogin(self):
        dialog = QDialog(self)
        layout = QFormLayout()
        layout.addRow(QLabel('User:'))
        user = QLineEdit('mangos')
        layout.addRow(user)
        layout.addRow(QLabel('Password:'))
        pw = QLineEdit('mangos')
        pw.setEchoMode(QLineEdit.Password)
        layout.addRow(pw)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        layout.addRow(buttonBox)
        dialog.setLayout(layout)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        dialog.setWindowTitle('MySQL')
        if(dialog.exec_()):
            self.user = user
            self.pw = pw

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

    def __initUI(self):
        self.statusBox = QGroupBox('Status', self)
        self.statusLabels = {}
        self.statusLayout = QVBoxLayout()
        for label in self.statusTexts:
            self.__initStatusLabel(label)
        self.__update()
        btn = QPushButton('🔄 Refresh')
        btn.clicked.connect(self.__update)
        self.statusLayout.addWidget(btn)
        self.statusBox.setLayout(self.statusLayout)

        self.tabs = QTabWidget()
        self.tabWidgets = []
        self.tabWidgets.append(VersionTab('classic', self.user, self.pw, self))
        self.tabWidgets.append(VersionTab('tbc', self.user, self.pw, self))
        self.tabWidgets.append(VersionTab('wotlk', self.user, self.pw, self))
        self.tabs.addTab(self.tabWidgets[0], 'Classic')
        self.tabs.addTab(self.tabWidgets[1], 'TBC')
        self.tabs.addTab(self.tabWidgets[2], 'WotLK')
        self.tabStatus = QTabWidget()
        self.tabStatus.addTab(self.tabWidgets[0].statusTab, 'Classic')
        self.tabStatus.addTab(self.tabWidgets[1].statusTab, 'TBC')
        self.tabStatus.addTab(self.tabWidgets[2].statusTab, 'WotLK')
        self.tabStatus.tabBar().hide()
        self.tabStatus.setDocumentMode(True)

        self.tabs.currentChanged.connect(self.currentChangedTab)
        self.tabStatus.currentChanged.connect(self.currentChangedStatus)

        self.mainLayout.addWidget(self.statusBox, 0, 0)
        self.mainLayout.addWidget(self.tabs, 0, 1, 0, 2)
        self.mainLayout.addWidget(self.tabStatus, 1, 0)
        self.setLayout(self.mainLayout)

        self.setFixedSize(self.mainLayout.sizeHint())
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform != 'linux':
        box = QMessageBox()
        box.setText('Warning: This program has only been tested on Linux!')
        box.exec_()
    w = Cmangos()
    sys.exit(app.exec_())
