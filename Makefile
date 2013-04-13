noop:
	@true

.PHONY: noop

test:
	py.test --cov gonzo
	flake8 --ignore=E128 gonzo tests
