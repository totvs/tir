#CAWebHelper

##What is it?

CAWebHelper is a Python module used to create test scripts for the Protheus web interface. With it, you are able to easily create and execute test suites and test cases for Protheus routines.

##How to install:

The installation is pretty simple. All you need as a requirement is Python installed in your system.
After cloning this repository, *double click on "install.cmd"* or if you have *make* installed, you could run the following command on a console:

```
make install
```

##Usage:
After the module is installed, you could just import it on your Test Case. 
See the following example: 

```python
from cawebhelper import CAWebHelper

test_helper = CAWebHelper()
test_helper.Setup('SIGAGCT','10/08/2017','T1','D MG 01 ','05')
test_helper.UTProgram('CNTA010')

test_helper.SetButton('Incluir')
test_helper.SetFilial('D MG 01')
test_helper.UTSetValue('aCab','CN0_DESCRI','ADITIVO AMBOS QUANTIDADE/PRAZO')
test_helper.UTSetValue('aCab','CN0_TIPO','1')
test_helper.UTSetValue('aCab','CN0_MODO','3 - Ambos')
test_helper.UTSetValue('aCab','CN0_ESPEC','4 - Quant/Prazo')
test_helper.SetButton('Salvar')
test_helper.SetButton('Cancelar')

test_helper.SetButton('Visualizar')
test_helper.UTCheckResult('aCab','CN0_DESCRI','ADITIVO AMBOS QUANTIDADE/PRAZO')
test_helper.UTCheckResult('aCab','CN0_TIPO','1')
test_helper.UTCheckResult('aCab','CN0_MODO','3 - Ambos')
test_helper.UTCheckResult('aCab','CN0_ESPEC','4 - Quant/Prazo')

test_helper.SetButton('Cancelar')
test_helper.AssertTrue()

test_helper.TearDown()
```

#Documentation

This project has a docs folder with Sphinx(http://www.sphinx-doc.org/en/master/) files.
The documents can be built by running the following command inside the docs folder:
```
make html
```
This will generate a documentation website inside ~cabwenhelper/docs/build/html/index.html, which you can open in any browser and find the description of every method.


#Contributing

In order to contribute be sure to follow the [Contribution](CONTRIBUTING.md) guidelines.
