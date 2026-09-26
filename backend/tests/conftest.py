"""Point the test suite at an isolated test database before the app is imported."""

import os
import tempfile

test_db_dir = tempfile.mkdtemp(prefix="documentops-test-")
test_db_path = os.path.join(test_db_dir, "test.db")

# Use sqlite for fast, isolated test suite execution unless overridden
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{test_db_path.replace(chr(92), '/')}",
)
os.environ.setdefault(
    "DOCOPS_DATABASE_URL",
    f"sqlite:///{test_db_path.replace(chr(92), '/')}",
)
os.environ.setdefault("DOCOPS_STORAGE_DIR", test_db_dir)
