
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'My Project',
    'author': 'My Name',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'My email.',
    'version': '0.1',
    'install_requires': [
        'beautifulsoup4==4.6.0',
        'bs4==0.0.1',
        'numpy==1.13.3',
        'pandas==0.22.0',
        'python-dateutil==2.6.1',
        'pytz==2017.3',
        'selenium==3.8.0',
        'six==1.11.0',
        'enum34',
        'sphinx',
        'sphinx-rtd-theme'
    ],
    'packages': ['cawebhelper'],
    'scripts': [],
    'name': 'cawebhelper'
}

setup(**config, include_package_data=True)

