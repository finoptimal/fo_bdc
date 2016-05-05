from setuptools import setup, find_packages
from glob import glob

setup(name='fo_bdc',
      version='1.0',
      description='Wrapper around Bill.com API',
      # Note that the tests folder can only be 1 level deep!!! 
      scripts=glob('tests/*'),
      packages=find_packages())
