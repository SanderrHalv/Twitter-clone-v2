# setup.py
from setuptools import setup, find_packages

setup(
    name="twitter_clone",
    version="0.1",
    packages=find_packages(),       # finds your 'app' package
    include_package_data=True,
)
