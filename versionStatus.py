from os.path import isfile, isdir
from os import devnull
from subprocess import run
import MySQLdb as mysql

DEVNULL = open(devnull, 'w')

class VersionStatus():
    def __init__(self, version):
        self.version = version
        self.repoStr = 'mangos-{}'.format(self.version)
        self.dbStr = '{}-db'.format(self.version)
        self.directories = {}
        self.install = {}
        self.update()

    def update(self):
        self.__checkDirectories()
        self.__checkInstall()

    def __checkInstall(self):
        if isfile('{}/server/bin/mangosd'.format(self.version)) and isfile('{}/server/bin/realmd'.format(self.version)):
            self.install['server'] = True
        else:
            self.install['server'] = False
        if isfile('{}/server/etc/mangosd.conf'.format(self.version)) and isfile('{}/server/etc/realmd.conf'.format(self.version)):
            self.install['config'] = True
        else:
            self.install['config'] = False
        if isdir('{}/server/bin/dbc'.format(self.version)) and isdir('{}/server/bin/maps'.format(self.version)) and isdir('{}/server/bin/vmaps'.format(self.version)):
            self.install['maps'] = True
        else:
            self.install['maps'] = False
        if isdir('{}/server/bin/mmaps'.format(self.version)):
            self.install['mmaps'] = True
        else:
            self.install['mmaps'] = False
        print(self.install)

    def __checkDirectories(self):
        dirs = [
            self.version,
            'build',
            'client',
            'server',
            self.repoStr,
            '{}/.git'.format(self.repoStr),
            self.dbStr,
            '{}/.git'.format(self.dbStr),
        ]
        for dir in dirs:
            if isdir('{}/{}'.format(self.version, dir)):
                self.directories[dir] = True
            else:
                self.directories[dir] = False
        if isdir(self.version):
            self.directories[self.version] = True
        print(self.directories)
        #TODO git repositories
        #TODO git synched
        #TODO git branch
        #TODO config files
        #TODO DB status
        #TODO server status
