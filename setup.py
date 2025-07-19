#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="baozong-superagent",
    version="1.0.0",
    author="宝总",
    author_email="baozong@example.com",
    description="专业级AI助手 - 为全栈开发者定制的智能Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/baozong/superagent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "aiohttp>=3.8.0",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "python-dotenv>=0.19.0",
        "pydantic>=1.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-asyncio>=0.15.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
        ],
        "ai": [
            "openai>=1.0.0",
            "anthropic>=0.8.0",
        ],
        "vector": [
            "sentence-transformers>=2.2.0",
            "chromadb>=0.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "baozong-agent=start_baozong_agent:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
