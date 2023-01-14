import time
import hashlib
from io import BytesIO as StringIO
from random import choice, randint, randrange
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from OJcenter.captcha import cnChar

class Captcha:
    # 登陆验证码配置项，请参考https://django-simple-captcha.readthedocs.io/en/latest/usage.html
    CAPTCHA_FONT_SIZE = 22
    CAPTCHA_IMAGE_SIZE = (130, 30)
    CAPTCHA_TIMEOUT = 60*5
    CAPTCHA_LENGTH = 4
    CAPTCHA_SCALE = 1
    CAPTCHA_PUNCTUATION = '_"\',.;:-'
    CAPTCHA_BACKGROUND_COLOR = '#ffffff'
    CAPTCHA_FOREGROUND_COLOR = '#001100'
    CAPTCHA_FONT_PATH = ['/root/OJcenter/OJcenter/OJcenter/captcha/NotoSansCJK-Bold.ttf',
                         '/root/OJcenter/OJcenter/OJcenter/captcha/NotoSansCJK-Medium.ttf',
                         '/root/OJcenter/OJcenter/OJcenter/captcha/NotoSansCJK-Regular.ttf']
    CAPTCHA_NOISE_FUNCTIONS = ['noise_dots']  # 图像噪声生成器
    CAPTCHA_CHALLENGE_FUNCT = 'random_num_char_challenge'
    CAPTCHA_LETTER_ROTATION = (-35, 35)  # 拉登变换参数，与图像倾斜幅度相关
    if CAPTCHA_CHALLENGE_FUNCT == 'random_cn_challenge':
        CAPTCHA_LETTER_ROTATION = (choice(range(35, 70)) * -1, choice(range(35, 70)))
    CAPTCHA_FILTER_FUNCTIONS = ['post_smooth']
    captcha_regex = {'random_cn_challenge': r'^[\u4E00-\u9FA5]{4}$',
                     'random_num_char_challenge': r'^[\da-zA-Z]{4}$',
                     'random_calculation_challenge': r'^(\d|[1-9]\d{1,2})$'}
    MAX_RANDOM_KEY = 18446744073709551616  # 2 << 63

    def random_cn_challenge(self):
        # 中文验证码
        captcha = ''.join([choice(cnChar.cn_char) for i in range(4)])
        return captcha, captcha

    def random_num_char_challenge(self):
        # 数字加字母验证码
        captcha = ''.join(
            [choice('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') + choice(['', ' ']) for i in
             range(3)])
        captcha += choice('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        return captcha, captcha.replace(' ', '')

    def random_calculation_challenge(self):
        # 计算题验证码
        a = choice(range(1, 101))
        b = choice(range(1, a + 1))
        return ('%s+%s=?' % (a, b), str(a + b)) if choice([0, 1]) else ('%s-%s=?' % (a, b), str(a - b))

    def getsize(self, font, text):
        if hasattr(font, 'getoffset'):
            return tuple([x + y for x, y in zip(font.getsize(text), font.getoffset(text))])
        else:
            return font.getsize(text)

    def makeimg(self, size):
        if self.CAPTCHA_BACKGROUND_COLOR == "transparent":
            image = Image.new('RGBA', size)
        else:
            image = Image.new('RGB', size, self.CAPTCHA_BACKGROUND_COLOR)
        return image

    def noise_arcs(self, draw, image):
        size = image.size
        draw.arc([-20, -20, size[0], 20], 0, 295, fill=self.CAPTCHA_FOREGROUND_COLOR)
        draw.line([-20, 20, size[0] + 20, size[1] - 20], fill=self.CAPTCHA_FOREGROUND_COLOR)
        draw.line([-20, 0, size[0] + 20, size[1]], fill=self.CAPTCHA_FOREGROUND_COLOR)
        return draw

    def noise_dots(self, draw, image):
        size = image.size
        for p in range(int(size[0] * size[1] * 0.1)):
            draw.point((randint(0, size[0]), randint(0, size[1])), fill=self.CAPTCHA_FOREGROUND_COLOR)
        return draw

    def post_smooth(self, image):
        return image.filter(ImageFilter.SMOOTH)

    def create_hashkey(self):
        text, result = getattr(self, self.CAPTCHA_CHALLENGE_FUNCT)()
        key = '%s%s%s%s' % (randrange(0, self.MAX_RANDOM_KEY), time.time(), text, result)
        return hashlib.sha1(key.encode('utf8')).hexdigest()

    def create_image(self):
        text, result = getattr(self, self.CAPTCHA_CHALLENGE_FUNCT)()
        fontpath = choice(self.CAPTCHA_FONT_PATH)
        font = ImageFont.truetype(fontpath, self.CAPTCHA_FONT_SIZE * self.CAPTCHA_SCALE)
        size = self.CAPTCHA_IMAGE_SIZE
        image = self.makeimg(size)
        xpos = 2

        charlist = []
        for char in text:
            if char in self.CAPTCHA_PUNCTUATION and len(charlist) >= 1:
                charlist[-1] += char
            else:
                charlist.append(char)

        distance_from_top = 4  # Distance of the drawn text from the top of the captcha image
        for char in charlist:
            fgimage = Image.new('RGB', size, self.CAPTCHA_FOREGROUND_COLOR)
            charimage = Image.new('L', self.getsize(font, ' %s ' % char), '#000000')
            chardraw = ImageDraw.Draw(charimage)
            chardraw.text((0, 0), ' %s ' % char, font=font, fill='#ffffff')
            charimage = charimage.rotate(randrange(*self.CAPTCHA_LETTER_ROTATION), expand=0, resample=Image.BICUBIC)
            charimage = charimage.crop(charimage.getbbox())
            maskimage = Image.new('L', size)

            maskimage.paste(charimage,
                            (xpos, distance_from_top, xpos + charimage.size[0], distance_from_top + charimage.size[1]))
            size = maskimage.size
            image = Image.composite(fgimage, image, maskimage)
            xpos = xpos + 2 + charimage.size[0]

        # centering captcha on the image
        tmpimg = self.makeimg(size)
        tmpimg.paste(image, (int((size[0] - xpos) / 2), int((size[1] - charimage.size[1]) / 2 - distance_from_top)))
        image = tmpimg.crop((0, 0, size[0], size[1]))
        draw = ImageDraw.Draw(image)
        for f in self.CAPTCHA_NOISE_FUNCTIONS:
            draw = getattr(self, f)(draw, image)
        for f in self.CAPTCHA_FILTER_FUNCTIONS:
            image = getattr(self, f)(image)
        out = StringIO()
        image.save(out, "PNG")
        out.seek(0)
        return result, out