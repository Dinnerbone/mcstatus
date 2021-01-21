from setuptools import setup

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

with open("test-requirements.txt") as f:
    tests_require = f.read().splitlines()
    tests_require.pop(0)  # remove '-r requirements.txt' line

setup(
    name="mcstatus",
    version="5.1.1",
    author="Nathan Adams",
    author_email="dinnerbone@dinnerbone.com",
    url="https://pypi.python.org/pypi/mcstatus",
    packages=["mcstatus", "mcstatus.protocol", "mcstatus.scripts"],
    description="A library to query Minecraft Servers for their status and capabilities.",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    tests_require=tests_require,
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    entry_points="""
        [console_scripts]
        mcstatus=mcstatus.scripts.mcstatus:cli
    """,
    project_urls={
        "Source": "https://github.com/Dinnerbone/mcstatus",
    },
)
