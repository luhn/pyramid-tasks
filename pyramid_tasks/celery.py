from celery import Celery, signals
from pyramid.paster import get_app

from . import set_global_app

celery = Celery(autofinalize=False)


def add_preload_arguments(parser):
    parser.add_argument(
        "-i", "--ini", default=None, help="Paste ini configuration file."
    )
    parser.add_argument(
        "--ini-var",
        default=None,
        help="Comma separated list of key=value to pass to ini.",
    )


celery.user_options["preload"].add(add_preload_arguments)


@signals.user_preload_options.connect
def on_preload_parsed(options, **kwargs):
    """
    Load Pyramid application.

    """
    ini_location = options["ini"]
    ini_vars = options["ini_var"]
    if ini_location is None:
        print("You must provide the --ini argument")
        exit(-1)

    options = {}
    if ini_vars is not None:
        for pairs in ini_vars.split(","):
            key, value = pairs.split("=")
            options[key] = value

    set_global_app(celery)
    # We don't do anything with this, just want to trigger configuration.
    print(ini_location)
    get_app(ini_location, options=options)
