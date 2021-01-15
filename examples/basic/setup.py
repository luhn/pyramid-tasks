from setuptools import setup, find_packages


REQUIRES = [
    'celery[redis]~=4.4',
    'pyramid-tasks~=0.2',
    'pyramid~1.10',
    'redis~=3.5',
    'waitress~=1.4',
]


setup(
    name='basicapp',
    packages=find_packages(),
    install_requires=REQUIRES,
    entry_points={
        'paste.app_factory': ['main=basicapp:application'],
    },
)
