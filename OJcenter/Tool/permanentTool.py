import os.path
import shutil
import platform

defaultFileName = ["main", "main.c", "main.py", "main.cpp"]


def initUserFolder(targetUser):
    if platform.system() == 'Windows':
        rootPath = r"D:\templeenvironment\dockerdir"
    elif platform.system() == 'Linux':
        rootPath = "/dockerdir"
    else:
        rootPath = "/"
    samplePath = "/dockerdir/answer"
    # /dockerdir/userfolder
    userPath = os.path.join(rootPath, "userfolder")
    # /dockerdir/userfolder/{username}
    targetPath = os.path.join(userPath, targetUser)
    if not os.path.exists(targetPath):
        # 用户目录不存在，创建
        os.mkdir(targetPath)
    # /dockerdir/userfolder/{username}/answer
    targetInnerPath = os.path.join(targetPath, "answer")
    if not os.path.exists(targetInnerPath):
        # 用户answer目录不存在，copy默认文件(/dockerdir/sample/main.*)
        shutil.copytree(samplePath, targetInnerPath)
    else:
        # 用户answer目录存在
        for defaultFile in defaultFileName:
            # /dockerdir/userfolder/{username}/answer/main.xxx
            defaultFilePath = os.path.join(targetInnerPath, defaultFile)
            if not os.path.exists(defaultFilePath):
                # 如果没有以上main文件，从sample目录下copy
                defaultFileSamplePath = os.path.join(samplePath, defaultFile)
                shutil.copy(defaultFileSamplePath, defaultFilePath)
    return targetInnerPath


def cleanPermanentPath(targetUser):
    # rootPath = "/dockerdir"
    # userPath = os.path.join(rootPath, "userfolder")
    # targetPath = os.path.join(userPath, targetUser)
    # targetInnerPath = os.path.join(targetPath, "answer")
    targetInnerPath = "/dockerdir/userfolder/%s/answer" % targetUser
    if os.path.exists(targetInnerPath):
        # 清除用户目录
        shutil.rmtree(targetInnerPath)
    return targetInnerPath


def initEmptyFolder():
    if platform.system() == 'Windows':
        rootPath = r"D:\templeenvironment\dockerdir"
    elif platform.system() == 'Linux':
        rootPath = "/dockerdir"
    else:
        rootPath = "/"
    samplePath = os.path.join(rootPath, "answer")
    return samplePath
