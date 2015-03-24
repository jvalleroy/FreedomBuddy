#! /usr/bin/env make

DATA_DIR = data
SCRIPTS_DIR = src/scripts
CERTIFICATE = $(DATA_DIR)/freedombuddy.crt
CFG_TEMPLATE = $(DATA_DIR)/template.cfg
CFG_PRODUCTION = $(DATA_DIR)/production.cfg
CFG_TEST = $(DATA_DIR)/test.cfg
KEYS_TEST = src/tests/data/test_gpg_home/

all: ssl-certificate $(CFG_PRODUCTION) $(CFG_TEST)

ssl-certificate: $(CERTIFICATE)

$(CERTIFICATE):
ifeq ($(wildcard $(CERTIFICATE)),)
	sudo make-ssl-cert generate-default-snakeoil
	sudo make-ssl-cert /usr/share/ssl-cert/ssleay.cnf $(CERTIFICATE)
	sudo chgrp 1000 $(CERTIFICATE)
	sudo chmod g+r $(CERTIFICATE)
	sudo touch $(CERTIFICATE)
else
	echo $(CERTIFICATE) already exists
endif

$(CFG_PRODUCTION):
	cp $(CFG_TEMPLATE) $(CFG_PRODUCTION)
	python src/config/update_encryption_key.py $(CFG_PRODUCTION) ~/.gnupg/

$(CFG_TEST):
	cp $(CFG_TEMPLATE) $(CFG_TEST)
	python src/config/update_encryption_key.py $(CFG_TEST) $(KEYS_TEST)

clean:
	rm -f $(CERTIFICATE) $(CFG_PRODUCTION) $(CFG_TEST)
