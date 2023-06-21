from . import database as db


def get_location_codes():
    """
    Function selects all the different location codes from the
    database and returns them in an array

    Returns
    -------
    list
        all the available location codes
    """
    codes = []
    connection, cursor = db.get_cursor_connection()

    # get all the location codes from the location table
    sql_query = (
        "SELECT distinct location_code\n"
        "FROM location"
    )

    cursor.execute(sql_query)

    # store the data received in an array
    for code in cursor:
        codes.append(code)

    return codes
