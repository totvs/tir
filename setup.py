
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'CAWebHelper',
    'author': 'TOTVS Automation Team',
    'url': 'http://code.engpro.totvs.com.br/heitor.marsolla/cawebhelper',
    'download_url': 'http://code.engpro.totvs.com.br/heitor.marsolla/cawebhelper',
    'author_email': 'squad.automacaoprotheus@totvs.com.br',
    'version': '0.1',
    'install_requires': [
        'beautifulsoup4==4.6.0',
        'bs4==0.0.1',
        'pandas==0.22.0',
        'python-dateutil==2.6.1',
        'pytz==2017.3',
        'selenium==3.8.0',
        'six==1.11.0',
        'enum34'
    ],
    'packages': ['cawebhelper'],
    'scripts': [],
    'name': 'cawebhelper'
}

setup(**config, include_package_data=True)

