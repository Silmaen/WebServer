"""
some usful functions
"""


def request_admin(request: str):
    """
    execute a request in the MeteoData database
    :param request: the request to execute
    :return: the feteched result
    """
    import MySQLdb
    import platform
    if platform.system() == "Windows":
        MySQLParams = {
            'host'  : "192.168.5.1",
            'user'  : "robot",
            'passwd': "Robot123",
            'db'    : "administration"
        }
    else:
        MySQLParams = {
            'host'  : "localhost",
            'user'  : "robot",
            'passwd': "Robot123",
            'db'    : "administration"
        }
    try:
        con = MySQLdb.connect(**MySQLParams)
        cur = con.cursor()
        cur.execute(request)
        con.commit()
        data = cur.fetchall()
    except MySQLdb.Error as err:
        print(str(err))
        return []
    except Exception as err:
        print(str(err))
        return []
    con.close()
    return data

def get_ActiveMachine():
    import datetime
    Table = "ActiveMachine"
    req = "SELECT * FROM `" + Table + "` ORDER BY `ID` ASC"
    data = request_admin(req)
    res = []
    for d in data:
        res.append(
            {
                "name": d[1],
                "ip": d[2],
                "mac": d[3],
                "external": d[5] == 1,
                "duration": datetime.datetime.now() - d[4],
                "status": "connected",
            }
        )
    return res
