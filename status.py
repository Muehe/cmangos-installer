from os.path import isfile, isdir
from os import devnull
from subprocess import run

DEVNULL = open(devnull, 'w')

class Status():
    def __init__(self):
        self.stats = {}
        if self.__checkBinary('systemctl'):
            self.services = 'systemctl'
        else:
            if self.__checkBinary('service'):
                self.services = 'service'
            else:
                self.services = None
        self.update()

    def __checkService(self, service):
        if self.services == None:
            return False
        if self.services == 'systemctl':
            return (run([self.services, 'status', service], stdout=DEVNULL).returncode == 0)
        if self.services == 'service':
            return (run([self.services, service, 'status'], stdout=DEVNULL).returncode == 0)

    def __checkBinary(self, binary):
        return run(['which', binary], stdout=DEVNULL).returncode == 0

    def update(self, value=None):
        if value == None or value == 'mysql_client':
            self.stats['mysql_client'] = self.__checkBinary('mysql')
        if value == None or value == 'mysql_server':
            self.stats['mysql_server'] = self.__checkBinary('mysqld')
        if value == None or value == 'mysql_running':
            self.stats['mysql_running'] = self.__checkService('mysql')
