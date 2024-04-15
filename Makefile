.EXPORT_ALL_VARIABLES:

# Default poetry virtual environment location, relative to the project root
VENV = .venv

setup: venv install

.PHONY: venv
venv:
	@echo "Creating .venv..."
	poetry config virtualenvs.prompt "py{python_version} "
	poetry env use python3

.PHONY: install
install:
	@echo "Installing dependencies..."
	poetry install

.PHONY: format
format:
	@echo "Sorting imports, formatting code..."
	isort --profile black -l $(PYTHON_MAX_LINE_LENGTH) src/
	black -l $(PYTHON_MAX_LINE_LENGTH) src/

.PHONY: clean
clean:
	rm -rf .pytest_cache/
	rm -rf $(VENV)/