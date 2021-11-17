from setuptools import setup, find_namespace_packages

setup(
    name='bristolhackspace.flask_utils',
    packages=find_namespace_packages(include=['bristolhackspace.*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask>=2.0',
        'yarl',
    ],
)