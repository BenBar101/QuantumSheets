from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="QuantumSheets",
    version="0.1.0",
    author="BenBar101",
    author_email="example@example.com",
    description="Render Qiskit quantum circuits as beautiful sheet music.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BenBar101/QuantumSheets",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "QuantumSheets": ["assets/*"],
    },
    install_requires=[
        "qiskit",
        "matplotlib"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
