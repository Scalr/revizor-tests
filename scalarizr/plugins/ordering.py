import itertools
import typing as tp

from _pytest.python import Function


def pytest_collection_modifyitems(session, config, items: tp.List[Function]):
    sorted_items = []
    groups = itertools.groupby(items, key=lambda i: i.cls.__name__)
    for group_name, group_items in groups:
        def order_fn(i):
            assert hasattr(i.cls, 'order'), f'{i.cls.__name__}.order class attribute is missing'
            assert i.name in i.cls.order, f'Function {i.name} is not present in test order list'
            return i.cls.order.index(i.name)

        sorted_items.extend(sorted(group_items, key=order_fn))
    items[:] = sorted_items
