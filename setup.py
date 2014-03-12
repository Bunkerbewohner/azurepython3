from distutils.core import setup

setup(
    name='azurepython3',
    version='1.7.6',
    author='Mathias Kahl',
    author_email='mathias.kahl@gmail.com',
    packages=['azurepython3'],
    scripts=[],
    url='http://pypi.python.org/pypi/azurepython3/',
    download_url='https://github.com/Bunkerbewohner/azurepython3',
    license='MIT License',
    description='Incomplete Windows Azure library for Python 3',
    long_description=open('README.md').read(),
    install_requires=[
        "requests >= 1.2.3"
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3'
    ]
)