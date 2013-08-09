from distutils.core import setup

setup(
    name='AzurePython3',
    version='0.1.0',
    author='Mathias Kahl',
    author_email='mathias.kahl@gmail.com',
    packages=['azurepython3'],
    scripts=[],
    url='http://pypi.python.org/pypi/AzurePython3/',
    license='LICENSE',
    description='Incomplete Windows Azure library for Python 3',
    long_description=open('README.md').read(),
    install_requires=[
        "requests >= 1.2.3"
    ],
)