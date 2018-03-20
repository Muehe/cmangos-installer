from os.path import isfile, isdir
from os import devnull
from subprocess import run
import MySQLdb as mysql

DEVNULL = open(devnull, 'w')

class VersionStatus():
    def __init__(self, version, parent):
        self.version = version
        self.parent = parent
        self.repoStr = 'mangos-{}'.format(self.version)
        self.dbStr = '{}-db'.format(self.version)
        self.directories = {}
        self.install = {}
        self.database = {}
        self.update()

    def update(self):
        self.__checkDirectories()
        self.__checkInstall()
        self.__checkDatabase()

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
        #print(self.install)

    def __checkDatabase(self):
        try:
            con = mysql.connect('localhost', self.parent.user, self.parent.pw)
            cur = con.cursor()
            self.connection = True
        except:
            self.connection = False
        if not self.connection:
            self.database['mangos'] = False
            self.database['realmd'] = False
            self.database['characters'] = False
            return
        if cur.execute('SHOW DATABASES LIKE \'{}-mangos\''.format(self.version)) == 0:
            self.database['mangos'] = False
        else:
            self.database['mangos'] = True
        if cur.execute('SHOW DATABASES LIKE \'{}-realmd\''.format(self.version)) == 0:
            self.database['realmd'] = False
        else:
            self.database['realmd'] = True
        if cur.execute('SHOW DATABASES LIKE \'{}-characters\''.format(self.version)) == 0:
            self.database['characters'] = False
        else:
            self.database['characters'] = True
        con.close()
        return

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
        #print(self.directories)
        #TODO git synched
        #TODO git branch
        #TODO DB status
