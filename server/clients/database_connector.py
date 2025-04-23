"""
Module to handle slqite3 database connections.
"""

import sqlite3
import logging
import sys
import pickle

from pathlib import Path
from datetime import datetime


class DatabaseConnector:
    """
    Class to handle sqlite3 database connections via
    a single connection and cursor.
    """

    def __init__(self, database_filename):
        logging.info("DatabaseConnector initialising.")
        self.database_filename = database_filename
        self.databases_directory = Path(sys.argv[0]).parent / 'databases'
        self.conn = sqlite3.connect(self.databases_directory / database_filename)
        self.cursor = self.conn.cursor()
        logging.info("DatabaseConnector initialised.")

    def preview_data(self):
        """
        Method to preview the first 10 rows of the database
        and return data as a list of dictionaries.
        """
        logging.info("DatabaseConnector previewing data.")
        self.cursor.execute("SELECT * FROM data LIMIT 10")
        columns = [description[0] for description in self.cursor.description]
        data = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        logging.info("DatabaseConnector returning preview data.")
        return data

    def get_columns(self):
        """
        Method to get the columns of the database.
        """
        logging.info("DatabaseConnector getting columns.")
        self.cursor.execute("PRAGMA table_info(data)")
        columns = [row[1] for row in self.cursor.fetchall()]
        logging.info("DatabaseConnector returning columns.")
        return columns

    def get_total_documents(self):
        """
        Method to get the total number of documents in the database.
        """
        logging.info("DatabaseConnector getting total documents.")
        self.cursor.execute("SELECT COUNT(*) FROM data")
        total_documents = self.cursor.fetchone()[0]
        logging.info("DatabaseConnector returning total documents.")
        return total_documents

    def get_unenriched_documents(self, embedding_field, count):
        """
        Method to get the first n documents that are not
        enriched.
        """
        logging.info("DatabaseConnector getting unenriched documents.")
        self.cursor.execute(
            f"SELECT * FROM data WHERE \"{embedding_field}\" IS NULL LIMIT {count}"
        )
        columns = [description[0] for description in self.cursor.description]
        data = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        logging.info("DatabaseConnector returning unenriched documents.")
        return data

    def create_field_to_store_embeddings(self, field_name):
        """
        Method to create a field in the database to store
        embeddings.
        """
        logging.info("DatabaseConnector creating field to store embeddings.")
        if not field_name.endswith("_embedding"):
            field_name += "_embedding"
        self.cursor.execute(
            f"ALTER TABLE data ADD COLUMN \"{field_name}\" BLOB"
        )
        self.conn.commit()
        logging.info("DatabaseConnector created field to store embeddings.")
        return field_name

    def write_embedded_documents(self, documents, storage_field):
        """
        Method to write enriched documents to the database.
        """
        logging.info("DatabaseConnector writing enriched documents.")
        for document in documents:
            self.cursor.execute(
                f"UPDATE data SET \"{storage_field}\" = ? WHERE _id = ?",
                (document[storage_field], document["_id"]),
            )
        self.conn.commit()
        logging.info("DatabaseConnector wrote enriched documents.")

    def get_completed_document_count(self, storage_field):
        """
        Method to get the number of completed documents
        in the database.
        """
        logging.info("DatabaseConnector getting completed document count.")
        self.cursor.execute(
            f"SELECT COUNT(*) FROM data WHERE \"{storage_field}\" IS NOT NULL"
        )
        completed_document_count = self.cursor.fetchone()[0]
        logging.info("DatabaseConnector returning completed document count.")
        return completed_document_count

    def get_embeddings(self):
        """
        Method to get the embeddings from the database.
        """
        logging.info("DatabaseConnector getting embeddings.")
        self.cursor.execute("SELECT * FROM data")
        columns = [description[0] for description in self.cursor.description]
        embedding_field = next(
            (col for col in columns if col.endswith("_embedding")), None
        )
        if not embedding_field:
            logging.error("DatabaseConnector could not find embedding field.")
            raise ValueError("DatabaseConnector could not find embedding field.")
        
        self.cursor.execute(f"SELECT _id, \"{embedding_field}\" FROM data")
        data = self.cursor.fetchall()
        embeddings_dict = {}
        for row in data:
            id_val = row[0]
            embedding_blob = row[1]
            if embedding_blob is not None:
                try:
                    embedding = pickle.loads(embedding_blob)
                    embeddings_dict[id_val] = embedding
                except Exception as e:
                    logging.error(f"Error deserializing embedding for ID {id_val}: {e}")
                    embeddings_dict[id_val] = None
            else:
                embeddings_dict[id_val] = None
        logging.info("DatabaseConnector returning embeddings.")
        return embeddings_dict

    def get_data_by_id(self, id):
        """
        Method to get data by ID from the database, 
        except for the embedding field.
        """
        logging.info("DatabaseConnector getting data by ID.")
        self.cursor.execute("SELECT * FROM data WHERE _id = ?", (id,))
        columns = [description[0] for description in self.cursor.description]
        data = dict(zip(columns, self.cursor.fetchone()))
        embedding_field = next(
            (col for col in columns if col.endswith("_embedding")), None
        )
        if embedding_field:
            del data[embedding_field]            
        logging.info("DatabaseConnector returning data by ID.")
        return data

    def simple_query(self, field, query, operator):
        """
        Method to execure a simple query using a field, query, and 
        operator, which is one of equals, does not equal, contains,
        does not contain, and return maching ids.
        """
        logging.info("DatabaseConnector executing simple query.")
        if operator == "equals":
            self.cursor.execute(f"SELECT _id FROM data WHERE \"{field}\" = ?", (query,))
        elif operator == "not equals":
            self.cursor.execute(f"SELECT _id FROM data WHERE \"{field}\" != ?", (query,))
        elif operator == "contains":
            self.cursor.execute(f"SELECT _id FROM data WHERE \"{field}\" LIKE ?", (f"%{query}%",))
        elif operator == "not contains":
            self.cursor.execute(f"SELECT _id FROM data WHERE \"{field}\" NOT LIKE ?", (f"%{query}%",))
        else:
            logging.error("DatabaseConnector invalid operator for simple query.")
            raise ValueError("DatabaseConnector invalid operator for simple query.")
        
        ids = [row[0] for row in self.cursor.fetchall()]
        if not ids:
            return []
        logging.info("DatabaseConnector returning IDs from simple query.")
        return ids

class DatabaseCreator:
    """
    Class to create new sqlite3 database files from
    a list of dictionaries and list attributes for
    file selection.
    """

    def __init__(self):
        logging.info("DatabaseCreator initialising.")
        self.databases_directory = Path(sys.argv[0]).parent / 'databases'
        self.databases_directory.mkdir(parents=True, exist_ok=True)
        logging.info("DatabaseCreator initialised.")

    def list_databases(self):
        """
        Method to list all databases in the databases directory, 
        including name, row count, table names, and column information.
        Returns a list of dictionaries with detailed information about each database.
        """
        logging.info("DatabaseCreator listing databases with details.")
        databases = [f for f in self.databases_directory.iterdir() if f.is_file() and f.suffix == '.db']
        result = []
        
        for db_file in databases:
            db_info = {"name": db_file.name}
            
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                table_info = {}
                
                for table in tables:
                    table_name = table[0]
                    
                    if table_name == 'sqlite_sequence':
                        continue
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    row_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    table_info[table_name] = {
                        "columns": columns,
                        "row_count": row_count
                    }
                
                db_info["tables"] = table_info
                conn.close()
                
            except Exception as e:
                logging.error(f"Error getting details for {db_file.name}: {str(e)}")
                db_info["tables"] = {}
            
            result.append(db_info)
        
        logging.info("DatabaseCreator returning detailed list of databases.")
        return result

    def create_new_database(self, source_filename, data_list):
        """
        Method to create a new database file from a list of dictionaries.
        """
        logging.info("DatabaseCreator creating new database file.")
        filename = f"{source_filename.split('.')[0]}-{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
        db_path = self.databases_directory / filename

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if not data_list:
            logging.error("DatabaseCreator received empty data_list.")
            raise ValueError("DatabaseCreator received empty data_list.")

        columns = list(data_list[0].keys())
        columns_escaped = [f'"{col}"' for col in columns]  

        table_name = "data"
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                {', '.join([f"{col} TEXT" for col in columns_escaped])}
            )
        """
        cursor.execute(create_table_query)

        for data_row in data_list:
            processed_row = {}
            for k, v in data_row.items():
                if v is None or isinstance(v, (int, float, str, bytes)):
                    processed_row[k] = v
                else:
                    processed_row[k] = str(v)
            
            placeholders = ', '.join(['?'] * len(processed_row))
            insert_query = f"""
                INSERT INTO {table_name} ({', '.join(columns_escaped)}) 
                VALUES ({placeholders})
            """
            cursor.execute(insert_query, tuple(processed_row.values()))

        conn.commit()
        conn.close()

        logging.info("DatabaseCreator created file %s.", filename)
        return filename