import datetime
import platform

import MySQLdb
import pandas as pd


def queryMessage(username):
    if platform.system() == 'Windows':
        db1 = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "jol", charset='utf8')
    elif platform.system() == 'Linux':
        db1 = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "jol", charset='utf8')
    cursor1 = db1.cursor()
    curr_time = datetime.datetime.now()
    time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
    cursor1.execute(
        "SELECT id,content FROM notification WHERE (`targetuser`=%s OR  `targetuser`='' OR  `targetuser` is null) AND (`platform`='all' or `platform`='vscode') AND (deadline>%s or `deadline`='')",
        (username, time_str))
    allmessage = cursor1.fetchall()
    allmessage = pd.DataFrame(list(allmessage), columns=['id', 'content'])
    for index in range(len(allmessage['id'])):
        item = allmessage['id'][index]
        cursor2 = db1.cursor()
        cursor2.execute("SELECT * FROM notificationget WHERE `username`=%s and notificationid=%s",
                        (username, item))
        receivedmessage = cursor2.fetchall()
        if len(receivedmessage) > 0:
            continue
        else:
            cursor3 = db1.cursor()
            cursor3.execute("INSERT into notificationget (username,notificationid) VALUES (%s,%s)", (username, item))
            db1.commit()
            return allmessage['content'][index]
    return None
