import mysql.connector

from . import database as db
from datetime import timezone


# TODO : insert or update
def insert_psd(psd_data):
    """
    Function inserts and/or updates the noise psd value of a set of files.
    The files it modifies depends on the values received in the
    psd_data array it receives as argument.

    Parameters
    ----------
    psd_data : array
        Array which contains dictionaries. Each dictionary is composed of
        the psd value, a system_id and the start time of the file.

    Returns
    -------
    boolean
        Returns True on success, False on fail
    """
    connection, cursor = db.get_cursor_connection()
    print('Saving values in the database...')

    # sql query to update the database values
    sql_query = (
        "UPDATE file\n"
        "SET\n"
        "   noise = %(noise_psd)s,\n"
        "   calibrator = %(calibrator_psd)s\n"
        "WHERE\n"
        "   system_id = %(system_id)s\n"
        "   AND start = %(time)s\n"
    )

    # execute and commit the values
    try:
        cursor.executemany(sql_query, psd_data)
        connection.commit()
        return_value = True
    except mysql.connector.Error as e:
        connection.rollback()
        print(e)
        return_value = False

    db.close_connection(connection, cursor)
    return return_value


# TODO : insert or update
def insert_calibrator(psd_data):
    """
    Function inserts and/or updates the calibrator psd value of a set of files.
    The files it modifies depends on the values received in the
    psd_data array it receives as argument.

    Parameters
    ----------
    psd_data : array
        Array which contains dictionaries. Each dictionary is composed of
        the psd value, a system_id and the start time of the file.

    Returns
    -------
    boolean
        Returns True on success, False on fail
    """
    connection, cursor = db.get_cursor_connection()
    print('Saving values in the database...')

    # sql query to update the database values
    sql_query = (
        "INSERT INTO psd (system_id, start, calibrator)\n"
        "VALUES (%(system_id)s, %(time)s, %(calibrator)s)\n"
        "ON DUPLICATE KEY UPDATE\n"
        "noise = VALUES(calibrator)\n"
    )

    # execute and commit the values
    try:
        cursor.executemany(sql_query, psd_data)
        connection.commit()
        return_value = True
    except mysql.connector.Error as e:
        connection.rollback()
        print(e)
        return_value = False

    db.close_connection(connection, cursor)
    return return_value


# TODO
def get_previous_noise_psd(stations, start_date, end_date):
    """
    Function gets last inserted psd values from the database. Then
    number of psd values returned depends on the 'limit' arg.
    It is possible to only get psd value from specific stations,
    this is done by setting the get_all flag to false and pass
    and array with the system_ids to select psd values from.
    Note than if the get_all value is set to True, the limit  and
    station args will be ignored.

    Parameters
    ----------
    stations : list, optional
        list of the station ids to get psd values from, by default []
    get_all : bool, optional
        determines whether to get all the psd values from the table or not,
        by default True
    limit : int, optional
        limit of values per station, is multiplied by the length of the
        stations list, by default 150

    Returns
    -------
    dict
        a dictionary where the system ids are the keys and the values are
        lists of psd values
    """
    arguments = ['%s' for i in range(len(stations))]
    sql_args = [start_date, end_date] + stations.items()
    psd = {}
    connection, cursor = db.get_cursor_connection()

    # get the last noise psd values and system_id from the database
    sql_query = (
        "SELECT\n"
        "   system_id,\n"
        "   DATE_FORMAT(start, '%Y-%m-%%d %H:%%i') as start,\n"
        "   noise\n"
        "FROM psd\n"
        "WHERE noise is not null\n"
        "AND start >= %s\n"
        "AND start < %s\n"
    )

    sql_query += (
        "AND system_id in (%s)\n"
        % ', '.join(arguments)
    )

    # order by statement in order to get the last psd values
    sql_query += "ORDER BY file.precise_start\n"

    cursor.execute(sql_query, tuple(sql_args))

    # structure the data received from the database into a dictionary of
    # arrays
    for (sys_id, start, psd_val) in cursor:
        if sys_id not in psd:
            psd[sys_id] = {}

        if start not in psd[sys_id].keys():
            psd[sys_id][start] = []

        psd[sys_id][start].append(psd_val)

    db.close_connection(cursor, connection)

    return psd


# TODO
def get_previous_all_psd(stations, start_date, end_date, interval):
    """
    Function gets the last calibrator psd value from the database
    for each station.
    If the get_all flag is set to False, only the calibrator psd
    values from the stations specified in the stations array will
    be returned.

    Parameters
    ----------
    stations : list, optional
        List of stations to get calibrator psd from. This list is
        ignored if get_all is set to True, by default []
    get_all : bool, optional
        determines whether to get the last psd value from all the
        stations or only the stations specified in the stations
        list, by default True

    Returns
    -------
    dict
        a dictionary where the system ids are the keys and the values are
        the calibrator psd values
    """
    arguments = ['%s' for i in range(len(stations))]
    sql_args = [
        '%Y-%m-%d %H:%i',
        start_date.strftime('%Y-%m-%d %H:%M'),
        end_date.strftime('%Y-%m-%d %H:%M')
    ] + stations
    sql_args.append(interval)
    psd = {}
    connection, cursor = db.get_cursor_connection()

    # get the last calibrator psd value for the requested systems (stations)
    sql_query = (
        "SELECT\n"
        "   system_id,\n"
        "   DATE_FORMAT(start, %s) as start,\n"
        "   calibrator,\n"
        "   noise\n"
        "FROM file\n"
        "WHERE (\n"
        "   calibrator is not null\n"
        "   OR noise is not null\n"
        ")\n"
        "AND start >= %s\n"
        "AND start < %s\n"
    )

    # filter system ids if asked
    sql_query += (
        "AND system_id in (%s)\n"
        % ', '.join(arguments)
    )

    # https://stackoverflow.com/questions/34270918/mysql-select-interval-of-every-2-hours-from-timestamp-column
    sql_query += (
        "GROUP BY\n"
        "   system_id,\n"
        "   DATE(start),\n"
        "   HOUR(start),\n"
        "   MINUTE(start) DIV %s\n"
    )

    cursor.execute(sql_query, tuple(sql_args))

    # structure the data received from the database into a dictionary of
    # arrays
    for (sys_id, start, psd_cal, psd_noise) in cursor:
        if sys_id not in psd:
            psd[sys_id] = {}

        psd[sys_id][start] = {
            "noise": psd_noise,
            "calibrator": psd_cal
        }

    db.close_connection(cursor, connection)

    return psd


def get_file_by_interval(stations, interval):
    """
    Function gets files that contain the interval passed as argument
    and were produced by one of the systems passed in the stations
    argument, from the database.
    It then structures all that data in a dict where the first layer
    keys are the location codes and the second key layer the antenna
    numbers (ie {'CODE': {'ANTENNA': {}}}).

    Parameters
    ----------
    stations : list
        list with the station ids to take files from
    interval : dict
        dict with the start_time and the end_time if the interval as a
        timestamp

    Returns
    -------
    dict
        dictionary with all the data from the database, structured by
        antenna id and location code
    """
    arguments = ['%s' for i in range(len(stations))]
    files = {}
    connection, cursor = db.get_cursor_connection()

    # get the files that are contain the interval
    sql_query = (
        "SELECT\n"
        "   location_code,\n"
        "   antenna,\n"
        "   precise_start,\n"
        "   precise_end,\n"
        "   file.start,\n"
        "   longitude,\n"
        "   latitude,\n"
        "   path\n"
        "FROM file\n"
        "JOIN `system` on file.system_id = system.id\n"
        "JOIN location on system.location_id = location.id\n"
        "WHERE (\n"
        "   (\n"
        "       precise_start <= %(start_time)s\n"
        "       AND precise_end >= %(start_time)s\n"
        "   ) OR (\n"
        "       precise_end >= %(end_time)s\n"
        "       AND precise_start <= %(end_time)s\n"
        "   )\n"
        ")\n"
    )

    # add the system_id condition
    where_clause = "AND file.system_id in (%s)\n" % ', '.join(arguments)
    where_clause = where_clause % tuple(stations)
    sql_query += where_clause

    cursor.execute(sql_query, interval)

    # structure all the data received from the database in a dictionary
    # where the location codes and teh antennas are the keys
    for (code, antenna, start, end, date, longitude, latitude, path) in cursor:
        date = date.replace(tzinfo=timezone.utc)
        if code not in files.keys():
            files[code] = {
                'longitude': longitude,
                'latitude': latitude,
                'sys': {}
            }

        if str(antenna) not in files[code]['sys'].keys():
            files[code]['sys'][str(antenna)] = {}

        files[code]['sys'][str(antenna)][date.strftime('%Y%m%d%H%M')] = {
            'start': start,
            'end': end,
            'date': date,
            'file_path': path
        }

    db.close_connection(cursor, connection)

    return files
