
install:
	pip install --process-dependency-links -e .

unit-tests:
	nosetests --with-coverage --cover-package=transiter_nycsubway --rednose -v tests



