def get(query: str, object: dict):
    def _get(_query: list[str], c_object: dict):
        _q = _query.pop(0)
        data = c_object.get(_q)
        if isinstance(data, dict) and len(_query) != 0:
            return _get(_query, data)
        return data

    query_blocks = query.split(".")
    return _get(query_blocks, object)
