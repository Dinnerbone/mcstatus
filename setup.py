from distutils.core import setup
import sys
PY2 = sys.version_info[0] == 2

install_requires = [
    'six'
]

if PY2:
    install_requires.append('dnspython')
else:
    install_requires.append('dnspython3')

tests_require = [
    'mock'
]

setup(
    name='mcstatus',
    version='2.1',
    author='Nathan Adams',
    author_email='dinnerbone@dinnerbone.com',
    url='https://pypi.python.org/pypi/mcstatus',
    packages=['mcstatus', 'mcstatus.protocol'],
    description='A library to query Minecraft Servers for their status and capabilities.',
    install_requires=install_requires,
    tests_require=tests_require,
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