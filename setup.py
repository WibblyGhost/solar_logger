"""
Setup instructions for package management
"""
import setuptools

PACKAGE_NAME = "Solar-Logger"
PACKAGE_DIR = "."
EXCLUDED_PACKAGES = ["*tests*"]
VERSION = "1.0.0"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author="Zach Sanson",
    author_email="zac@sanson.co.nz",
    description="MQTT to Influx DB converter for Outback solar controller",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/WibblyGhost/solar_logger",
    project_urls={
        "Bug Tracker": "https://github.com/WibblyGhost/solar_logger/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": PACKAGE_DIR},
    packages=setuptools.find_packages(where=PACKAGE_DIR, exclude=EXCLUDED_PACKAGES),
    python_requires=">=3.10",
    install_requires=[
        "influxdb_client==1.20.0",
        "paho_mqtt==1.5.1",
        "pymate @ git+https://github.com/WibblyGhost/pymate.git@feature/python3",
        "Rx~=3.2.0",
        "pytz~=2021.1",
    ],
)
