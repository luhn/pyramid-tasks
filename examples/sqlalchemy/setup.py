from setuptools import setup, find_packages


REQUIRES = [
    'celery[redis]~=5.2',
    'pyramid-tasks~=0.3.0',
    'pyramid~=2.0',
    'pyramid_tm~=2.5',
    'redis~=4.3',
    'SQLAlchemy~=1.4',
    'waitress~=2.1',
    'zope.sqlalchemy~=1.6',
]


setup(
    name='sqlalchemyapp',
    packages=find_packages(),
    install_requires=REQUIRES,
    entry_points={
        'paste.app_factory': ['main=sqlalchemyapp:application'],
    },
)
