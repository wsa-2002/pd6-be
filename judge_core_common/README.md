# Judge Core - Common

This is the base implementation of judge core.

This project is expected to use with our home-modified `nsjail` project as base docker image.
Since the image contains Python 3.8, the implementation of judge core is in Python 3.8.

## WARNING

Since this project is intended to work as a SUBMODULE, please ONLY do relative import like this:

```python
from .. import parent_related
from . import related
```

and NOT

```python
import parent_related
from parent_related import related
```

so the imports will not break when this project is actually used by other projects.
