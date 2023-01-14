import urllib
import rsa
import base64


def decode(input):
    result = urllib.parse.unquote(input)
    return result
    # list=input.split("|")
    # with open("/root/OJcenter/OJcenter/OJcenter/Tool/private.pem") as f:
    #     privkey = rsa.PrivateKey.load_pkcs1(f.read().encode())
    #     message=""
    #     for item in list:
    #         if len(item)>0:
    #             temp = base64.b64decode(item)
    #             message += rsa.decrypt(temp, privkey).decode()
    #     result = urllib.parse.unquote(message)
    #     return result
