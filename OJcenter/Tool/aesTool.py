import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher(object):

    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]


# 加密
# test = AESCipher("1p0d[a;'.tjg94'h[5[h.f.s''43'wds;f[a]g'f[[,25474-=f-sa-")
# encode = test.encrypt("appmlk 2022/3/7/-17:17")
# print('encode = ' , encode)

def getEncrypt(str):
    test = AESCipher("1p0d[a;'.tjg94'h[5[h.f.s''43'wds;f[a]g'f[[,25474-=f-sa-")
    encode = test.encrypt(str)
    return encode


# 解密
# encode='ZtttPUDDPcIQaeBlt/upnMi7g2Vp77RJ6MIcA71U5kg='
# decode = test.decrypt(encode)
# print('decode = ' , decode)

def getDecrypt(str):
    test = AESCipher("1p0d[a;'.tjg94'h[5[h.f.s''43'wds;f[a]g'f[[,25474-=f-sa-")
    decode = test.decrypt(str)
    return decode
