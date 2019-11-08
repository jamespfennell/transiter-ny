from setuptools import setup, find_packages

long_description = """
# NYC Subway integration for Transiter

This package is used to integrate 
 [Transiter](https://github.com/jamespfennell/transiter) 
 with the data feeds for the New York City Subway.
The package needs to be used with configuration files provided in
 [the Github repository](https://github.com/jamespfennell/transiter); 
 as such, the full usage
 instructions are over there.
"""

setup(
    name="transiter_nycsubway",
    version="0.2.0",
    author="James Fennell",
    author_email="jamespfennell@gmail.com",
    description="NYC Subway integration for Transiter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jamespfennell/transiter-nycsubway",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["python-dateutil>=2.8.1", "transiter>=0.2.2"],
    license="MIT",
)
