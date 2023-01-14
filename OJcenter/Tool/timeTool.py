import datetime


def getCurrTime():
    # 获取当前时间
    currTime = datetime.datetime.now()

    # 转化时间格式
    currTime = datetime.datetime.strftime(currTime, '%Y/%m/%d-%H:%M')
    return currTime
