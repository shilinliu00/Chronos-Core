import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="chronos-core",
    version="0.1.0",
    author="Shilin Liu",  
    author_email="sliu114@stevens.edu", 
    description="A high-precision temporal feature extraction engine for non-linear cyclic patterns.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shilinliu00/chronos-core", 
    project_urls={
        "Bug Tracker": "https://github.com/shilinliu00/chronos-core/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[],
)
