import mysql.connector
import os

from tqdm import tqdm
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
        database=os.getenv('DATABASE')
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


def insert_noise(psd_data):
    """
    Function inserts and/or updates the noise psd value of a set of files.
    The files it modifies depends on the values received in the
    psd_data array it receives as argument.

    Parameters
    ----------
    psd_data : array
        Array which contains dictionnaries. Each dictionnary is composed of
        the psd value, a system_id and the start time of the file.
    """
    connection, cursor = get_cursor_connection()
    print('Saving values in the database...')

    # sql query to update the database values
    sql_query = (
        "UPDATE file "
        "SET psd = %(psd)s "
        "WHERE "
        "system_id = %(system_id)s "
        "AND start = %(time)s"
    )

    # execute and commit the values
    try:
        cursor.executemany(sql_query, psd_data)
        connection.commit()
    except mysql.connector.Error as e:
        connection.rollback()
        print(e)

    close_connection(connection, cursor)


def insert_calibrator(psd_data):
    """
    Function inserts and/or updates the calibrator psd value of a set of files.
    The files it modifies depends on the values received in the
    psd_data array it receives as argument.

    Parameters
    ----------
    psd_data : array
        Array which contains dictionnaries. Each dictionnary is composed of
        the psd value, a system_id and the start time of the file.
    """
    connection, cursor = get_cursor_connection()
    print('Saving values in the database...')

    # sql query to update the database values
    sql_query = (
        "UPDATE file "
        "SET calibrator = %(psd)s "
        "WHERE "
        "system_id = %(system_id)s "
        "AND start = %(time)s"
    )

    # execute and commit the values
    try:
        cursor.executemany(sql_query, psd_data)
        connection.commit()
    except mysql.connector.Error as e:
        connection.rollback()
        print(e)

    close_connection(connection, cursor)


def get_station_ids(stations):
    """
    Function receives location codes ('BEHAAC', 'BEGRIM', ...) as argument
    and returns the system_id(s) it finds for a location code (i.e. suppose
    'BEGRIM' has 2 systems with ids 1 and 2, it will generate a dictionnary
    as follows: {
        'BEGRIM': {
            '1': 1,
            '2': 2,
        }
    })

    Parameters
    ----------
    stations : array
        array of the string location codes

    Returns
    -------
    array
        array of dictionnaries containing all the system ids of the asked
        location codes.
        The system ids are grouped by location codes and by antenna.
    """
    arguments = ['%s' for i in range(len(stations))]
    ids = {}
    connection, cursor = get_cursor_connection()

    # get system_id for each location and antenna
    sql_query = (
        "SELECT system.id, location_code, antenna\n"
        "FROM `system`, location\n"
        "WHERE location.id = system.location_id AND location_code in (%s);"
        % ', '.join(arguments)
    )

    cursor.execute(sql_query, tuple(stations))

    print('Structuring data received from the database...')
    # structure the system id's first by location code and then by antenna
    for (sys_id, loc_code, antenna) in tqdm(cursor):
        if loc_code not in ids:
            ids[loc_code] = {}

        ids[loc_code][str(antenna)] = sys_id

    close_connection(connection, cursor)

    return ids
