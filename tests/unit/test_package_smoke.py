from voxcodex import __version__
from voxcodex.cli import app


def test_package_exports_version_and_cli():
    assert __version__ == "0.1.0"
    assert app.info.name == "voxcodex"
