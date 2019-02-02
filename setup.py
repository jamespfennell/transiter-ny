from setuptools import setup, find_packages

setup(
    name='transiter_nycsubway',
    version='0.1dev',
    packages=find_packages(),
    include_package_data=True,
    install_requires = [
        'python-dateutil',
#        'transiter==0.1dev'
    ],
#    dependency_links=[
#        'https://github.com/jamespfennell/transiter/tarball/master#egg=transiter-0.1dev'
#    ],
    license='MIT',
)