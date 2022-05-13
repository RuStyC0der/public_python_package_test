from typing import List, Dict

__version__ = '0.2.1'


def group_by_key(data: List[dict], key: str) -> Dict[str, list]:
    """
        data = [{'a': 123, 'b': 1, 'c': 2}, {'a': 123, 'b': 3, 'c': 4}, {'a': 456, 'b': 5, 'c': 6}]
        key = 'a'
        result:
        {123: [{'a': 123, 'b': 1, 'c': 2}, {'a': 123, 'b': 3, 'c': 4}], 456: [{'a': 456, 'b': 5, 'c': 6}]}
    """
    resp = {}
    for r in data:
        resp[r[key]] = resp.setdefault(r[key], [])
        resp[r[key]].append(r)
    return resp


def split_list_by_batches(lst: list, batch_size: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]
