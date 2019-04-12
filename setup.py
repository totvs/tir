
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'TOTVS Interface Robot',
    'author': 'TOTVS Automation Team',
    'url': 'https://github.com/totvs/tir',
    'download_url': 'https://github.com/totvs/tir',
    'author_email': 'squad.automacaoprotheus@totvs.com.br',
    'version': '1.9.1',
    'install_requires': [
        'beautifulsoup4==4.6.0',
        'bs4==0.0.1',
        'numpy',
        'pandas==0.23.4',
        'python-dateutil==2.6.1',
        'pytz==2017.3',
        'selenium==3.8.0',
        'six==1.11.0',
        'enum34',
        'requests'
    ],
    'packages': ['tir'],
    'scripts': [],
    'name': 'tir'
}

setup(**config, include_package_data=True)