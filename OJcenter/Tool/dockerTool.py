import json
import os
import tarfile
import time
from io import BytesIO

import datetime
import docker
from OJcenter.Tool import systemTool, RSAdecode, timeTool, aesTool

import threading
import _thread
from OJcenter.Tool import redisTool
import MySQLdb
import pandas as pd
import difflib


def cleanContainers():
    client = docker.from_env()
    containerList = client.containers.list(all=True)
    for container in containerList:
        containerName = str(container.name)
        if containerName.startswith("ojDockerServer"):
            container.stop()
            container.remove()
            print(containerName)


def createContainerWait(targetPort):
    try:
        if targetPort != -1:
            client = docker.from_env()
            client.containers.run(image="server_20220330:latest", detach=True,
                                  name=["ojDockerServer" + str(targetPort)],
                                  ports={'8443': ('0.0.0.0', targetPort)})
            return targetPort
        else:
            return -1
    except:
        return -1


def removeContainer(targetPort):
    try:
        client = docker.from_env()
        container = client.containers.get("ojDockerServer" + str(targetPort))
        if container != None:
            container.stop()
            container.remove()
            return 1
        else:
            return 0
    except:
        return -1


def dockerExist(targetPort):
    try:
        client = docker.from_env()
        container = client.containers.get("ojDockerServer" + str(targetPort))
        if container != None:
            return True
        else:
            return False
    except:
        return False


def getDockerFile(container, fileName):
    try:
        file = container.get_archive(fileName)
        stream, stat = file
        file_obj = BytesIO()
        for i in stream:
            file_obj.write(i)
        file_obj.seek(0)
        tar = tarfile.open(mode='r', fileobj=file_obj)
        temp = fileName.split("/")
        text = tar.extractfile(temp[len(temp) - 1])
        q = text.read()
        return str(q, encoding="utf-8")
    except:
        return ""


def getContainerFile(targetPort, language):
    try:
        client = docker.from_env()
        container = client.containers.get("ojDockerServer" + str(targetPort))
        if container != None:
            # filePath=getDockerFile(container,"/config/workspace/.vscode/currentFile")
            # codeContent=getDockerFile(container,filePath)
            codeContent = getDockerFile(container, "/config/workspace/answer/main." + language)
            return codeContent
        else:
            return ""
    except:
        return ""


def writeContainerFile(targetPort, code, id, language):
    command = "docker exec " + "ojDockerServer" + str(targetPort) + " mkdir /config/workspace/test"
    os.system(command)

    with open("/root/ojtempfile/" + id + "." + language, "w") as f:
        f.write(code)

    command = "docker exec " + "ojDockerServer" + str(targetPort) + " rm /config/workspace/test/" + id + "." + language
    os.system(command)

    command = "docker cp " + "/root/ojtempfile/" + id + "." + language + " " + "ojDockerServer" + str(targetPort) + \
              ":/config/workspace/test/"
    os.system(command)

    command = "docker exec " + "ojDockerServer" + str(
        targetPort) + " chown abc /config/workspace/test/" + id + "." + language
    os.system(command)

    os.remove("/root/ojtempfile/" + id + "." + language)


def refreshthread():
    try:
        _thread.start_new_thread(refreshcopy, ())
    except:
        print("Error: 无法启动线程")


def addEightHours(inputTime):
    timestamp = time.mktime(time.strptime(inputTime, '%Y-%m-%d %H:%M:%S'))
    datetime_struct = datetime.datetime.fromtimestamp(timestamp)
    datetime_struct += datetime.timedelta(hours=8)
    datetime_str = datetime_struct.strftime('%Y-%m-%d %H:%M:%S')
    return datetime_str


def dockerWriteVSFile(fileName, username, targetPort, fileContent):
    with open("/root/ojtempfile/" + username + fileName, "w") as f:
        f.write(str(fileContent))

    command = "docker exec " + "ojDockerServer" + str(targetPort) + " rm /config/workspace/.vscode/" + fileName + ".txt"
    os.system(command)

    command = "docker cp " + "/root/ojtempfile/" + username + fileName + " " + "ojDockerServer" + str(
        targetPort) + ":/config/workspace/.vscode/" + fileName + ".txt"
    os.system(command)

    command = "docker exec " + "ojDockerServer" + str(
        targetPort) + " chown abc /config/workspace/.vscode/" + fileName + ".txt"
    os.system(command)

    os.remove("/root/ojtempfile/" + username + fileName)


def refreshcopy():
    while True:
        try:
            db = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "record", charset='utf8')
            db1 = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "jol", charset='utf8')
            userDict = redisTool.collectUser()
            for username in userDict:
                targetPort = userDict[username]
                client = docker.from_env()
                container = client.containers.get("ojDockerServer" + str(targetPort))
                if container != None:
                    skipLine = int(getDockerFile(container, "/config/workspace/.vscode/remove.txt"))
                    # skipLine*=1
                    recordLine = getDockerFile(container, "/config/workspace/.vscode/record.txt").split("\r\n")
                    # skipNextTime=int(len(recordLine)/1)
                    skipNextTime = len(recordLine)
                    if len(recordLine) <= skipLine:
                        continue
                    if skipNextTime >= 1:
                        if len(recordLine[0].strip()) == 0 and len(recordLine) == 1:
                            continue
                        dockerWriteVSFile("remove", username, targetPort, skipNextTime)
                        for num in range(len(recordLine)):
                            value = recordLine[num]
                            jsonData = json.loads(value)
                            modifyCode = ""
                            if len(jsonData["content1"]) > 0:
                                modifyCode = RSAdecode.decode(jsonData["content1"])
                            clipContent = ""
                            if len(jsonData["content2"]) > 0:
                                clipContent = RSAdecode.decode(jsonData["content2"])
                            modifyTime = jsonData["time"]
                            modifyTime = addEightHours(modifyTime)

                            fileAddress = jsonData["filename"]
                            codeType = jsonData["type"]

                            curr_time = datetime.datetime.now()
                            time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')

                            # 查找同一用户、同一文件、临近前时间的代码
                            cursor1 = db.cursor()
                            cursor1.execute(
                                'select modifycode from collectinfo where username=%s and fileaddress=%s order by modifytime desc limit 1',
                                (username, fileAddress))
                            beforemodifycode = cursor1.fetchall()
                            beforemodifycode = pd.DataFrame(list(beforemodifycode), columns=['modifycode'])
                            beforemodifycode = beforemodifycode['modifycode']
                            if len(beforemodifycode) == 0:
                                action = "+" + modifyCode
                            else:
                                text1_lines = beforemodifycode[0].splitlines()
                                text2_lines = modifyCode.splitlines()
                                d = difflib.Differ()
                                diff = d.compare(text1_lines, text2_lines)
                                action = '\n'.join(list(diff))

                            # 查找时间对应的题目和竞赛
                            cursor2 = db1.cursor()
                            cursor2.execute(
                                'select username, problem, time from pagevisit where username=%s and time <%s order by time desc limit 1',
                                (username, modifyTime))
                            data = cursor2.fetchall()
                            data = pd.DataFrame(list(data), columns=['username', 'problem', 'time'])
                            visittime = data['time']
                            if len(visittime) > 0:
                                problem = data['problem'][0]
                                if '+' in problem:
                                    contestid = problem.split('+', 2)[0]
                                    if problem[-1] == "+":
                                        problemid = ""
                                    else:
                                        problemid = problem.split('+', 2)[1]
                                else:
                                    problemid = problem
                                    contestid = ""

                            cursor = db.cursor()
                            query = """insert into collectinfo (username, targetport, fileaddress,modifytime, codetype, modifycode, updatetime, contestid, problemid, action) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                            values = (
                            username, targetPort, fileAddress, modifyTime, codeType, modifyCode, time_str, contestid,
                            problemid, action)
                            cursor.execute(query, values)
                            db.commit()
                else:
                    return ""
            db.close()
            db1.close()
        except Exception as re:
            print(re)
            try:
                if username != None:
                    if redisTool.queryUser(username):
                        dockerWriteVSFile("remove", username, targetPort, "0")
                        dockerWriteVSFile("record", username, targetPort, "")

                    cursor = db.cursor()
                    sql = "INSERT INTO collectinfo(username," \
                          "targetport, fileaddress, modifytime, codetype, modifycode, updatetime)" \
                          "VALUES (%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(sql, [username, targetPort, "-", "-", "-", "vscode异常", time_str])
                    db.commit()
            except Exception as re:
                print(re)
        time.sleep(5)


def copyPermanentFolder(targetUser, targetPort, targetInnerPath):
    command = "docker start " + "ojDockerServer" + str(targetPort)
    os.system(command)
    systemTool.waitUntilFinished(targetPort)
    command = "docker cp " + targetInnerPath + " " + "ojDockerServer" + str(targetPort) + ":/config/workspace/"
    os.system(command)

    currtime = timeTool.getCurrTime()
    encryptpath = "/dockerdir/userfolder/" + targetUser
    if (os.path.exists(encryptpath + '/authorization')):
        os.remove(encryptpath + '/authorization')
    file = open(encryptpath + "/authorization", "w")
    stustr = targetUser + ' ' + currtime
    code = aesTool.getEncrypt(stustr)
    file.write(code.decode())
    file.close()

    topath = "/dockerdir/userfolder/" + targetUser + "/authorization"
    command = "docker cp " + topath + " " + "ojDockerServer" + str(targetPort) + ":/config/workspace/.vscode"
    os.system(command)

    command = "docker exec " + "ojDockerServer" + str(targetPort) + " chown -R abc /config/workspace/answer/"
    os.system(command)


def backupPermanentPath(targetPort, targetPath):
    try:
        command = "docker cp " + "ojDockerServer" + str(targetPort) + ":/config/workspace/answer" + " " + targetPath
        os.system(command)
    except Exception as re:
        print(re)


if __name__ == '__main__':
    test = "2021-10-08 8:42:44"
    timestamp = time.mktime(time.strptime(test, '%Y-%m-%d %H:%M:%S'))
    datetime_struct = datetime.datetime.fromtimestamp(timestamp)
    datetime_struct += datetime.timedelta(hours=8)
    datetime_str = datetime_struct.strftime('%Y-%m-%d %H:%M:%S')

    cleanContainers()

    for targetPort in range(9101, 9151):
        maxCpuNum = 20
        currentCpu = str(targetPort % maxCpuNum)
        if targetPort != -1:
            client = docker.from_env()
            client.containers.run("server_20220330:latest", cpuset_cpus=currentCpu, detach=True,
                                  name=["ojDockerServer" + str(targetPort)],
                                  ports={'8443': ('127.0.0.1', targetPort)})

    # 关闭并删除所有之前创建的相关容器（不会影响到和本项目无关的容器）
    # cleanContainers()

    # 从端口池中抽取一个空余端口号，创建容器并返回端口号
    # targetPort = createContainer()

    # 关闭并删除指定端口号对应的容器，返回值：
    # 1 关闭并删除成功
    # 0 不存在这个容器
    # -1 出现未知错误
    # response = removeContainer(targetPort)

    # print(response)
    # getContainerFile(9100,"cpp")
    # writeContainerFile(9100,"#includ2e <stdio.h>\n\nint main()\n{\n	printf(\"hello world\");\n}","123", "cpp")


def copyEmptyFolder(targetPort, targetInnerPath):
    return None
