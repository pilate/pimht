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

# Performance
The `chardet` module, used by default, is slow. Performance can be improved by also installing `cchardet` with:
```
$ pip install pimht[speedups]
```

This is aimed specifically at parsing Google Chrome generated snapshots as fast as possible, but feel free to report issues with MHTML files from other sources.