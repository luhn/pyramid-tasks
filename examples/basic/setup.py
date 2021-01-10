from setuptools import setup, find_packages


REQUIRES = [
    'celery[redis]>=4,<5',
    'pyramid-tasks>=0.1,<0.2',
    'pyramid>=1.10,<2',
    'redis>=3.5,<4',
    'waitress>=1.4,<2',
]


setup(
    name='basicapp',
    packages=find_packages(),
    install_requires=REQUIRES,
    entry_points={
        'paste.app_factory': ['main=basicapp:application'],
    },
)
