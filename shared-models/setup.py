from setuptools import setup, find_packages

setup(
    name="shared-models",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
    ],
    description="Shared models for microservices integration",
    author="Your Name",
    author_email="your.email@example.com",
)
