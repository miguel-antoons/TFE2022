import mysql.connector

from . import database as db
from datetime import timezone


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

    Returns
    -------
    boolean
        Returns True on success, False on fail
    """
    connection, cursor = db.get_cursor_connection()
    print('Saving values in the database...')

    # sql query to update the database values
    sql_query = (
        "UPDATE file "
        "SET psd = %(noise_psd)s "
        "WHERE "
        "system_id = %(system_id)s "
        "AND start = %(time)s"
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

    Returns
    -------
    boolean
        Returns True on success, False on fail
    """
    connection, cursor = db.get_cursor_connection()
    print('Saving values in the database...')

    # sql query to update the database values
    sql_query = (
        "UPDATE file "
        "SET calibrator = %(calibrator_psd)s "
        "WHERE "
        "system_id = %(system_id)s "
        "AND start = %(time)s"
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


def get_previous_noise_psd(stations=[], get_all=True, limit=150):
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
        determines wheter to get all the psd values from the table or not,
        by default True
    limit : int, optional
        limit of values per station, is multiplied by the length of the
        stations list, by default 150

    Returns
    -------
    dict
        a dictionnary where the system ids are the keys and the values are
        lists of psd values
    """
    arguments = ['%s' for i in range(len(stations))]
    psd = {}
    connection, cursor = db.get_cursor_connection()
    limit_statement = ""

    # get the last noise psd values and system_id from the database
    sql_query = (
        "SELECT system_id, psd\n"
        "FROM file\n"
        "WHERE psd is not null\n"
    )

    # filter system_id if asked
    if not get_all:
        sql_query += (
            "AND system_id in (%s)\n"
            % ', '.join(arguments)
        )

        # add limit to get only the 150 last values for each station
        limit_statement = "LIMIT %s" % (limit * len(stations))

    # order by statement in order to get the last psd values
    sql_query += f"ORDER BY file.precise_start\n{limit_statement}"

    cursor.execute(sql_query, tuple(stations))

    # structure the data received from the database into a dictionnary of
    # arrays
    for (sys_id, psd_val) in cursor:
        if sys_id not in psd:
            psd[sys_id] = []

        psd[sys_id].append(psd_val)

    db.close_connection(cursor, connection)

    return psd


def get_previous_calibrator_psd(stations=[], get_all=True):
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
        ignored if get_all is set to Trye, by default []
    get_all : bool, optional
        determines wheter to get the last psd value from all the
        stations or only the stations specified in the stations
        list, by default True

    Returns
    -------
    dict
        a dictionnary where the system ids are the keys and the values are
        the calibrator psd values
    """
    arguments = ['%s' for i in range(len(stations))]
    psd = {}
    connection, cursor = db.get_cursor_connection()

    # get the last calibrator psd value for the requested systems (stations)
    sql_query = (
        "SELECT file.system_id, calibrator\n"
        "FROM file\n"
        "INNER JOIN\n"
        "   (SELECT system_id, max(precise_start) as top_date\n"
        "   FROM file\n"
        "   WHERE calibrator is not null\n"
        "   GROUP BY system_id)\n"
        "   AS latest\n"
        "   ON latest.top_date = file.precise_start\n"
        "   AND latest.system_id = file.system_id\n"
    )

    # filter system ids if asked
    if not get_all:
        sql_query += (
            "WHERE file.system_id in (%s)\n"
            % ', '.join(arguments)
        )

    cursor.execute(sql_query, tuple(stations))

    # structure the data received from the database into a dictionnary of
    # arrays
    for (sys_id, psd_val) in cursor:
        psd[sys_id] = psd_val

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
        dictionnary with all the data from the database, structured by
        antenna id and location code
    """
    arguments = ['%s' for i in range(len(stations))]
    files = {}
    connection, cursor = db.get_cursor_connection()

    # get the files that are contain the interva
    sql_query = (
        "SELECT\n"
        "   location_code,\n"
        "   antenna,\n"
        "   precise_start,\n"
        "   precise_end,\n"
        "   file.start,\n"
        "   longitude,\n"
        "   latitude\n"
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

    # structure all the data received from the database in a dictionnary
    # where the location codes and teh antennas are the keys
    for (code, antenna, start, end, date, longitude, latitude) in cursor:
        date = date.replace(tzinfo=timezone.utc)
        if code not in files.keys():
            files[code] = {
                'longitude': longitude,
                'latitide': latitude
            }

        if str(antenna) not in files[code].keys():
            files[code][str(antenna)] = {}

        files[code][str(antenna)][date.strftime('%Y%m%d%H%M')] = {
            'start': start,
            'end': end,
            'date': date
        }

    db.close_connection(cursor, connection)

    return files
