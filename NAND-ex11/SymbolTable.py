from functools import reduce

CLASS_KINDS = ["STATIC", "FIELD"]
SUBROUTINE_KINDS = ["ARG", "LOCAL"]
STATIC = "STATIC"
FIELD = "FIELD"
ARG = "ARG"
LOCAL = "LOCAL"
TYPE_INDEX = 0
KIND_INDEX = 1
NUM_INDEX = 2


class SymbolTable:
    def __init__(self):
        self._table = {}

    def start_subroutine(self):
        self._table = {k: v for k, v in self._table.items() if
                       v[KIND_INDEX] in CLASS_KINDS}

    def define(self, name, type, kind):
        if name in self._table:
            raise SyntaxError(
                "A variable with name '" + name + "' already exists")
        self._table[name] = (type, kind, self.var_count(kind))

    def var_count(self, kind):
        return reduce(lambda x, y: x + (1 if self._table[y][KIND_INDEX] == kind else 0),
                      self._table, 0)

    def kind_of(self, name):
        if name in self._table:
            return self._table[name][KIND_INDEX]
        return None

    def type_of(self, name):
        if name in self._table:
            return self._table[name][TYPE_INDEX]
        return None

    def index_of(self, name):
        if name in self._table:
            return self._table[name][NUM_INDEX]
        return None
