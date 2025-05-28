from setuptools import setup, find_packages

setup(
    name="mediavault-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "jinja2==3.1.2",
        "python-dotenv==1.0.0",
        "python-multipart==0.0.6",
        "pydantic==2.4.2",
        "pydantic-settings==2.0.3",
        "apscheduler==3.10.1",
        "httpx==0.25.2",
        "typer>=0.9.0",
        "rich>=13.7.0",
        "click>=8.1,<8.2",
    ],
    entry_points={
        "console_scripts": [
            "mvm=app.cli:cli_app",
            "mvm-service=app.main:main",
        ],
    },
    python_requires=">=3.8",
) 