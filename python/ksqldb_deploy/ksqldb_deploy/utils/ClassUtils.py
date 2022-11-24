def autoRepr(obj):
    try:
        items = ("%s = %r" % (k, v) for k, v in obj.__dict__.items())
        return "<%s: {%s}." % (obj.__class__.__name__, ', '.join(items))
    except AttributeError:
        return repr(obj)
