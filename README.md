# CMaNGOS install script

This project contains just a Makefile which can be used to either install or update the CMaNGOS servers and databases on Ubuntu/Debian.

**Note:** Extracting files from the client is not yet included.

## Usage

#### Options
* **INIT** *(default: 0)*  
  Generate directory structure and clone repositories.
* **CORES** *(default: number of processors listed in `/proc/cpuinfo`)*  
  The number of cores used for compilation.

#### Cmake options
* **DEBUG** *(default: 0)*  
  Compile debug version.
* **PCH** *(default: 1)*  
  Use precompiled headers.
* **BUILD_EXTRACTORS** *(default: OFF)*  
  Build extractor binaries.
* **BUILD_PLAYERBOT** *(default: ON)*  
  Include Playerbot in core build.

#### Examples
* Install only Classic:  
  `make classic INIT=1`
* Install Classic and WotLK:  
  `make classic wotlk INIT=1`
* Install all three versions:  
  `make INIT=1`
* Update only Classic:  
  `make classic`
* Update all three versions:  
  `make`

Running e.g. `make classic INIT=1` will create a directory structure like this:

```
cmangos-installer
| - classic
    | - build
    | - classic-db
    | - client
    | - mangos-classic
    | - server
```

## Software requirements

```
sudo apt-get install \
    build-essential \
    `#contained in build-essential: gcc` \
    `#contained in build-essential: g++` \
    `#contained in build-essential: make` \
    automake \
    git \
    autoconf \
    patch \
    libmysql++-dev \
    mysql-server \
    `#alternative to mysql-server: mariadb-server` \
    libtool \
    libssl-dev \
    grep \
    sed \
    binutils \
    zlibc \
    libc6 \
    libbz2-dev \
    cmake \
    libboost-all-dev
```

`sudo apt-get install build-essential automake git autoconf patch libmysql++-dev mysql-server libtool libssl-dev grep sed binutils zlibc libc6 libbz2-dev cmake libboost-all-dev`

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
