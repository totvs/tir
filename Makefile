install:
	python setup.py sdist
	-taskkill /f /im geckodriver.exe
	-taskkill /f /im chromedriver.exe
	pip install -U dist/cawebhelper-0.1.tar.gz