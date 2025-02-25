# Add a column ''

import sys
import os

from psycopg2.errors import UniqueViolation

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "'/../..")
from common.lib.database import Database
from common.lib.logger import Logger

log = Logger(output=True)
try:
    import config
    db = Database(logger=log, dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD, host=config.DB_HOST, port=config.DB_PORT, sslmode=config.DB_SSLMODE, appname="4cat-migrate")
except (SyntaxError, ImportError, AttributeError) as e:
    import common.config_manager as config
    db = Database(logger=log, dbname=config.get('DB_NAME'), user=config.get('DB_USER'), password=config.get('DB_PASSWORD'), host=config.get('DB_HOST'), port=config.DB_PORT, sslmode=config.get('DB_SSLMODE'), appname="4cat-migrate")

# Add 'annotation_fields' column to datasets table.
print("  Checking if required columns exist... ", end="")
columns = [row["column_name"] for row in db.fetchall("SELECT column_name FROM information_schema.columns WHERE table_name = 'datasets'")]

if "annotation_fields" in columns:
	print("yes!\n")
else:
	print(" no, adding 'annotation_fields' column to datasets table\n")
	db.execute("ALTER TABLE datasets ADD COLUMN annotation_fields TEXT DEFAULT '' ")

# Make annotations table
print("  Checking if annotations table exist... ", end="")
annotations_table = db.fetchone("SELECT EXISTS ( SELECT FROM information_schema.tables WHERE table_name = 'annotations')")
if not annotations_table["exists"]:
	print("no, creating it now.")
	db.execute("""CREATE TABLE IF NOT EXISTS annotations (
					  key               text UNIQUE PRIMARY KEY,
					  annotations       text DEFAULT ''
					)
				""")
else:
	print("yes!")
