def existing_tables(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_listing = cursor.fetchall()
    returned = []
    for entry in table_listing:
        returned.append(entry[0])
    return returned

def get_data_download_timestamp(cursor, internal_region_name):
    cursor.execute("SELECT download_timestamp FROM osm_data_update_log WHERE area_identifier = :area_identifier ORDER BY download_timestamp DESC LIMIT 1", {"area_identifier": internal_region_name})
    returned = cursor.fetchall()
    if len(returned) == 0:
        return 0
    else:
        return returned[0][0]
