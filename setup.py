from setuptools import find_packages, setup

VERSION = "0.2.2"
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Framework :: Pyramid",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Programming Language :: Python",
    "Topic :: Software Development :: Object Brokering",
]


REQUIRES = [
    "celery>=4,<6",
    "pyramid>=1.9,<2",
    "venusian >= 1.0",
    "zope.interface >= 3.8.0",
]
EXTRAS_REQUIRE = {
    "testing": [
        "pytest~=6.1",
    ],
    "linting": [
        "black==20.8b1",
        "flake8~=3.8.4",
        "isort~=5.6",
    ],
}

DESCRIPTION = (
    "Bring parity to Pyramid and Celery by creating a full Pyramid "
    "application in the Celery worker and providing a request object for each "
    "task."
)


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="pyramid-tasks",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/luhn/pyramid-tasks/",
    author="Theron Luhn",
    author_email="theron@luhn.com",
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=REQUIRES,
    extras_require=EXTRAS_REQUIRE,
)
