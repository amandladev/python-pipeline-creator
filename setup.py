#!/usr/bin/env python3
"""
Setup script for Pipeline Creator CLI
"""

from setuptools import setup, find_packages

# Read README file for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Pipeline Creator CLI - A tool for setting up CI/CD pipelines on AWS"

setup(
    name="pipeline-creator",
    version="0.1.0",
    author="Sergio Reyes",
    author_email="sreyescurotto@gmail.com",
    description="A CLI tool for creating and managing CI/CD pipelines on AWS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amandladev/python-pipeline-creator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "colorama>=0.4.4",
        "rich>=13.0.0",
        "boto3>=1.26.0",
        "aws-cdk-lib>=2.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pipeline=pipeline_creator.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)