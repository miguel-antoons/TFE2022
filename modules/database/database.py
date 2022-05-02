import mysql.connector
import os

from dotenv import load_dotenv


def get_cursor_connection():
    """
    Function makes a connection to a mysql database
    with connection information if finds in a environnement file
    ant returns the database connection and cursor

    Returns
    -------
    MySQLConnection, MySQLCursor
        Returns the database connection and cursor
    """
    # load the .env file
    load_dotenv()

    # connect to the database with values coming from the .env file
    db = mysql.connector.connect(
        host=os.getenv('HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('PASSWORD'),
        database=os.getenv('DATABASE'),
    )

    return db, db.cursor()


def close_connection(connection, cursor):
    """
    Function closes the database connection and cursor it
    receives as arguments.

    Parameters
    ----------
    connection : MySQLConnection
        the mysql database connection object
    cursor : MySQLCursor
        the mysql database cursor object
    """
    cursor.close()
    connection.close()
