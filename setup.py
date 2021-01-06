from setuptools import setup, find_packages


VERSION = '0.1.0'
CLASSIFIERS = [
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Framework :: Pyramid',
    'Development Status :: 4 - Beta',
]


REQUIRES = [
    'pyramid>=1.9,<2',
    'celery>=4,<5',
    'venusian',
]
EXTRAS_REQUIRE = {
    'testing': ['pytest>=6,<7'],
}

DESCRIPTION = (
    'Bring parity to Pyramid and Celery by creating a full Pyramid '
    'application in the Celery worker and providing a request object for each '
    'task.'
)


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='pyramid-tasks',
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/luhn/pyramid-tasks/',
    author='Theron Luhn',
    author_email='theron@luhn.com',
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=REQUIRES,
    extras_require=EXTRAS_REQUIRE,
)
