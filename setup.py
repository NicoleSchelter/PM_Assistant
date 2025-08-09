#!/usr/bin/env python3
"""
Setup script for PM Analysis Tool.

This script provides a simple way to install the PM Analysis Tool
and make it available as a command-line tool.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pm-analysis-tool",
    version="1.0.0",
    author="PM Analysis Tool Team",
    author_email="team@pm-analysis-tool.com",
    description="A comprehensive project management document analysis tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pm-analysis-tool/pm-analysis-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pm-analysis=main:cli",
            "pma=main:cli",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.md"],
        "learning": ["modules/*.md"],
    },
    zip_safe=False,
)