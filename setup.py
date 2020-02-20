
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    description='TOTVS Interface Robot',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='tir_engpro',
    url='https://github.com/totvs/tir',
    download_url='https://github.com/totvs/tir',
    project_urls={
    'Script Samples': 'https://github.com/totvs/tir-script-samples'
    },
    version='1.13.0.post7',
    license='MIT',
    keywords='test automation selenium tir totvs protheus framework',
    classifiers=[
        'Environment :: Web Environment',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing'
    ],
    install_requires=[
        'beautifulsoup4>=4.7.1',
        'bs4>=0.0.1',
        'numpy',
        'pandas>=0.23.4',
        'python-dateutil>=2.6.1',
        'pytz>=2017.3',
        'selenium>=3.8.0',
        'six==1.11.0',
        'enum34',
        'requests'
    ],
    packages=['tir'],
    scripts=[],
    name='tir_framework'
)
