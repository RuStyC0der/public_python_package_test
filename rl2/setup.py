from setuptools import setup, find_packages

setup(
    name='rl2corelib',
    version='0.1',
    description='Contains libraries with basic logic for rl2',
    packages=find_packages(),
    install_requires=[
        'boto3',
        'botocore',
        'sqlalchemy',
        'jinja2'
    ],
    python_requires='>=3.8'
)
