from setuptools import setup


VERSION = '0.1.0',
REQUIRES = [
    'pyramid>=1.9,<2',
    'celery>=4,<5',
    'venusian',
]
CLASSIFIERS = [
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Framework :: Pyramid',
    'Development Status :: 4 - Beta',
]


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='pyramid-tasks',
    version=VERSION,
    description='Celery-powered tasks for Pyramid applications.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/luhn/pyramid-tasks/',
    author='Theron Luhn',
    author_email='theron@luhn.com',
    classifiers=CLASSIFIERS,
    py_modules=['pyramid_tasks'],
    python_requires='>=3.6',
    install_requires=REQUIRES,
)
