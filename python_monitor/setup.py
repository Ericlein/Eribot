from setuptools import setup, find_packages

setup(
    name="monitor-slackbot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "psutil",
        "pytest",
        "slack-sdk",
        "requests"
    ],
)