.EXPORT_ALL_VARIABLES:

# Default poetry virtual environment location, relative to the project root
VENV=.venv
# Port to run the moto server on
MOTO_PORT=5000

# Command is execute when devcontainer is started
setup: venv install
# Commands to run before committing code
test: tests_unit tests_integration tests_terraform
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

# Terraform Commands

.PHONY: tf-setup
tf-setup:
	@echo "** Creating Terraform plan..."
	terraform plan -var-file moto.tfvars -out moto.tfplan

.PHONY: tf-apply
tf-apply:
	@echo "** Applying Terraform plan..."
	terraform apply moto.tfplan

.PHONY: tf-destroy
tf-destroy:
	@echo "** Destroying Terraform stack..."
	terraform destroy -var-file moto.tfvars -auto-approve

# Terraform Tests

.PHONY: tests_terraform
tests_terraform:
	@echo "** Running Terraform tests..."
# Ensure we force-recreate the moto server for each test
	@rm -rf ./moto.* > /dev/null
	$(MAKE) kill-port PORT=$(MOTO_PORT)
# Set up moto server
	@echo "** Setting up terraform for local testing... Please wait..."
	@echo "" > $$PROJECT_ROOT/.moto-server-logs.log
	@( \
	MOTO_CALL_RESET_API=false \
	TEST_SERVER_MODE=true \
	moto_server --port $(MOTO_PORT) --host localhost >> $$PROJECT_ROOT/.moto-server-logs.log 2>&1 & \
	)
# Copy the moto test files to the root directory
	@cp -r ./tests/moto* ./ > /dev/null
	@$(MAKE) tf-setup
	@$(MAKE) tf-apply
# TODO: Run tests to ensure that required resources are there, can do by inspecting state file
# No errors, proceed with tear-down
	@echo "** Tearing down local terraform stack... Please wait..."
	$(MAKE) tf-destroy
	@echo "** Killing moto server..."
	@$(MAKE) kill-port PORT=$(MOTO_PORT)
	@rm -rf ./moto.* > /dev/null
	@echo "** Finished Terraform tests: SUCCESS."

# Unit/Integration tests

.PHONY: tests_unit
tests_unit:
	@echo "Running unit tests..."
	pytest -c $(PROJECT_ROOT)/src/lambda/tests/tests_unit/pytest.ini --rootdir=$(PROJECT_ROOT)/src/lambda/ $(PROJECT_ROOT)/src/lambda/tests/tests_unit/

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
