#! /usr/bin/env make

DATA_DIR = data
SCRIPTS_DIR = src/scripts
CFG_TEMPLATE = $(DATA_DIR)/template.cfg
CFG_PRODUCTION = $(DATA_DIR)/production.cfg
APACHE_CONF=$(DATA_DIR)/apache-freedombuddy.conf
CFG_TEST = $(DATA_DIR)/test.cfg
KEYS_TEST = src/tests/data/test_gpg_home/

all: $(CFG_PRODUCTION) $(CFG_TEST)

$(CFG_PRODUCTION):
	cp $(CFG_TEMPLATE) $(CFG_PRODUCTION)
	python src/config/update_encryption_key.py $(CFG_PRODUCTION) ~/.gnupg/

$(CFG_TEST):
	cp $(CFG_TEMPLATE) $(CFG_TEST)
	python src/config/update_encryption_key.py $(CFG_TEST) ~/.gnupg/

install:
	cp $(APACHE_CONF) /etc/apache2/conf-available/
	a2enconf apache-freedombuddy

clean:
	rm -f $(CFG_PRODUCTION) $(CFG_TEST)
