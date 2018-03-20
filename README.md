# CMaNGOS install script

This project is written in Python 3 and can be used to install, update and start the CMaNGOS servers and databases (GNU/Linux only so far).

## Usage

#### Software requirements

**Debian/Ubuntu:**  
`sudo apt-get install build-essential automake git autoconf patch libmysql++-dev mysql-server libtool libssl-dev grep sed binutils zlibc libc6 libbz2-dev cmake libboost-all-dev python3 python3-pip`

**Python:**  
`pip3 install PyQt5 mysqlclient`

#### Starting

`python3 -m main`

Running the installer and clicking these buttons:

1. Copy Client
2. Install Server
3. Install Database
4. Create Map Files/Copy Map Files

should create a directory structure like this:

```
cmangos-installer
| - classic
    | - build
    | - classic-db
    | - client
    | - mangos-classic
    | - server
```

and show the button to start the server.

## Setup MariaDB root password

If you installed MariaDB instead of MySQL you will need to make a few changes for the Makefile to work correctly.

1. Run this line by line in a terminal (replacing YOUR_NEW_PASSWORD):
```
sudo mysql -u root
update mysql.user set password=password('YOUR_NEW_PASSWORD') where user='root';
update mysql.user set plugin='' where user='root';
flush privileges;
quit
```
2. Edit `/etc/mysql/debian.cnf` to contain new root password.
