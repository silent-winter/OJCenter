import os.path
import shutil
import platform

defaultFileName = ["main", "main.c", "main.py", "main.cpp"]


def initUserFolder(targetUser):
    rootPath = ""
    if platform.system() == 'Windows':
        rootPath = r"D:\templeenvironment\dockerdir"
    elif platform.system() == 'Linux':
        rootPath = "/dockerdir"
    else:
        rootPath = "/"
    samplePath = os.path.join(rootPath, "answer")
    userPath = os.path.join(rootPath, "userfolder")
    targetPath = os.path.join(userPath, targetUser)
    if not os.path.exists(targetPath):
        os.mkdir(targetPath)
    targetInnerPath = os.path.join(targetPath, "answer")
    if not os.path.exists(targetInnerPath):
        shutil.copytree(samplePath, targetInnerPath)
    else:
        for defaultFile in defaultFileName:
            defaultFilePath = os.path.join(targetInnerPath, defaultFile)
            if not os.path.exists(defaultFilePath):
                defaultFileSamplePath = os.path.join(samplePath, defaultFile)
                shutil.copy(defaultFileSamplePath, defaultFilePath)
    return targetInnerPath


def cleanPermanentPath(targetUser):
    rootPath = "/dockerdir"
    userPath = os.path.join(rootPath, "userfolder")
    targetPath = os.path.join(userPath, targetUser)
    targetInnerPath = os.path.join(targetPath, "answer")
    if os.path.exists(targetInnerPath):
        shutil.rmtree(targetInnerPath)
    return targetInnerPath


def initEmptyFolder():
    rootPath = ""
    if platform.system() == 'Windows':
        rootPath = r"D:\templeenvironment\dockerdir"
    elif platform.system() == 'Linux':
        rootPath = "/dockerdir"
    else:
        rootPath = "/"
    samplePath = os.path.join(rootPath, "answer")
    return samplePath
