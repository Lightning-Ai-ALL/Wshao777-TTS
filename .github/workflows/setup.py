from setuptools import setup, find_packages

setup(
    name="lightning-ai-all",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pywin32",
        "wmi",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "lightning-start = control_tower.main:start"
        ]
    }
)
