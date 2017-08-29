Before:

```python
class A:
    __slots__ = [
        'foo',
        'bar',
    ]

    def __init__(self):
        self.foo = 1
        self.bar = 2


class B(A):
    __slots__ = A.__slots__ + [
        'baz',
    ]

    def __init__(self):
        super().__init__()
        self.baz = 3
```

After:

```python
import slot  # Alternatively: from slot import slots

class A:

      @slot.s
      def __init__(self):
          self.foo = 1
	  self.bar = 2


class B(A):

      @slot.s
      def __init__(self):
          super().__init__()
          self.baz = 3
```

Inspired by [attrs](http://www.attrs.org).
