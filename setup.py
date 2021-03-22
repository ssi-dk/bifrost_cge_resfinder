from setuptools import setup, find_packages

setup(
    name='bifrost_cge_resfinder',
    version='v3',
    description='Datahandling functions for bifrost (later to be API interface)',
    url='https://github.com/ssi-dk/bifrost_cge_resfinder',
    author="Kim Ng, Martin Basterrechea",
    author_email="kimn@ssi.dk",
    packages=find_packages(),
    install_requires=[
        'bifrostlib >= 2.1.9',
    ],
    package_data={"bifrost_cge_resfinder": ['config.yaml']},
    include_package_data=True
)
