from setuptools import setup, find_packages

setup(
    name="transiter_nycsubway",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["python-dateutil", "transiter"],
    license="MIT",
)
