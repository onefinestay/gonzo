noop:
	@true

.PHONY: noop

develop:
	python setup.py develop
	pip install -r test_requirements.txt

pytest:
	py.test --cov gonzo tests

flake8:
	flake8 --ignore=E128 gonzo tests

test: pytest flake8
