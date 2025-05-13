from setuptools import setup, find_packages

setup(
    name="devtooling_labels",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "requests>=2.31.0",
        "pyoso>=0.1.0",
        "google-generativeai>=0.3.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
) 