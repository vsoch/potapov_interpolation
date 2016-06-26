from setuptools import setup, find_packages

setup(
   
    # Application name:
    name='potapov',

    # Version number (initial):
    version='0.1',
    description='Treating feedback with delays in quantum systems',

    # Author and contributors
    author='Gil Tabak',
    author_email='tabak.gil@gmail.com',

    packages=find_packages(),

    # Details
    license='GNU',
    url='https://github.com/tabakg/potapov_interpolation',

    # Dependencies
    install_requires=[
        'matplotlib',
        'sympy',
        'numpy',
        'QNET==1.4.1',
    ],
    dependency_links = [
        'git+git@github.com:mabuchilab/QNET.git#egg=QNET-1.4.1',
    ],
    zip_safe=False

    )
