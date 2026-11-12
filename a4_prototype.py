"""
Prototype (Clone)

Structure:
1. Prototype Interface: declare clone abstract method
2. Concrete Prototype: implement clone method
3. Client: follow interface
4. Prototype Registry (Optional): access to frequently-used objects
"""

import copy
from abc import ABC, abstractmethod


class Prototype(ABC):

    @abstractmethod
    def clone(self):
        pass


class ConnectionPool:
    ...


class Report(Prototype):
    def __init__(self, name):
        self.name = name
        self.filters = []
        self.metadata = {}
        self.connection_pool = None

    def clone(self):
        memo = {id(self.connection_pool): self.connection_pool}
        return copy.deepcopy(self, memo)


def run_tests():
    r1 = Report("test")
    r1.filters = [1, 2, 3]
    r1.metadata = {
        "author": {
            "name": "Ali"
        }
    }
    r1.connection_pool = ConnectionPool()

    r2 = r1.clone()
    r2.filters.append(4)
    r2.metadata["author"]["name"] = "Reza"

    assert r1 is not r2
    assert r1.filters is not r2.filters
    assert r1.metadata is not r2.metadata

    assert len(r1.filters) == 3
    assert len(r2.filters) == 4

    assert r1.metadata["author"]["name"] == "Ali"
    assert r2.metadata["author"]["name"] == "Reza"

    assert r1.connection_pool is r2.connection_pool

    print("OK!")


if __name__ == "__main__":
    run_tests()
