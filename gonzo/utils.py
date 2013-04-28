def last_index(list_, value):
    """ last_index(list, value) -> integer

    Analogous to list.index, but returns the last index rather than the first
    Raises ValueError if the value is not present.
    """

    found = None
    for index, val in enumerate(list_):
        if val == value:
            found = index
    if found is None:
        raise ValueError("{} is not in list {}".format(value, list_))
    return found
