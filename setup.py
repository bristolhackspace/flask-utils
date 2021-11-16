from setuptools import setup, find_namespace_packages

setup(
    name='bristolhackspace.flask_utils',
    packages=find_namespace_packages(include=['bristolhackspace.*']),
    package_data={
        "bristolhackspace": ["*"],
    },
    install_requires=[
        'flask>=2.0',
        'yarl',
    ],
)