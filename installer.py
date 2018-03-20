from subprocess import run, Popen, PIPE
from multiprocessing import cpu_count
from os import devnull, chdir, getcwd, makedirs, stat, chmod, remove
from os.path import isfile, isdir
from re import sub
from shutil import copytree, rmtree, copy2, move
#from _mysql import connect
import MySQLdb as mysql

DEVNULL = open(devnull, 'w')

class Installer():
    def __init__(self, version):
        self.version = version
    def copyClient(self, path):
        target = '{}/client'.format(self.version)
        if isdir(target):
            print('{} client dir already exists. aborting'.format(self.version))
            return False
        copytree(path, target)
        print('{} client copied'.format(self.version))
        return True

    def copyMaps(self, path, mmaps=True):
        dirs = ['dbc','maps','vmaps']
        if mmaps:
            dirs.append('mmaps')
        for dir in dirs:
            if isdir('{}/server/bin/{}'.format(self.version,dir)):
                print('{} {} target dir already exists. aborting'.format(self.version,dir))
                return False
            if not isdir('{}/{}'.format(path,dir)):
                print('{} {} source dir does not exist. aborting'.format(self.version,dir))
                return False
        for dir in dirs:
            copytree('{}/{}'.format(path,dir), '{}/server/bin/{}'.format(self.version,dir))
        return True

    def cloneCore(self):
        if isdir('{}/mangos-{}'.format(self.version,self.version)):
            print('{} core target directory exists. aborting'.format(self.version))
            return False
        r = run(['git', 'clone', 'https://github.com/cmangos/mangos-{}.git'.format(self.version), '{}/mangos-{}'.format(self.version,self.version)], stdout=DEVNULL)
        if r.returncode == 0:
            print('{} core cloned'.format(self.version))
            return True
        print('error during cloning of {} core '.format(self.version))
        return False

    def cloneDB(self):
        if isdir('{}/{}-db'.format(self.version,self.version)):
            print('{} db target directory exists. aborting'.format(self.version))
            return False
        r = run(['git', 'clone', 'https://github.com/cmangos/{}-db.git'.format(self.version), '{}/{}-db'.format(self.version,self.version)], stdout=DEVNULL)
        if r.returncode == 0:
            print('{} db cloned'.format(self.version))
            return True
        print('error during cloning of {} db '.format(self.version))
        return False

    def applyCoreConfig(self, user='mangos', pw='mangos', targetFile='mangosd', log=0, mangos=False, realmd=False, chars=False):
        if not mangos:
            mangos = '{}-mangos'.format(self.version)
        if not realmd:
            realmd = '{}-realmd'.format(self.version)
        if not chars:
            chars = '{}-characters'.format(self.version)
        path = '{}/{}/server/etc'.format(getcwd(), self.version)
        with open('{}/mangosd.conf.dist'.format(path), 'r') as dist:
            content = dist.read()
        content = sub(r'mangos;mangos;realmd', r'{};{};{}'.format(user,pw,realmd), content)
        content = sub(r'mangos;mangos;mangos', r'{};{};{}'.format(user,pw,mangos), content)
        content = sub(r'mangos;mangos;characters', r'{};{};{}'.format(user,pw,chars), content)
        content = sub(r'LogLevel = 3', r'LogLevel = 1'.format(log), content)
        with open('{}/{}.conf'.format(path,targetFile), 'w') as conf:
            conf.write(content)
        return True

    def applyRealmConfig(self, user='mangos', pw='mangos', targetFile='realmd', realmd=False):
        if not realmd:
            realmd = '{}-realmd'.format(self.version)
        path = '{}/{}/server/etc'.format(getcwd(), self.version)
        with open('{}/realmd.conf.dist'.format(path), 'r') as dist:
            content = dist.read()
        content = sub(r'mangos;mangos;realmd', r'{};{};{}'.format(user,pw,realmd), content)
        with open('{}/{}.conf'.format(path,targetFile), 'w') as conf:
            conf.write(content)
        return True

    def compileCore(self, pch=1, debug=0, ext='ON', bot='ON', cores=None, noScript=False):
        # get paths and make sure they exist
        startPath = getcwd()
        buildPath = '{}/{}/build'.format(startPath, self.version)
        installPath = '{}/{}/server'.format(startPath, self.version)
        if not isdir(buildPath):
            makedirs(buildPath)
        if not isdir(installPath):
            makedirs(installPath)
        # use all cores if core number was not passed
        if cores == None:
            cores = cpu_count()
        # disable script if option was passed
        scripts = 'ON'
        if noScript:
            scripts = 'OFF'
        # change into buildPath and run cmake, make and make install
        chdir(buildPath)
        run([
            'cmake',
            '../mangos-{}'.format(self.version),
            '-DCMAKE_INSTALL_PREFIX=\\{}'.format(installPath),
            '-DPCH={}'.format(pch),
            '-DDEBUG={}'.format(debug),
            '-DBUILD_EXTRACTORS={}'.format(ext),
            '-DBUILD_PLAYERBOT={}'.format(bot),
            '-DBUILD_SCRIPTDEV={}'.format(scripts),
        ])
        run([
            'make',
            '-j{}'.format(cores),
        ])
        run([
            'make',
            'install',
            '-j{}'.format(cores),
        ])
        # return to normal working directory and apply configs
        chdir(startPath)
        return True

    def createUser(self, rootpw, user, pw, host='localhost'):
        db = mysql.connect(host, 'root', rootpw)
        cursor = db.cursor()
        cursor.execute('CREATE USER "{}"@"{}" IDENTIFIED BY "{}";'.format(user, host, pw))
        db.close()
        return True

    def dbSetup(self, rootpw, user='mangos', pw='mangos', host='localhost', mangos=None, realmd=None, chars=None, createMysqlUser=False):
        # set up defaults
        if mangos == None:
            mangos = '{}-mangos'.format(self.version)
        if realmd == None:
            realmd = '{}-realmd'.format(self.version)
        if chars == None:
            chars = '{}-characters'.format(self.version)
        # connect to mysql
        db = mysql.connect(host, 'root', rootpw)
        cursor = db.cursor()
        # ensure user exists
        cursor.execute('SELECT User FROM mysql.user WHERE User = "{}"'.format(user))
        if cursor.fetchone() == None:
            if not createUser:
                print('user "{}" doesn\'t exist. aborting'.format(user))
                db.close()
                return False
            else:
                createUser(rootpw, user, pw)
        # ensure dbs do NOT exist
        cursor.execute('SHOW DATABASES;')
        f = cursor.fetchall()
        for schema in [mangos, realmd, chars]:
            for x in f:
                if schema in x:
                    print('db "{}" already exist. aborting'.format(schema))
                    db.close()
                    return False
        # create dbs
        for schema in [mangos, realmd, chars]:
            cursor.execute('CREATE DATABASE `{}` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;'.format(schema))
            cursor.execute('GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, LOCK TABLES, CREATE TEMPORARY TABLES, EXECUTE, ALTER ROUTINE, CREATE ROUTINE ON `{}`.* TO "{}"@"{}";'.format(schema,user,host))
        db.close()
        with open('{}/mangos-{}/sql/base/mangos.sql'.format(self.version,self.version) ,'r') as f:
            d = mysql.connect(host,user,pw,mangos)
            c = d.cursor()
            c.execute(f.read())
            d.close()
        with open('{}/mangos-{}/sql/base/realmd.sql'.format(self.version,self.version) ,'r') as f:
            d = mysql.connect(host,user,pw,realmd)
            c = d.cursor()
            c.execute(f.read())
            d.close()
        with open('{}/mangos-{}/sql/base/characters.sql'.format(self.version,self.version) ,'r') as f:
            d = mysql.connect(host,user,pw,chars)
            c = d.cursor()
            c.execute(f.read())
            d.close()
        return True

    def applyDBConfig(self, user='mangos', pw='mangos', db=None, core=None, wait='NO', host='localhost'):
        if core == None:
            core = '../mangos-{}'.format(self.version)
        if db == None:
            db = '{}-mangos'.format(self.version)
        configPath = '{}/{}-db/InstallFullDB.config'.format(self.version,self.version)
        if not isdir(configPath):
            return False
        with open(configPath,'r') as f:
            content = f.read()
        content = sub(r'USERNAME=".*?"', r'USERNAME="{}"'.format(user), content)
        content = sub(r'PASSWORD=".*?"', r'PASSWORD="{}"'.format(pw), content)
        content = sub(r'DATABASE=".*?"', r'DATABASE="{}"'.format(db), content)
        content = sub(r'FORCE_WAIT=".*?"', r'FORCE_WAIT="{}"'.format(wait), content)
        if core != False:
            content = sub(r'CORE_PATH=".*?"', r'CORE_PATH="{}"'.format(core), content)
        with open(configPath,'w') as f:
            f.write(content)
        return True

    def dbInstall(self, user='mangos', pw='mangos', db=None, core=None, wait='NO', host='localhost'):
        scriptPath = '{}/{}-db'.format(self.version,self.version)
        if isfile('{}/InstallFullDB.config'.format(scriptPath)):
            print('config file exists. aborting')
            return False
        try:
            con = mysql.connect(host, user, pw)
            con.close()
        except:
            print('error connecting to user {}@{}. aborting'.format(user, host))
            return False
        startPath = getcwd()
        chdir(scriptPath)
        run(['./InstallFullDB.sh'])
        chdir(startPath)
        self.applyDBConfig(user, pw, db, core, wait, host)
        chdir(scriptPath)
        run(['./InstallFullDB.sh'])
        chdir(startPath)
        return True

    def dbUpdate(self, user='mangos', pw='mangos', db=None, core=None, wait='NO', host='localhost'):
        scriptPath = '{}/{}-db'.format(self.version,self.version)
        if not isfile('{}/InstallFullDB.config'.format(scriptPath)):
            print('config file does not exists. aborting')
            return False
        try:
            con = mysql.connect(host, user, pw)
            con.close()
        except:
            print('error connecting to user {}@{}. aborting'.format(user, host))
            return False
        #self.applyDBConfig(user, pw, db, core, wait, host)
        startPath = getcwd()
        chdir(scriptPath)
        run(['./InstallFullDB.sh'])
        chdir(startPath)
        return True

    def extractMaps(self, cores=None):
        if not isdir('{}/server/bin/tools'.format(self.version)):
            print('tools not found. aborting extraction.')
            return False
        if not isdir('{}/client'.format(self.version)):
            print('client not found. aborting extraction.')
            return False
        if not isfile('{}/mangos-{}/contrib/extractor_scripts/ExtractResources.sh'.format(self.version, self.version)) or not isfile('{}/mangos-{}/contrib/extractor_scripts/MoveMapGen.sh'.format(self.version, self.version)):
            print('scripts not found. aborting extraction.')
            return False
        copy2('{}/server/bin/tools/ad'.format(self.version), '{}/client'.format(self.version))
        copy2('{}/server/bin/tools/MoveMapGen'.format(self.version), '{}/client'.format(self.version))
        copy2('{}/server/bin/tools/vmap_assembler'.format(self.version), '{}/client'.format(self.version))
        copy2('{}/server/bin/tools/vmap_extractor'.format(self.version), '{}/client'.format(self.version))
        copy2('{}/mangos-{}/contrib/extractor_scripts/MoveMapGen.sh'.format(self.version, self.version), '{}/client'.format(self.version))
        copy2('{}/mangos-{}/contrib/extractor_scripts/ExtractResources.sh'.format(self.version, self.version), '{}/client'.format(self.version))
        copy2('{}/mangos-{}/contrib/extractor_scripts/offmesh.txt'.format(self.version, self.version), '{}/client'.format(self.version))
        startPath = getcwd()
        chdir('{}/client'.format(self.version))
        chmod('MoveMapGen.sh', stat('MoveMapGen.sh').st_mode | 0o100)
        chmod('ExtractResources.sh', stat('ExtractResources.sh').st_mode | 0o100)
        ex = Popen(['./ExtractResources.sh', 'a'], stdin=PIPE)
        # use all cores if core number was not passed
        if cores == None:
            cores = cpu_count()
        ex.communicate(str.encode(str(cores)))
        ret = ex.wait()
        chdir(startPath)
        print(ret)
        if ret == 0:
            if isdir('{}/server/bin/dbc'.format(self.version)):
                rmtree('{}/server/bin/dbc'.format(self.version))
            if isdir('{}/server/bin/maps'.format(self.version)):
                rmtree('{}/server/bin/maps'.format(self.version))
            if isdir('{}/server/bin/mmaps'.format(self.version)):
                rmtree('{}/server/bin/mmaps'.format(self.version))
            if isdir('{}/server/bin/vmaps'.format(self.version)):
                rmtree('{}/server/bin/vmaps'.format(self.version))
            for dir in ['dbc', 'maps', 'mmaps', 'vmaps']:
                if isdir('{}/server/bin/{}'.format(self.version, dir)):
                    rmtree('{}/server/bin/{}'.format(self.version, dir))
                move('{}/client/{}'.format(self.version, dir), '{}/server/bin'.format(self.version))
            for dir in ['Buildings', 'dbc', 'maps', 'mmaps', 'vmaps']:
                if isdir('{}/client/{}'.format(self.version, dir)):
                    rmtree('{}/client/{}'.format(self.version, dir))
            for file in ['ad', 'MoveMapGen', 'vmap_assembler', 'vmap_extractor', 'ExtractResources.sh', 'MoveMapGen.sh', 'MaNGOSExtractor.log', 'MaNGOSExtractor_detailed.log', 'offmesh.txt']:
                if isfile('{}/client/{}'.format(self.version, file)):
                    remove('{}/client/{}'.format(self.version, file))
            return True
        else:
            return False
