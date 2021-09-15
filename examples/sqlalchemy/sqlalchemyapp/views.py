from pyramid.httpexceptions import HTTPBadRequest

from .models import Ledger


def includeme(config):
    config.add_route("append", "/append")
    config.add_view(append, route_name="append", renderer="string")
    config.add_route("total", "/total")
    config.add_view(total, route_name="total", renderer="string")


def append(context, request):
    """
    Append a value to the ledger.

    """
    try:
        value = int(request.params["value"])
    except KeyError:
        raise HTTPBadRequest("Must include `value`.")
    except ValueError:
        raise HTTPBadRequest("`value` must be an integer.")
    request.db.add(Ledger(amount=value))
    return "Done.\n"


def total(context, request):
    """
    Calculate the total.

    """
    result = request.defer_task("total_task").get()
    return f"{ result }\n"
