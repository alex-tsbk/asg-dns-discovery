.EXPORT_ALL_VARIABLES:

# Default poetry virtual environment location, relative to the project root
VENV=.venv
# Port to run the moto server on
MOTO_PORT=5000

# Command is execute when devcontainer is started
setup: venv install

# Commands to run before committing code
test: tests_unit tests_integration tests_component tests_terraform
pre-commit: format test

# Commands to help with re-initializing the project setup
reset: clean setup

# Bootstrap commands

.PHONY: venv
venv:
	@echo "Creating .venv..."
	poetry config virtualenvs.prompt "py{python_version} "
	poetry env use python3

.PHONY: install
install:
	@echo "Installing dependencies..."
	poetry install
	@echo "Installing pre-commit hooks..."
	poetry run pre-commit install
	@echo "Ininitalizing terraform..."
	terraform init
	@echo "Finished installing dependencies."

# Linting and formatting commands

.PHONY: format
format:
	@echo "Sorting imports, formatting code..."
	@isort --profile black -l $(PYTHON_MAX_LINE_LENGTH) src/
	@black -l $(PYTHON_MAX_LINE_LENGTH) src/

# Motot setup

.PHONY: moto-server-up
moto-server-up:
	@echo "Setting up moto server..."
	@echo "" > $$PROJECT_ROOT/.moto-server-logs.log
	MOTO_CALL_RESET_API=false moto_server --port $(MOTO_PORT) --host localhost > $$PROJECT_ROOT/.moto-server-logs.log 2>&1 &
	@echo "Moto server started on port $(MOTO_PORT)."

.PHONY: moto-server-down
moto-server-down:
	@echo "Killing moto server..."
	@$(MAKE) kill-port PORT=$(MOTO_PORT)

# Terraform Tests

.PHONY: tests_terraform_local
tests_terraform_local:
	@echo "** Running Terraform tests.. [LOCAL]"
	terraform test -filter=tests/aws.local.tftest.hcl
	@echo "** Finished Terraform tests: SUCCESS."

.PHONY: tests_terraform_moto
tests_terraform_moto:
	@echo "** Running Terraform tests... [MOTO]"
	@$(MAKE) moto-server-up
	terraform test -filter=tests/aws.moto.tftest.hcl
	@$(MAKE) moto-server-down
	@echo "** Finished Terraform tests: SUCCESS."

.PHONY: tests_terraform
tests_terraform: tests_terraform_local tests_terraform_moto

# Unit tests

.PHONY: tests_unit
tests_unit:
	@echo "Running unit tests..."
	pytest -c $(PROJECT_ROOT)/src/lambda/tests/tests_unit/pytest.ini --rootdir=$(PROJECT_ROOT)/src/lambda/ $(PROJECT_ROOT)/src/lambda/tests/tests_unit/

# Integration tests

tests_integration_aws:
	@echo "Running AWS integration tests..."
	pytest -c $(PROJECT_ROOT)/src/lambda/tests/tests_integration/tests_aws/pytest.ini --rootdir=$(PROJECT_ROOT)/src/lambda/ $(PROJECT_ROOT)/src/lambda/tests/tests_integration/tests_aws/

.PHONY: tests_integration
tests_integration: tests_integration_aws

# Utility commands

.PHONY: kill-port
kill-port:
	@PID=$$(lsof -t -i:$(PORT)); \
	if [ -n "$$PID" ]; then \
		echo "Killing process $$PID on port $(PORT)..."; \
		kill $$PID || true; \
	fi

.PHONY: clean
clean:
	rm -rf .pytest_cache/
	rm -rf $(VENV)/
	rm -rf .terraform/
	rm -rf ./terraform.*
	rm -rf ./.terraform.*
	rm -rf ./moto.*
