#!python

from setuptools import setup

# with open('README.rst') as rm:
#     long_description = rm.read()

setup(
    name='mangadl',
    version='0.0.1a',
    author="alethiophile",
    author_email="tomdicksonhunt@gmail.com",
    description="Multi-site manga downloader",
    # long_description=long_description,
    # long_description_content_type='text/x-rst',
    license='MIT',
    packages=['mangadl'],
    # url="https://github.com/alethiophile/qtoml",
    install_requires=['click'],
    python_requires='~=3.6',
    # classifiers=(
    #     "Programming Language :: Python :: 3",
    #     "Operating System :: OS Independent",
    #     "License :: OSI Approved :: MIT License",
    #     "Topic :: Software Development :: Libraries :: Python Modules"
    # )
)
