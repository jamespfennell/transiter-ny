.PHONY: test

unit-tests:
	rm -f .coverage
	nosetests --with-coverage --cover-package=transiter_nycsubway --rednose -v tests

test: unit-tests


