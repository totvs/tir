install:
	python setup.py build
	python setup.py sdist
	pip install -U dist/cawebhelper-0.1.tar.gz