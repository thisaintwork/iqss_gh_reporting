from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='iqss_gh_reporting',
    version='0.1',
    description='collects raw data from github and transforms it into a format that can be used for reporting',
    author='Mike Reekie',
    author_email='mike@reekie.us',
    url='https://github.com/thisaintwork/iqss_gh_reporting/tree/master/workflows',
    license='MIT',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'PyGithub',
        'gql',
        'json2xml',
        'pathvalidate',
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'fetch_from_legacy_proj = workflows.main:main'
        ]
}
)
