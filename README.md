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
    print(part.content_type, len(part.raw))
```

# Modifying

```python
import pimht

mhtml = pimht.from_filename("test.mhtml")
for part in mhtml.parts:
    if part.is_text:
        part.text = part.text.replace("Hello", "Goodbye")

with open("modified.mhtml", "wb") as f:
    f.write(mhtml.to_bytes())
```

# Performance
The `chardet` module, used by default, is slow. Performance can be improved by also installing `cchardet` and `pybase64` with:
```
$ pip install pimht[speedups]
```

This is aimed specifically at parsing Google Chrome generated snapshots as fast as possible, but feel free to report issues with MHTML files from other sources.