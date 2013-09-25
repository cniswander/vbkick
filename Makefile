# Makefile for vbkick and convert_2_scancode.py scripts (bash & python)
# src: https://github.com/wilas/vbkick
.PHONY: all

# where place files
MANDIR := /usr/local/man/man1
PREFIX := $(shell echo $(PREFIX))

# custom shebang
BASH_SHEBANG := $(shell echo $(BASH_SHEBANG))
PY_SHEBANG := $(shell echo $(PY_SHEBANG))

# install command
INSTALL := install

# place for tmp files
BUILD_DIR := build_src

# what scripts install/uninstall
BASH_TARGET := vbkick
PY_TARGET := convert_2_scancode.py


all:
	@printf "usage:\tmake install\n"
	@printf "\tmake uninstall\n"

install: check-env
	mkdir -p $(BUILD_DIR)
	@sed '1,1 s:#!/usr/bin/python:#!$(PY_SHEBANG):; 1,1 s:"::g' $(PY_TARGET) > $(BUILD_DIR)/$(PY_TARGET).tmp
	@sed '1,1 s:#!/bin/bash:#!$(BASH_SHEBANG):; 1,1 s:"::g' $(BASH_TARGET) > $(BUILD_DIR)/$(BASH_TARGET).tmp
	$(INSTALL) -m 0755 -d $(PREFIX)
	$(INSTALL) -m 0755 -p $(BUILD_DIR)/$(PY_TARGET).tmp $(PREFIX)/$(PY_TARGET)
	$(INSTALL) -m 0755 -p $(BUILD_DIR)/$(BASH_TARGET).tmp $(PREFIX)/$(BASH_TARGET)
	$(INSTALL) -g 0 -o 0 -m 0644 -p docs/man/vbkick.1 $(MANDIR)
	rm -rf $(BUILD_DIR)

uninstall: check-env
	cd $(PREFIX) && rm -f $(BASH_TARGET) && rm -f $(PY_TARGET)
	cd $(MANDIR) && rm -f vbkick.1

clean:
	rm -rf $(BUILD_DIR)

check-env:
ifndef PREFIX
  PREFIX := "/usr/local/bin"
endif
ifndef BASH_SHEBANG
  BASH_SHEBANG := "/bin/bash"
endif
ifndef PY_SHEBANG
  PY_SHEBANG := "/usr/bin/python"
endif
