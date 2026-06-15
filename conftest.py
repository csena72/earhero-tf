import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Los tests usan SQLite en memoria (rápido, sin servicios externos).
# Debe setearse ANTES de importar earhero.db / earhero.api.
os.environ.setdefault("DATABASE_URL", "sqlite://")
