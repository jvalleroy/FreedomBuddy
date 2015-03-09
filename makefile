#! /usr/bin/env make

DATA_DIR = data
BUILD_DIR = build
SCRIPTS_DIR = src/scripts
CERTIFICATE = $(DATA_DIR)/freedombuddy.crt
CFG_TEMPLATE = $(DATA_DIR)/template.cfg
CFG_PRODUCTION = $(DATA_DIR)/production.cfg
CFG_TEST = $(DATA_DIR)/test.cfg
KEYS_TEST = src/tests/data/test_gpg_home/

all: predepend $(BUILD_DIR) ssl-certificate $(BUILD_DIR)/plinth $(SCRIPTS_DIR)/tinc_rollout $(CFG_PRODUCTION) $(CFG_TEST)
	@echo "Configuring FreedomBuddy for first run."
	./start.sh 0
	sleep 10
	PYTHONPATH=.:$$PYTHONPATH python src/connectors/cli/controller.py --stop
	@echo ""
	@echo "Configuration complete."
	@echo "You can now start FreedomBuddy by running:"
	@echo "    bash start.sh 5"
# TODO should this run publish at some point?

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

ssl-certificate: $(CERTIFICATE)

$(CERTIFICATE): $(BUILD_DIR) $(BUILD_DIR)/cert-depends
ifeq ($(wildcard $(CERTIFICATE)),)
	sudo make-ssl-cert generate-default-snakeoil
	sudo make-ssl-cert /usr/share/ssl-cert/ssleay.cnf $(CERTIFICATE)
	sudo chgrp 1000 $(CERTIFICATE)
	sudo chmod g+r $(CERTIFICATE)
	sudo touch $(CERTIFICATE)
else
	echo $(CERTIFICATE) already exists
endif

$(BUILD_DIR)/cert-depends: $(BUILD_DIR)
	sudo apt-get install ssl-cert
	touch $(BUILD_DIR)/cert-depends

$(BUILD_DIR)/plinth: $(BUILD_DIR)
	test -d $(BUILD_DIR)/plinth || git clone git://github.com/NickDaly/Plinth.git $(BUILD_DIR)/plinth
	cd $(BUILD_DIR)/plinth; git pull

$(SCRIPTS_DIR)/tinc_rollout: $(BUILD_DIR)
	test -d $(SCRIPTS_DIR)/tinc_rollout || git clone git://github.com/jvasile/tinc-rollout.git $(SCRIPTS_DIR)/tinc_rollout
	cd $(SCRIPTS_DIR)/tinc_rollout; git pull

predepend:
	sudo sh -c "apt-get install python-bjsonrpc python-cheetah python-cherrypy3 python-contract python-dateutil python-httplib2 python-openssl python-routes python-socksipy python-gnupg"
	touch predepend

$(CFG_PRODUCTION):
	cp $(CFG_TEMPLATE) $(CFG_PRODUCTION)
	python src/config/update_encryption_key.py $(CFG_PRODUCTION) ~/.gnupg/

$(CFG_TEST):
	cp $(CFG_TEMPLATE) $(CFG_TEST)
	python src/config/update_encryption_key.py $(CFG_TEST) $(KEYS_TEST)

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(CERTIFICATE)
	rm -f predepend
