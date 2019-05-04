from setuptools import setup, find_packages

setup(
    name="transiter_nycsubway",
    version="0.1dev",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["transiter"],
    license="MIT",
)
