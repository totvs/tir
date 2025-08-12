
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('tir/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    description='Test Interface Robot',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='tir_engpro',
    url='https://github.com/totvs/tir',
    download_url='https://github.com/totvs/tir',
    project_urls={
    'Script Samples': 'https://github.com/totvs/tir-script-samples'
    },
    version=main_ns['__version__'],
    license='MIT',
    keywords='test automation selenium tir totvs protheus framework',
    classifiers=[
        'Environment :: Web Environment',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.12',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing'
    ],
    install_requires=[
        'beautifulsoup4==4.12.3',
        'numpy==1.26.4',
        'pandas==2.2.1',
        'python-dateutil==2.9.0.post0',
        'pytz==2024.1',
        'selenium==4.19.0',
        'six==1.16.0',
        'enum34==1.1.10',
        'requests==2.31.0',
        'pyodbc==5.1.0',
        'psutil==5.9.8',
        'lxml==5.1.0',
        'opencv-python==4.9.0.80',
        'webdriver-manager==4.0.2',
        'sqlalchemy==2.0.42',
        'oracledb==3.2.0',
    ],
    python_requires='==3.12.*',
    packages=find_packages(),
    scripts=[],
    name='tir_framework',
    include_package_data=True
)
