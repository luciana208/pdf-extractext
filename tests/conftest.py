"""configuracion global: consul apagado y base de test separada para no tocar datos de desarrollo"""

import os

os.environ["CONSUL_ENABLED"] = "false"
os.environ.setdefault("DB_NAME", "pdf_test_db")
os.environ.setdefault("MONGO_CONNECT_RETRIES", "2")
