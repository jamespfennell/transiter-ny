from setuptools import setup, find_packages

setup(
    name='Transiter NYC Subway package',
    version='0.1dev',
    packages=find_packages(),
    install_requires = [
        'python-dateutil',
        'transiter==0.1dev'
    ],
    dependency_links=[
        'https://github.com/jamespfennell/transiter/tarball/master#egg=transiter-0.1dev'
    ],
    license='MIT',
)