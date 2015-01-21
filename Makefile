noop:
	@true

.PHONY: noop

develop:
	python setup.py develop
	pip install -r test_requirements.txt

unit_tests:
	coverage run --source=gonzo -m pytest tests
	coverage report

all_tests:
	coverage run --source=gonzo -m pytest tests integration_tests
	coverage report

flake8:
	flake8 --ignore=E128 gonzo tests

test: unit_tests flake8
