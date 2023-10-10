# pimht
Python mhtml parser

# Installation
```
$ pip install pimht
```

# Example

```python

import pimht

mhtml = pimht.from_filename("test.mhtml")
for part in mhtml:
    print(part)

```