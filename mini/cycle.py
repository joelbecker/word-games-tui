from typing import Iterable


class Cycle(Iterable):
    def __init__(self, iterable: Iterable):
        self.data = list(iterable)
        self.index = 0

    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        return iter(self.data)
    
    def __next__(self):
        return self.next()

    def next(self):
        result = self.data[self.index]
        self.index = (self.index + 1) % len(self.data)
        return result
    
    def prev(self):
        self.index = (self.index - 1) % len(self.data)
        return self.data[self.index]
    
    def cur(self):
        return self.data[self.index]

    def first(self):
        return self.data[0]
    
    def last(self):
        return self.data[-1]