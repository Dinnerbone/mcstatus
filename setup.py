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
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)