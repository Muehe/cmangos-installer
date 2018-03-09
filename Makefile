# get login information from user
$(info ########################################################################)
$(info ################### Welcome to the CMaNGOS installer ###################)
$(info ########################################################################)
$(info ========================== Enter MySQL info ============================)
 # mysql root pw is only needed when creating the user and dbs
ifeq "$(INIT)" "1"
  MYSQL_ROOT := $(shell stty -echo; read -p "MySQL Root Password: " pwd; echo $$pwd; stty echo)
  $(info password temporarily saved)
  BUILD_EXTRACTORS := ON
endif
# get mysql user
USER := $(shell bash -c 'read -p "User Name (leave empty for default): " usr; echo $$usr')
ifeq "$(USER)" ""
  USER := mangos
endif
# get mysql password
PASSWORD := $(shell stty -echo; read -p "User Password (leave empty for default): " pwd; echo $$pwd; stty echo)
ifeq "$(PASSWORD)" ""
  PASSWORD := mangos
endif
$(info password saved)

# set defaults if they haven't been passed to make
INIT ?= 0
CORES ?= $(shell grep -c ^processor /proc/cpuinfo)
DEBUG ?= 0
PCH ?= 1
BUILD_EXTRACTORS ?= OFF
BUILD_PLAYERBOT ?= ON

# define functions
define clone_core
if [ ! -d "mangos-$(1)" ]; \
then \
	echo "=================== Cloning $(1) core repository ===================="; \
	git clone https://github.com/cmangos/mangos-$(1).git; \
	echo "================================= Done ================================="; \
else \
	echo "=============== Core repository already exists, updating ==============="; \
	$(call pull_core,$(1)); \
fi
endef
define clone_db
if [ ! -d "$(1)-db" ]; \
then \
	echo "================= Cloning $(1) database repository =================="; \
	git clone https://github.com/cmangos/$(1)-db.git; \
	echo "================================= Done ================================="; \
else \
	echo "============= Database repository already exists, updating ============="; \
	$(call pull_db,$(1)); \
fi
endef
define pull_core
if [ -d "mangos-$(1)" ]; then \
	echo "================== Updating $(1) core repository ===================="; \
	cd mangos-$(1); \
	git checkout master; \
	git pull; \
	echo "================================= Done ================================="; \
	cd ..; \
else \
	echo "========================== No core repository =========================="; \
fi
endef
define pull_db
if [ -d "$(1)-db" ]; then \
	echo "================= Updating $(1) database repository ================="; \
	cd $(1)-db; \
	git checkout master; \
	git pull; \
	echo "================================= Done ================================="; \
	cd ..; \
else \
	echo "======================== No database repository ========================"; \
fi
endef
# already done by InstallFullDB.sh?
define dbc
for sql_file in ls mangos-$(1)/sql/base/dbc/original_data/*.sql; do \
	mysql -u $(USER) -p$(PASSWORD) $(1)-mangos < $sql_file; \
done; \
for sql_file in ls mangos-$(1)/sql/base/dbc/updates/*.sql; do \
	mysql -u $(USER) -p$(PASSWORD) $(1)-mangos < $sql_file; \
done
endef

# install/update all cores. since the projects are phony, they will be run every time
all: classic tbc wotlk
	@echo "Finished"

# install/update a specific core
.PHONY: classic tbc wotlk
classic tbc wotlk:
	@echo "########################################################################"
	@echo "########################### $@ started ############################"
	@echo "########################################################################"
	@if [ "$(INIT)" = "1" ]; then \
		echo "===================== Initiating folder structure ======================"; \
		mkdir -p $@; \
		cd $@; \
		mkdir -p server; \
		mkdir -p client; \
		mkdir -p build; \
		echo "========================= Cloning repositories ========================="; \
		$(call clone_core,$@); \
		$(call clone_db,$@); \
		sed -e "s/\`mangos\`/\`$@-mangos\`/g" \
		-e "s/\`characters\`/\`$@-characters\`/g" \
		-e "s/\`realmd\`/\`$@-realmd\`/g" \
		-e "s/'mangos'@/'$(USER)'@/g" \
		-e "s/'mangos';/'$(PASSWORD)';/" \
		mangos-$@/sql/create/db_create_mysql.sql > test.sql; \
		echo "================ Create databases, user and set grants ================="; \
		echo "================= (Error 1007 and 1396 can be ignored) ================="; \
		mysql --force -u root -p$(MYSQL_ROOT) < test.sql; \
		echo "========================= Initialise databases ========================="; \
		mysql -u $(USER) -p$(PASSWORD) $@-mangos < mangos-$@/sql/base/mangos.sql; \
		mysql -u $(USER) -p$(PASSWORD) $@-characters < mangos-$@/sql/base/characters.sql; \
		mysql -u $(USER) -p$(PASSWORD) $@-realmd < mangos-$@/sql/base/realmd.sql; \
		# $(call dbc,$@); \
	else \
		echo "========================= Pulling repositories ========================="; \
		cd $@; \
		$(call pull_core,$@); \
		$(call pull_db,$@); \
	fi
	@echo "============================ Fill databases ============================"
	@if [ ! -f "$@/$@-db/InstallFullDB.config" ]; then \
		cd $@/$@-db; \
		./InstallFullDB.sh && \
		echo "Error creating config file, script returned 0" || \
		echo "========================== Config file created ========================="; \
		sed -i \
		-e "s/DATABASE=\"mangos\"/DATABASE=\"$@-mangos\"/" \
		-e "s/USERNAME=\"mangos\"/USERNAME=\"$(USER)\"/" \
		-e "s/PASSWORD=\"mangos\"/PASSWORD=\"$(PASSWORD)\"/" \
		-e "s/CORE_PATH=\"\"/CORE_PATH=\"..\/mangos-$@\"/" \
		InstallFullDB.config; \
		echo "========================= Config file updated =========================="; \
	fi
	@echo "====================== Starting InstallFullDB.sh ======================="
	@cd $@/$@-db; \
	./InstallFullDB.sh
	@echo "====================== Finished InstallFullDB.sh ======================="
	@echo "======================= Compile and install core ======================="
	@cd $@/build; \
	cmake ../mangos-$@ \
	-DCMAKE_INSTALL_PREFIX=\../server \
	-DPCH=$(PCH) \
	-DDEBUG=$(DEBUG) \
	-DBUILD_EXTRACTORS=$(BUILD_EXTRACTORS) \
	-DBUILD_PLAYERBOT=$(BUILD_PLAYERBOT); \
	make -j$(CORES); \
	make install -j$(CORES)
	@if [ "$(INIT)" = "1" ]; then \
		echo "================= Copy config files and update logins =================="; \
		sed \
		-e "s/mangos;mangos;realmd/$(USER);$(PASSWORD);$@-realmd/" \
		-e "s/mangos;mangos;mangos/$(USER);$(PASSWORD);$@-mangos/" \
		-e "s/mangos;mangos;characters/$(USER);$(PASSWORD);$@-characters/" \
		$@/server/etc/mangosd.conf.dist > $@/server/etc/mangosd.conf; \
		sed \
		-e "s/mangos;mangos;realmd/$(USER);$(PASSWORD);$@-realmd/" \
		$@/server/etc/realmd.conf.dist > $@/server/etc/realmd.conf; \
	fi
	@echo "########################################################################"
	@echo "########################### $@ finished ###########################"
	@echo "########################################################################"
