from setuptools import setup, find_packages


REQUIRES = [
    'celery[redis]~=4.4',
    'pyramid-tasks~=0.2.0',
    'pyramid~=1.10',
    'pyramid_tm~=2.4',
    'redis~=3.5',
    'SQLAlchemy~=1.3.22',
    'waitress~=1.4',
    'zope.sqlalchemy~=1.3',
]


setup(
    name='sqlalchemyapp',
    packages=find_packages(),
    install_requires=REQUIRES,
    entry_points={
        'paste.app_factory': ['main=sqlalchemyapp:application'],
    },
)
