class PodMetaInfo:
    def __init__(self, ip, port, name, pvPath):
        self.ip = ip
        self.port = port
        self.name = name
        self.pvPath = pvPath

    def __repr__(self):
        return "ip=%s, port=%s, name=%s, pvPath=%s" % (self.ip, self.port, self.name, self.pvPath)
