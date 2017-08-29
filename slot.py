import ast
import sys


def slots(initfunc):
    """An __init__ function decorator."""
    frame = sys._getframe(1)

    assert "__slots__" not in frame.f_locals, "__slots__ already declared"

    names = set()
    _add_slots(names, frame, initfunc)
    slots = tuple(sorted(names))
    frame.f_locals["__slots__"] = slots

    return initfunc


def _add_slots(names, frame, initfunc):
    code = initfunc.__code__

    with open(code.co_filename) as f:
        rootnode = ast.parse(f.read(), code.co_filename)

    for node in ast.walk(rootnode):
        if isinstance(node, ast.FunctionDef) and node.lineno == code.co_firstlineno:
            funcnode = node
            break
    else:
        raise Exception("{} not found in {} at line {}".format(initfunc, rootnode, code.co_firstlineno))

    def add_self_attribute_names(node):
        if isinstance(node, ast.Attribute):
            if node.value.id == "self":
                names.add(node.attr)
        elif isinstance(node, ast.Tuple):
            for e in node.elts:
                add_self_attribute_names(e)

    def find_class(top):
        for x in ast.iter_child_nodes(top):
            if isinstance(x, ast.ClassDef):
                if funcnode in ast.iter_child_nodes(x):
                    return x

            x = find_class(x)
            if x:
                return x

    def handle_super_call():
        classnode = find_class(rootnode)
        if not classnode:
            raise Exception("Class definition containing {} not found in {}", initfunc, rootnode)

        for b in classnode.bases:
            if not isinstance(b, ast.Name):
                raise Exception("Base class expression not supported")

            try:
                base = frame.f_locals[b.id]
            except KeyError:
                base = frame.f_globals[b.id]

            try:
                names.update(getattr(base, "__slots__"))
            except AttributeError:
                raise Exception("Base class {} does not have __slots__".format(base))

    for node in ast.walk(funcnode):
        if isinstance(node, ast.AnnAssign):
            add_self_attribute_names(node.target)

        if isinstance(node, ast.Assign):
            for x in node.targets:
                add_self_attribute_names(x)

        if (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and
                isinstance(node.func.value, ast.Call) and
                isinstance(node.func.value.func, ast.Name) and
                node.func.value.func.id == "super" and
                node.func.attr == "__init__"):
            handle_super_call()


# Alternative spelling:
#
#     import slot
#     @slot.s
#
s = slots


if __name__ == "__main__":
    import random

    class EmptyClass:
        __slots__ = ()

    class BaseClass(EmptyClass):

        @slots
        def __init__(self):
            super().__init__()
            self.foo = 0

    class MiddleClass(BaseClass):
        __slots__ = BaseClass.__slots__

    class SubClass(MiddleClass):

        @slots
        def __init__(self, baz=2):
            if random.random() <= 1:
                self.baz, dummy = baz, Ellipsis
                dummy = dummy

                if random.random() < 0:
                    self.bar = 1
                    return

            super().__init__()

    class UselessClass(SubClass):
        __slots__ = SubClass.__slots__

    x = UselessClass()
    assert x.__slots__ == ("bar", "baz", "foo")

    assert x.foo == 0

    try:
        x.bar
    except AttributeError:
        pass
    else:
        assert False
    x.bar = None

    assert x.baz == 2

    try:
        x.quux = 3
    except AttributeError:
        pass
    else:
        assert False
