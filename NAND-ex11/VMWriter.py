FIELD = "FIELD"
CONST = "CONST"
ARG = "ARG"
LOCAL = "LOCAL"
STATIC = "STATIC"
THIS = "THIS"
THAT = "THAT"
POINTER = "POINTER"
TEMP = "TEMP"


class VMWriter:
    def __init__(self):
        self._vm = []

    def get_vm(self):
        return self._vm

    def write_push(self, segment, index):
        # writes a VM push command
        if segment == CONST:
            self._vm.append("\tpush constant " + str(index))
        if segment == ARG:
            self._vm.append("\tpush argument " + str(index))
        if segment == LOCAL:
            self._vm.append("\tpush local " + str(index))
        if segment == STATIC:
            self._vm.append("\tpush static " + str(index))
        if segment == THIS or segment == FIELD:
            self._vm.append("\tpush this " + str(index))
        if segment == THAT:
            self._vm.append("\tpush that " + str(index))
        if segment == POINTER:
            self._vm.append("\tpush pointer " + str(index))
        if segment == TEMP:
            self._vm.append("\tpush temp " + str(index))

    def write_pop(self, segment, index):
        # writes a VM push command
        if segment == CONST:
            self._vm.append("\tpop constant " + str(index))
        if segment == ARG:
            self._vm.append("\tpop argument " + str(index))
        if segment == LOCAL:
            self._vm.append("\tpop local " + str(index))
        if segment == STATIC:
            self._vm.append("\tpop static " + str(index))
        if segment == THIS or segment == FIELD:
            self._vm.append("\tpop this " + str(index))
        if segment == THAT:
            self._vm.append("\tpop that " + str(index))
        if segment == POINTER:
            self._vm.append("\tpop pointer " + str(index))
        if segment == TEMP:
            self._vm.append("\tpop temp " + str(index))

    def write_arithmetic(self, command):
        # writes a VM push command
        self._vm.append("\t" + command.lower())

    def write_label(self, label):
        self._vm.append("label " + label)

    def write_goto(self, label):
        self._vm.append("\tgoto " + label)

    def write_if(self, label):
        self._vm.append("\tif-goto " + label)

    def write_call(self, name, n_args):
        self._vm.append("\tcall " + name + " " + str(n_args))

    def write_function(self, name, n_locals):
        self._vm.append("\tfunction " + name + " " + str(n_locals))

    def write_return(self):
        self._vm.append("\treturn")
