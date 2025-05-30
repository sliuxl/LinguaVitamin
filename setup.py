from setuptools import setup, find_packages

setup(
    name="LinguaVitamin",
    version="0.1.0",
    description="A daily multilingual language learning tool with news or academic (arXiv) content.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.25.1",
        "transformers>=4.0.0",
        "beautifulsoup4",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "linguavitamin=lingua_vitamin.main:main",
        ],
    },
)
