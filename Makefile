tests:
	pytest  --cov=transiter_nycsubway

package:
	rm dist/*
	python setup.py sdist bdist_wheel

distribute:
	twine upload dist/*

.PHONY: tests
