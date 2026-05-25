import subprocess
import sys


def test_asgi_app_imports_in_fresh_process() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import app.main; print('ok')"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
