from . import database as db


def get_station_ids(stations=[], get_all=True):
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
        array of the string location codes, defaults to an empty array
    get_all : boolean
        determines wheter to get all the station ids or only to get those
        that are part of the location_codes specified in the 'stations'
        array

    Returns
    -------
    array
        array of dictionnaries containing all the system ids of the asked
        location codes.
        The system ids are grouped by location codes and by antenna.
    """
    arguments = ['%s' for i in range(len(stations))]
    ids = {}
    connection, cursor = db.get_cursor_connection()

    # get system_id for each location and antenna
    sql_query = (
        "SELECT system.id, location_code, antenna\n"
        "FROM `system`\n"
        "JOIN location on system.location_id = location.id\n"
    )

    if not get_all:
        sql_query += (
            "WHERE location.id = system.location_id AND location_code in (%s);"
            % ', '.join(arguments)
        )

    cursor.execute(sql_query, tuple(stations))

    # structure the system id's first by location code and then by antenna
    for (sys_id, loc_code, antenna) in cursor:
        if loc_code not in ids:
            ids[loc_code] = {}

        ids[loc_code][str(antenna)] = sys_id

    db.close_connection(connection, cursor)

    return ids
