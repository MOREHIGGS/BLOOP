import sys
from pathlib import Path

# Setup runtime paths for Cython modules
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root / "Source"))
sys.path.insert(0, str(package_root / "Build" / "CythonModules"))

# Get version from setuptools-scm
try:
    from importlib.metadata import version
    __version__ = version("BLOOP")
except Exception:
    __version__ = "unknown"

