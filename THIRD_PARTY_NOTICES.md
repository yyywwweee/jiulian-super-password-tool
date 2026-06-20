# Third-party Notices

## CPython telnetlib.py

- File: `shared/backend/vendor/telnetlib_compat.py`
- Source: CPython 3.12 `Lib/telnetlib.py`
- License: Python Software Foundation License; see `shared/backend/vendor/LICENSE.PSF`
- Reason: Python 3.13+ removed stdlib `telnetlib`; this project vendors the Python 3.12 implementation to keep Windows/macOS builds independent of host Python stdlib availability.

