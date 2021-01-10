from pyramid.config import Configurator


def configure(settings=None):
    if settings is None:
        settings = dict()

    config = Configurator(settings=settings)
    config.include(".models")
    config.include(".views")
    config.include(".tasks")

    return config


def application(global_config, **settings):
    return configure(settings).make_wsgi_app()
