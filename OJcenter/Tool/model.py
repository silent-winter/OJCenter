class PodMetaInfo:
    def __init__(self, port, pvPath, clusterIp):
        self.clusterIp = clusterIp
        self.port = port
        self.pvPath = pvPath

    def __repr__(self):
        return "clusterIp=%s, port=%s, pvPath=%s" % (self.clusterIp, self.port, self.pvPath)
