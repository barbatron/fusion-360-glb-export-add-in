ADDIN_NAME := Export As Glb
DIST_DIR := dist
PACKAGE_NAME := Export-As-Glb-submission.zip
PACKAGE_PATH := $(DIST_DIR)/$(PACKAGE_NAME)

# Required by Autodesk submission process.
REQUIRED_FILES := \
	Export As Glb.manifest \
	Export As Glb.py

# Helpful extras for reviewers and users.
OPTIONAL_FILES := \
	LICENSE \
	README.md \
	addon-icon.svg

FILES := $(REQUIRED_FILES) $(OPTIONAL_FILES)

.PHONY: all package clean verify

all: package

verify:
	@for f in $(REQUIRED_FILES); do \
		if [ ! -f "$$f" ]; then \
			echo "Missing required file: $$f"; \
			exit 1; \
		fi; \
	done

package: verify

ifeq ($(OS),Windows_NT)
	@powershell -NoProfile -ExecutionPolicy Bypass -File .\package-submission.ps1
else
	@mkdir -p "$(DIST_DIR)"
	@rm -f "$(PACKAGE_PATH)"
	@zip -q -j "$(PACKAGE_PATH)" $(FILES)
	@echo "Created $(PACKAGE_PATH)"
endif

clean:
	@rm -rf "$(DIST_DIR)"
	@echo "Removed $(DIST_DIR)"