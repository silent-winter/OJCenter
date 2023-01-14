from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from OJcenter.captcha.CaptchaTool import Captcha
from OJcenter.Tool import redisTool, systemTool

captcha = Captcha()


def is_hashkey(hashkey):
    if len(hashkey) == 40:
        try:
            int(hashkey, 16)
        except:
            return False
        return True
    raise False


def captcha_hashkey(request):
    """生成新的验证码标识，删除旧的验证码"""
    if is_hashkey(request.POST['hashkey']):
        cache.delete('captcha_img:%s' % request.POST['hashkey'])
        return JsonResponse({'code': '0', 'hashkey': captcha.create_hashkey()})
    return JsonResponse({'code': '1', 'msg': '参数错误'})


def captcha_image(request, hashkey):
    """返回验证码图片，同时缓存验证码的值"""
    captcha_content, captcha_image_file = captcha.create_image()
    username = systemTool.checkLogin(request)
    cache.set('captcha_img:%s' % username, captcha_content, captcha.CAPTCHA_TIMEOUT)
    response = HttpResponse(captcha_image_file.read(), content_type='image/png')
    response['Content-length'] = captcha_image_file.tell()
    return response


def check_captcha(request):
    """检查验证码是否正确"""
    captcha = request.POST['captcha']
    username = systemTool.checkLogin(request)
    cache_captcha = cache.get('captcha_img:%s' % username)
    if not cache_captcha:
        return JsonResponse({'code': 0, 'msg': '验证码已过期'})
    elif str(cache_captcha).upper() != str(captcha).upper():
        return JsonResponse({'code': 0, 'msg': '验证码错误'})
    else:
        redisTool.extendLife(username)
        return JsonResponse({'code': 1, 'msg': '验证码正确'})
