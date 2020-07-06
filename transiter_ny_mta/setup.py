from setuptools import setup, find_packages

setup(
    name="transiter-ny-mta",
    version="0.1.0",
    author="James Fennell",
    author_email="jamespfennell@gmail.com",
    description="Transiter parsers for NY MTA transit systems (subway, LIRR, MetroNorth)",
    url="https://github.com/jamespfennell/transiter-nycsubway",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["python-dateutil>=2.8.1", "transiter>=0.5.0"],
    license="MIT",
)
