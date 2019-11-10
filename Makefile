tests:
	pytest  --cov=transiter_nycsubway

package:
	rm -r dist
	python setup.py sdist bdist_wheel

distribute:
	twine upload dist/*

.PHONY: tests
