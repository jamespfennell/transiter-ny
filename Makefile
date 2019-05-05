tests:
	nosetests --with-coverage --cover-package=transiter_nycsubway --rednose -v tests

package:
	rm dist/*
	python setup.py sdist bdist_wheel

distribute:
	twine upload dist/*

.PHONY: tests
