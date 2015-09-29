__author__ = 'marc'
from constants import DATA_FOLDER
import csv
import db.datastore as db
import errno
import os
import re
import shutil
import sqlite3 as lite
import tarfile
import time

_TABLES = {
	'hashmap': ['hash', 'filepath'],
	'profile': ['id', 'serializedUserInfo'],
	'listings': ['id', 'serializedListings'],
	'keys': ['type', 'privkey', 'pubkey'],
	'followers': ['id', 'serializedFollowers'],
	'following': ['id', 'serializedFollowing'],
	'messages': ['guid', 'handle', 'signed_pubkey', 'encryption_pubkey', 'subject', 'message_type', 'message', 'timestamp', 'avatar_hash', 'signature', 'outgoing'],
	'notifications': ['guid', 'handle', 'message', 'timestamp', 'avatar_hash'],
	'vendors': ['guid', 'ip', 'port', 'signedPubkey'],
	'moderators': ['guid', 'signedPubkey', 'encryptionKey', 'encryptionSignature', 'bitcoinKey', 'bitcoinSignature', 'handle'],
	'purchases': ['id', 'title', 'timestamp', 'btc', 'address', 'status', 'thumbnail', 'seller', 'proofSig'],
	'sales': ['id', 'title', 'timestamp', 'btc', 'address', 'status', 'thumbnail', 'seller'],
	'dht': ['keyword', 'id', 'value', 'birthday']
}

def _getDatabase():
	"""Retrieves the OpenBazaar database file."""
	Database = db.Database()
	return Database.DATABASE

def silentRemove(filename):
	"""Silently removes a file if it exists."""
	try:
		os.remove(filename)
	except OSError as e:
		if e.errno != errno.ENOENT: # ENOENT: no such file or directory
			raise

def _exportDatabaseToCsv(tablesAndColumns):
	"""Reads the database for all given tables and stores them as CSV files."""
	dbFile = _getDatabase()
	result = None
	with lite.connect(dbFile) as dbConnection:
		dbConnection.text_factory = str
		cursor = dbConnection.cursor()
		for table in tablesAndColumns:
			table_name = table[0]
			table_columns = ', '.join(table[1])
			data = cursor.execute("SELECT {0} FROM {1}".format(table_columns, table_name))
			fileName = 'table_{0}.csv'.format(table_name)
			filePath = os.path.join('backup', fileName)
			with open(filePath, 'wb') as f:
				writer = csv.writer(f)
				writer.writerow(table[1])
				writer.writerows(data)
	return result

def backupFiles(output=None):
	"""Archives OpenBazaar files in a single tar archive."""
	os.chdir(DATA_FOLDER)

	# Archive files
	files = os.listdir(DATA_FOLDER)
	if not output:
		output = 'backup_{0}.tar.gz'.format(time.strftime('%Y-%m-%d'))
	silentRemove(output)
	with tarfile.open(output, 'w:gz') as tar:
		for f in files:
			tar.add(f)
		tar.close()
	return 'Success'

def exportDatabase(tableList, removePrevious=False):
	"""Exports given tables to the OpenBazaar folder."""
	# Parse table list
	tableList = tableList.replace(' ', '').split(',')
	tablesAndColumns = []
	for table in tableList:
		if table in _TABLES:
			tablesAndColumns.append((table, _TABLES[table]))
		else:
			return 'ERROR, Table not found: {0}'.format(table)

	# Remove existing database files and re-make them
	if removePrevious and os.path.exists('backup'):
		shutil.rmtree('backup')
	if not os.path.exists('backup'):
		os.makedirs('backup')
	_exportDatabaseToCsv(tablesAndColumns)
	return 'Success'

def _importCsvToTable(fileName, deleteDataFirst=False):
	"""Imports given CSV file to the database."""
	tableName = re.search('table_(\w+).csv', fileName).group(1)
	dbFile = _getDatabase()
	with lite.connect(dbFile) as dbConnection:
		dbConnection.text_factory = str
		cursor = dbConnection.cursor()
		if deleteDataFirst:
			cursor.execute('DELETE FROM {0}'.format(tableName))
		with open(fileName, 'rb') as f:
			reader = csv.reader(f)
			header = True
			for row in reader:
				if header:
					header = False
					columns = ', '.join(['?' for column in row])
					insertsql = 'INSERT INTO {0} VALUES ({1})'.format(tableName, columns)
					rowlen = len(row)
				else:
					if len(row) == rowlen:
						cursor.execute(insertsql, row)


def restoreFiles(input, removePreviousDatabaseFiles=False):
	"""Restores files of given archive to OpenBazaar folder."""
	if not input:
		return 'Input path is needed'
	os.chdir(DATA_FOLDER)

	# Remove existing database files if any
	if removePreviousDatabaseFiles and os.path.exists('backup'):
		shutil.rmtree('backup')

	# Unarchive files
	with tarfile.open(input, 'r:gz') as tar:
		tar.extractall()

	return 'Success'

if __name__ == '__main__':
	print 'Backup tool works as a library.'

def importDatabase(deletePreviousData=False):
	"""Imports table files from the OpenBazaar folder."""
	# Restore database files to the database
	if os.path.exists('backup'):
		files = ['backup/{0}'.format(f) for f in os.listdir('backup')]
		for f in files:
			_importCsvToTable(f, deletePreviousData)
	return 'Success'
