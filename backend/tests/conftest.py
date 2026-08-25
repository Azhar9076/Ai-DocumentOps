"""Point the test suite at an isolated database before the app is imported."""

import os
import tempfile

os.environ.setdefault(
    "DOCOPS_DATABASE_URL",
    "postgresql+psycopg2://docops:docops@localhost:5432/documentops_test",
)
os.environ.setdefault("DOCOPS_STORAGE_DIR", tempfile.mkdtemp(prefix="documentops-test-"))
