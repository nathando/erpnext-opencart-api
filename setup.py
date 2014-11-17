from setuptools import setup, find_packages
import os

version = '0.0.1'

setup(
    name='opencart_api',
    version=version,
    description='App for connecting Opencart through APIs. Updating Products, recording transactions',
    author='<nathan.dole@gmail.com> Nathan (Hoovix Consulting Pte. Ltd.)',
    author_email='nathan.dole@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=("frappe",),
)
