from setuptools import setup, find_packages


REQUIRES = [
    'celery[redis]~=5.2',
    'pyramid-tasks~=0.3',
    'pyramid~=2.0',
    'redis~=4.3',
    'waitress~=2.1',
]


setup(
    name='basicapp',
    packages=find_packages(),
    install_requires=REQUIRES,
    entry_points={
        'paste.app_factory': ['main=basicapp:application'],
    },
)
