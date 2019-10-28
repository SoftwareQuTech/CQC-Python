def get_header(header_class, *args, **kwargs):
    """Construct and packs a given header"""
    hdr = header_class()
    hdr.setVals(*args, **kwargs)
    return hdr.pack()
