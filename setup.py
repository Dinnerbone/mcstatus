from distutils.core import setup

setup(
    name='mcstatus',
    version='2.0dev',
    author='Nathan Adams',
    author_email='dinnerbone@dinnerbone.com',
    url='https://pypi.python.org/pypi/mcstatus',
    packages=['minecraft_query',],
    description='A library to query Minecraft Servers for their status and capabilities.',
    install_requires=['six'],
    tests_require=['mock'],
)