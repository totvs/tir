# TIR - Test Interface Robot
![GitHub release (latest by date)](https://img.shields.io/github/v/release/totvs/tir)

TIR is a Python module used to create test scripts for web interfaces. With it, you can easily create and execute test suites and test cases for any supported web interface systems, such as Protheus Webapp.

### Current Supported Technologies

- Protheus Webapp
- APW

## Table of Contents

[Documentation](#documentation)<br>
[Installation](#installation)<br>
[Config](#config)<br>
[Usage](#usage)<br>
[Docker](#docker)<br>
[Samples](#samples)<br>
[Contact Us](#contact)<br>
[Contributing](#contributing)

## Documentation
Our documentation can be found here:

- [TIR Documentation](https://totvs.github.io/tir-docs/)

- [TIR Technical Documentation](https://totvs.github.io/tir/)

This project has a docs folder with [Sphinx](http://www.sphinx-doc.org/en/master/) files.

Our **create_docs.cmd** script handles the installation of dependencies and creates the offline documentation on the doc_files/build/html folder.

## Installation

The installation is pretty simple. All you need as a requirement is Python 3.7.9 (Mozilla Firefox) installed in your system.

There are three ways of installing TIR:

### 1. Installing and Upgrade from PyPI

TIR can be installed via pip from [Pypi](https://pypi.org/project/tir-framework/)

```shell
pip install tir_framework --upgrade
```

### 2. via Terminal(Deprecated For The Branch Master)

You can install TIR via the terminal. Make sure your Python and Git are installed and run this command:

```shell
pip install git+https://github.com/totvs/tir.git --upgrade
```

It will install the last release of TIR in the active Python instance.

## Config

The environment must be configured through a [config.json](config.json) file.
You can find one to be used as a base in this repository. To select your file,
you can either put it in your workspace or pass its path as a parameter of any of our classes' initialization.

### Config options

Here you can find all the supported keys: [Config.json keys](https://totvs.github.io/tir/configjson)

### Custom config path

Just pass the path as a parameter in your script:

#### Protheus WebApp Class example:
```python
#To use a custom path for your config.json
test_helper = Webapp("C:\PATH_HERE\config.json")
```

## Usage

After the module is installed, you could just import it into your Test Case.
See the following example:

[**Protheus WebApp Class**](https://totvs.github.io/tir-docs/TIR/first/)


## Samples

We have a repository with different samples of TIR scripts:

[TIR Script Samples](https://github.com/totvs/tir-script-samples)

## Contact

[Gitter](https://gitter.im/totvs-tir/General)

## Contributing

To contribute be sure to follow the [Contribution](CONTRIBUTING.md) guidelines.

Also, it's important to understand the chosen [architecture](https://github.com/totvs/tir/blob/master/doc_files/ARCHITECTURE.md).
