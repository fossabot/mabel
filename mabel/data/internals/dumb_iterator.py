"""
There's nothing clever here, it's just a dumb iterator wrapper
"""

class DumbIterator:
    def __init__(self, i):
        self._i = iter(i)

    def __next__(self):
        return next(self._i)
