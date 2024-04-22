.EXPORT_ALL_VARIABLES:

# Default poetry virtual environment location, relative to the project root
VENV = .venv
ROOT_DIR:=$(realpath $(shell dirname $(firstword $(MAKEFILE_LIST))))

setup: venv install
test: tests_unit tests_integration
reboot: clean setup

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

.PHONY: format
format:
	@echo "Sorting imports, formatting code..."
	isort --profile black -l $(PYTHON_MAX_LINE_LENGTH) src/
	black -l $(PYTHON_MAX_LINE_LENGTH) src/

.PHONY: tf-setup
tf-setup:
	@echo "Running Terraform locally..."
	terraform plan -var-file moto.tfvars -out moto.tfplan

.PHONY: tf-apply
tf-apply:
	@echo "Running Terraform locally..."
	terraform apply moto.tfplan

.PHONY: tf-destroy
tf-destroy:
	@echo "Running Terraform locally..."
	terraform destroy -var-file moto.tfvars -auto-approve

.PHONY: tests_unit
tests_unit:
	@echo "Running unit tests..."
	pytest -c $(ROOT_DIR)/src/lambda/pytest.ini --rootdir=$(ROOT_DIR)/src/lambda

.PHONY: tests_integration
tests_integration:
	@echo "Setting up terraform for local testing... Please wait..."
# Clean up any existing terraform state and setup a new one
	curl -X POST $$TEST_SERVER_MODE_ENDPOINT/moto-api/reset
	rm -rf ./moto.* > /dev/null
# Copy the moto test files to the root directory
	cp -r ./tests/moto* ./ > /dev/null
	$(MAKE) tf-setup > /dev/null
	$(MAKE) tf-apply
	@echo "Running integration tests..."
# TODO: Add integration tests here
	@echo "Tearing down local terraform stack... Please wait..."
	$(MAKE) tf-destroy > /dev/null
	rm -rf ./moto.* > /dev/null
	@echo "Finished integration tests."

.PHONY: clean
clean:
	rm -rf .pytest_cache/
	rm -rf $(VENV)/
	rm -rf .terraform/
	rm -rf ./terraform.*
	rm -rf ./.terraform.*
	rm -rf ./moto.*
