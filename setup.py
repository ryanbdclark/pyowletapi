from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="pyowletapi",
    version="2025.4.10",
    description="Owlet baby monitor API wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ryanbdclark/pyowletapi",
    author="Ryan Clark",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="owlet, api, baby",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={"pyowletapi": ["py.typed"]},
    python_requires=">=3.10",
    install_requires=["aiohttp"],
)
