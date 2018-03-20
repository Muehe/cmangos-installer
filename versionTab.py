from PyQt5.QtWidgets import QApplication, qApp, QWidget, QVBoxLayout, QLabel, QGroupBox, QPushButton, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

from versionStatus import *
from installer import *
from dialogs import *

from os import makedirs, getcwd, chdir
from os.path import exists
from subprocess import *
from signal import *

class VersionTab(QWidget):
    def __init__(self, version, parent):
        super().__init__()
        self.version = version
        self.parent = parent
        self.status = VersionStatus(version, parent)

        self.statusTab = QGroupBox('{} status'.format(version))
        self.statusTab.layout = QVBoxLayout()
        self.statusTab.labels = {}
        for label in self.status.directories:
            self.statusTab.labels[label] = QLabel('')
            self.statusTab.layout.addWidget(self.statusTab.labels[label])
            if label == 'server':
                self.statusTab.labels['server_install'] = QLabel('')
                self.statusTab.layout.addWidget(self.statusTab.labels['server_install'])
                self.statusTab.labels['server_config'] = QLabel('')
                self.statusTab.layout.addWidget(self.statusTab.labels['server_config'])
                self.statusTab.labels['server_maps'] = QLabel('')
                self.statusTab.layout.addWidget(self.statusTab.labels['server_maps'])
            if label == '{}-db/.git'.format(self.version):
                for db in self.status.database:
                    self.statusTab.labels[db] = QLabel('')
                    self.statusTab.layout.addWidget(self.statusTab.labels[db])
        self.__updateStatusPage()
        self.statusTab.setLayout(self.statusTab.layout)

        self.installer = Installer(version)
        self.tabLayout = QVBoxLayout()
        self.buttons = {}
        self.buttons['client'] = self.__createButton('Copy Client', 'Specify a directory to copy the client from.')
        self.buttons['client'].clicked.connect(self.__client)
        self.buttons['server'] = self.__createButton('Install Server', 'Clone and compile the core, then apply config options.')
        self.buttons['server'].clicked.connect(self.__server)
        self.buttons['database'] = self.__createButton('Install Database', 'Clone and install the Database. Grant rights to currently set user.')
        self.buttons['database'].clicked.connect(self.__databaseInstall)
        self.buttons['maps'] = self.__createButton('Copy Map Files', 'Specify a directory to copy pre-existing map files from.')
        self.buttons['maps'].clicked.connect(self.__maps)
        self.buttons['mmaps'] = self.__createButton('Create Map Files', 'Extract map information from the client.')
        self.buttons['mmaps'].clicked.connect(self.__extract)
        self.buttons['server_start'] = self.__createButton('Start server', 'Start the mangos and realm daemons.')
        self.buttons['server_start'].clicked.connect(self.__serverStart)
        self.buttons['server_stop'] = self.__createButton('Stop server', 'Stop the mangos and realm daemons.')
        self.buttons['server_stop'].clicked.connect(self.__serverStop)
        self.buttons['recompile'] = self.__createButton('Re-compile Core', 'Re-compile the {} core from the currently checked out commit.'.format(self.version))
        self.buttons['recompile'].clicked.connect(self.__compile)
        self.buttons['reinstall'] = self.__createButton('Re-install Database', 'Re-install the {} database from the currently checked out commit.'.format(self.version))
        self.buttons['reinstall'].clicked.connect(self.__databaseUpdate)
        self.buttons['config'] = self.__createButton('Re-apply Server Config', 'Re-apply the currently set user and password to the config files.')
        self.buttons['config'].clicked.connect(self.__config)
        self.buttons['remap'] = self.__createButton('Recreate Map Files', 'Run a new map extraction and replace current files.')
        self.buttons['remap'].clicked.connect(self.__extract)
        self.tabLayout.setAlignment(Qt.AlignTop)
        self.__updateButtons()
        self.setLayout(self.tabLayout)

    def __extract(self):
        self.__deactivateWindow('Extracting maps. Please wait...')
        success = self.installer.extractMaps()
        if success:
            self.__reactivateWindow('Extracting maps finished.')
        else:
            self.__reactivateWindow('Error! Extracting maps failed.')
        self.update()

    def __serverStart(self):
        startPath = getcwd()
        serverPath = '{}/server/bin'.format(self.version)
        chdir(serverPath)
        self.mangosd = Popen(['./mangosd', '-c', '../etc/mangosd.conf'], stdin=PIPE)
        if self.mangosd.poll() != None:
            self.mangosd = None
            chdir(startPath)
            return
        self.realmd = Popen(['./realmd', '-c', '../etc/realmd.conf'])
        if self.mangosd.poll() != None:
            self.mangosd = None
        chdir(startPath)
        self.update()

    def __serverStop(self):
        self.mangosd.communicate(b'server shutdown 1')
        print('mangosd exited with: {}'.format(self.mangosd.wait()))
        self.mangosd = None
        self.realmd.send_signal(SIGINT)
        print('realmd exited with: {}'.format(self.realmd.wait()))
        self.realmd = None
        self.update()

    def __compile(self):
        self.__deactivateWindow('Compiling core. Please wait...')
        success = self.installer.compileCore()
        if success:
            self.__reactivateWindow('Finished compiling {} core successfully.'.format(self.version))
        else:
            self.__reactivateWindow('Error! Failed compiling {} core.'.format(self.version))
        self.update()

    def __config(self):
        self.installer.applyCoreConfig(self.parent.user, self.parent.pw)
        self.installer.applyRealmConfig(self.parent.user, self.parent.pw)
        self.update()

    def __client(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        path = dialog.getExistingDirectory(self, '{} client source path'.format(self.version))
        if (path == ''):
            return
        self.parent.setWindowTitle('Copying. Please wait...')
        self.parent.setDisabled(True)
        self.parent.blockSignals(True)
        self.__deactivateWindow('Copying client. Please wait...')
        QApplication.processEvents()
        success = self.installer.copyClient(path)
        if success:
            self.__reactivateWindow('Finished copying {} client successfully.'.format(self.version))
        else:
            self.__reactivateWindow('Error! Failed copying {} client.'.format(self.version))
        self.parent.blockSignals(False)
        self.parent.setEnabled(True)
        self.parent.setWindowTitle('CMangos Control Center')
        self.update()

    def __maps(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        path = dialog.getExistingDirectory(self, '{} dbc/maps/vmaps/mmaps path'.format(self.version))
        if (path == ''):
            return
        self.__deactivateWindow('Copying maps. Please wait...')
        success = self.installer.copyMaps(path)
        if success:
            self.__reactivateWindow('Finished copying {} mapfiles successfully.'.format(self.version))
        else:
            self.__reactivateWindow('Error! Failed copying {} mapfiles.'.format(self.version))
        self.update()

    def __server(self):
        self.__deactivateWindow('Installing core. Please wait...'.format(self.version))
        self.installer.cloneCore()
        success = self.installer.compileCore()
        self.__config()
        if success:
            self.__reactivateWindow('Finished installing {} core successfully.'.format(self.version))
        else:
            self.__reactivateWindow('Error! Failed installing {} core.'.format(self.version))

    def __databaseInstall(self):
        dialog = QDialog(self.parent)
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
            self.__deactivateWindow('Installing {} database'.format(self.version))
            self.installer.cloneDB()
            self.installer.dbSetup(root.text(), self.parent.user, self.parent.pw)
            success = self.installer.dbInstall(self.parent.user, self.parent.pw)
            if success:
                self.__reactivateWindow('{} database installed successfully.'.format(self.version))
            else:
                self.__reactivateWindow('Error! {} database installed failed.'.format(self.version))
        self.update()

    def __databaseUpdate(self):
        if not self.status.directories['{}-db'.format(self.version)] or not self.status.connection or not self.status.database['mangos'] or not  self.status.database['realmd'] or not  self.status.database['characters']:
            return
        self.__deactivateWindow('Updating database. Please wait...'.format(self.version))
        success = self.installer.dbUpdate(self.parent.user, self.parent.pw)
        if success:
            self.__reactivateWindow('{} database updated successfully.'.format(self.version))
        else:
            self.__reactivateWindow('Error! {} database update failed.'.format(self.version))
        self.update()

    def __getStatusChar(self, value):
        if self.status.directories[value]:
            return '☑'
        else:
            return '☐'

    def __updateLabel(self, label, text):
        char = self.__getStatusChar(label)
        self.statusTab.labels[label].setText(text.format(char))

    def __updateServerLabel(self, label, text):
        labels = {
            'server_install': 'server',
            'server_config': 'config',
            'server_maps': 'maps',
        }
        if self.status.install[labels[label]]:
            char = '☑'
        else:
            char = '☐'
        self.statusTab.labels[label].setText(text.format(char))

    def __updateDBLabel(self, label, text):
        if self.status.database[label]:
            char = '☑'
        else:
            char = '☐'
        self.statusTab.labels[label].setText(text.format(char))

    def __createButton(self, label, tooltip=None):
        btn = QPushButton(label)
        if tooltip:
            btn.setToolTip(tooltip)
        self.tabLayout.addWidget(btn)
        return btn

    def __updateButtons(self):
        if not (self.status.install['maps'] and self.status.directories['client']):
            self.buttons['remap'].hide()
        else:
            self.buttons['remap'].show()
        if not (self.status.install['maps'] and self.status.install['mmaps']):
            self.buttons['maps'].show()
            self.buttons['mmaps'].show()
            if not self.status.directories['client']:
                self.buttons['mmaps'].setEnabled(False)
                self.buttons['mmaps'].setToolTip('Client directory needed for map extraction.')
            else:
                self.buttons['mmaps'].setEnabled(True)
                self.buttons['mmaps'].setToolTip('Extract map information from the client.')
            if not self.status.install['server']:
                self.buttons['mmaps'].setEnabled(False)
                self.buttons['mmaps'].setToolTip('Installed server needed for map extraction.')
                self.buttons['maps'].setEnabled(False)
                self.buttons['maps'].setToolTip('Installed server needed for copying maps.')
            else:
                if self.status.directories['client']:
                    self.buttons['mmaps'].setEnabled(True)
                    self.buttons['mmaps'].setToolTip('Extract map information from the client.')
                self.buttons['maps'].setEnabled(True)
                self.buttons['maps'].setToolTip('Specify a directory to copy pre-existing map files from.')
        else:
            self.buttons['maps'].hide()
            self.buttons['mmaps'].hide()
        if not self.status.directories['client']:
            self.buttons['client'].show()
        else:
            self.buttons['client'].hide()
        if not self.status.install['server']:
            self.buttons['server'].show()
            self.buttons['recompile'].hide()
            if self.status.directories['mangos-{}/.git'.format(self.version)]:
                self.buttons['server'].setEnabled(False)
                self.buttons['server'].setToolTip('Git files exist but server is not installed.\nTry deleting the {}/mangos-{} directory.'.format(self.version, self.version))
            else:
                self.buttons['server'].setEnabled(True)
                self.buttons['server'].setToolTip('Clone and compile the core, then apply config options.')
        else:
            self.buttons['server'].hide()
            self.buttons['recompile'].show()
        if self.status.install['server'] and self.status.install['config']:
            self.buttons['config'].show()
        else:
            self.buttons['config'].hide()
        if not self.status.database['mangos'] or not  self.status.database['realmd'] or not  self.status.database['characters']:
            self.buttons['database'].show()
            self.buttons['reinstall'].hide()
        else:
            self.buttons['database'].hide()
            self.buttons['reinstall'].show()
        if self.status.install['server'] and self.status.install['config'] and self.status.install['maps'] and self.status.database['mangos'] and self.status.database['realmd'] and self.status.database['characters']:
            try:
                if self.mangosd != None and self.realmd != None:
                    self.buttons['server_stop'].show()
                    self.buttons['server_start'].hide()
                else:
                    self.buttons['server_stop'].hide()
                    self.buttons['server_start'].show()
            except:
                self.buttons['server_stop'].hide()
                self.buttons['server_start'].show()
        else:
            self.buttons['server_stop'].hide()
            self.buttons['server_start'].hide()

    def __updateStatusPage(self):
        self.__updateLabel(self.version, '{} base directory')
        self.__updateLabel('build', '    {} build directory')
        self.__updateLabel('client', '    {} client directory')
        self.__updateLabel('server', '    {} server directory')
        self.__updateServerLabel('server_install', '        {} binaries')
        self.__updateServerLabel('server_config', '        {} config files')
        self.__updateServerLabel('server_maps', '        {} map files')
        self.__updateLabel('mangos-{}'.format(self.version), '    {} core directory')
        self.__updateLabel('mangos-{}/.git'.format(self.version), '        {} core git files')
        self.__updateLabel('{}-db'.format(self.version), '    {} db directory')
        self.__updateLabel('{}-db/.git'.format(self.version), '        {} db git files')
        self.__updateDBLabel('mangos', '        {} mangos db')
        self.__updateDBLabel('realmd', '        {} realmd db')
        self.__updateDBLabel('characters', '        {} characters db')

    def update(self):
        self.status.update()
        self.__updateStatusPage()
        self.__updateButtons()

    def __deactivateWindow(self, message):
        self.parent.setWindowTitle(message)
        self.parent.setDisabled(True)
        self.parent.blockSignals(True)
        QApplication.processEvents()

    def __reactivateWindow(self, message):
        self.parent.blockSignals(False)
        self.parent.setEnabled(True)
        self.parent.setWindowTitle('CMangos Control Center')
        msg = QMessageBox(self.parent)
        msg.setText(message)
        msg.exec_()
