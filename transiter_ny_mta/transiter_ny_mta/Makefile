tests:
	pytest  --cov=transiter_nycsubway

package:
	rm -rf dist 
	rm -rf build
	python setup.py sdist bdist_wheel

distribute:
	twine upload dist/*

.PHONY: tests
