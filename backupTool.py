import csv
import db.datastore as db
import os
import re
import shutil
import sqlite3 as lite
import tarfile
import time

TABLES = [
    ('hashmap', ['hash', 'filepath']),
    ('profile', ['id', 'serializedUserInfo']),
    ('listings', ['id', 'serializedListings']),
    ('keys', ['type', 'privkey', 'pubkey']),
    ('followers', ['id', 'serializedFollowers']),
    ('following', ['id', 'serializedFollowing']),
    ('messages', ['guid', 'handle', 'signed_pubkey', 'encryption_pubkey', 'subject', 'message_type', 'message', 'timestamp', 'avatar_hash', 'signature', 'outgoing']),
    ('notifications', ['guid', 'handle', 'message', 'timestamp', 'avatar_hash']),
    ('vendors', ['guid', 'ip', 'port', 'signedPubkey']),
    ('moderators', ['guid', 'signedPubkey', 'encryptionKey', 'encryptionSignature', 'bitcoinKey', 'bitcoinSignature', 'handle']),
    ('purchases', ['id', 'title', 'timestamp', 'btc', 'address', 'status', 'thumbnail', 'seller', 'proofSig']),
    ('sales', ['id', 'title', 'timestamp', 'btc', 'address', 'status', 'thumbnail', 'seller']),
    ('dht', ['keyword', 'id', 'value', 'birthday'])
]

# TODO: Add all files and directories to back up together with the database
# Ex: ['file', 'path/to/file2', ...]
FILES = []

def _getDatabase():
    Database = db.Database()
    return Database.DATABASE

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

def backup(tablesAndColumns, files, output=None):
    """Archives given tables and files in a single tar archive."""
    # Remove existing database files and re-make them
    if os.path.exists('backup'):
        shutil.rmtree('backup')
    os.makedirs('backup')
    _exportDatabaseToCsv(tablesAndColumns)

    # Archive files
    if not output:
        output = 'backup_{0}.tar.gz'.format(time.strftime('%Y-%m-%d'))
    with tarfile.open(output, 'w:gz') as tar:
        tar.add('backup')
        for f in files:
            tar.add(f)
        tar.close()

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
                        print 'Insert into {0}: {1}'.format(tableName, row)
                        print insertsql
                        cursor.execute(insertsql, row)


def restore(input, deleteTableDataFirst=False):
    """Restores files and tables of given archive."""
    # Remove existing database files if any
    if os.path.exists('backup'):
        shutil.rmtree('backup')

    # Unarchive files
    with tarfile.open(input, 'r:gz') as tar:
        tar.extractall()

    # Restore database files to the database
    if os.path.exists('backup'):
        files = ['backup/{0}'.format(f) for f in os.listdir('backup')]
        for f in files:
            _importCsvToTable(f, deleteTableDataFirst)

if __name__ == '__main__':
    print 'Backup tool works as a library.'
