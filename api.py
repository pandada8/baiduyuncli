import requests
import time
import json
import os
import re
from sign import GetMethod
CONFIG_JSON = './.config.json'
DEFAULT_CONFIG = {
    
}
def get_timestamp():
    return int(time.time() * 100)

class ApiError(Exception):
    pass

class YunApi:
    def __init__(self):
        self.r = requests.Session()
        self.logined = False
    def loadConfig(self):
        if os.path.exists(CONFIG_JSON):
            with open(CONFIG_JSON) as fp:
                self.config = json.load(fp)
        else:
            self.config = DEFAULT_CONFIG
    def storeConfig(self):
        with open(CONFIG_JSON) as fp:
            json.dump(self.config, fp)
    def syncCookie(self,cookie = None):
        if cookie:
            require = ['BDUSS','BAIDUID']
            self.config['cookie'].update({i:j for i,j in self.r.cookies.get_dict() if i in require})
        else:
            self.r.cookies.update(cookie)
    def checkLogin(self):
        self.logined = self.r.get('https://pan.baidu.com/api/account/thirdinfo',verify=False).json()['errno'] == 0
        return self.logined
    def getToken(self):
        if not self.r.cookies.get('BAIDUID'):
            self.r.get('https://passport.baidu.com/v2/api/?getapi&tpl=netdisk&class=login',verify=False)
        text = self.r.get('https://passport.baidu.com/v2/api/?getapi&tpl=netdisk&class=login',verify=False).text
        token = re.search(r'[0-9a-z]{32}',text).group()
        if not token:
            raise ApiError
        else:
            return token
    def login(self,username,password,input_for_verify = input):
        token = self.getToken()
        # Check if we need a verify code
        url = 'https://passport.baidu.com/v2/api/?logincheck&token={}&tpl=netdisk&username={}'.format(token,quote(username))
        ret = json.loads(self.r.get(url,verify=False).text[1:-1])
        if ret['codestring']:
            url = "https://passport.baidu.com/cgi-bin/genimage?{}".format(ret['codestring'])
            with open('verify.jpg','wb') as fp:
                fp.write(self.r.get(url,verify=False).content)
            verifyCode = input_for_verify('Verify Code("verify.jpg"):')
        else:
            verifyCode = ""
        # Build Requests
        html = self.r.post("https://passport.baidu.com/v2/api/?login",
            data = {'staticpage':"http://pan.baidu.com/res/static/thirdparty/pass_v3_jump.html",
            'charset':'utf-8',
            'token':token,
            'tpl':'netdisk',
            'tt':getTimestamp(),
            'code_string':ret['codestring'],
            'u':'http://pan.baidu.com',
            'safeflg':0,
            'username':username,
            'password':password,
            'verifycode':verifyCode,
            'mem_pass':'on'
            },verify=False).text
        url = re.search(r"(?<=encodeURI\(').+?(?='\))", html).group()
        self.r.get(url)
        self.logined = True
    def fetchSign():
        html = self.r.get('http://pan.baidu.com/disk/home').text
        self._signs = re.findall(r"(?<=yunData\.sign\d\s=\s').+?(?=';)", html)
        self.sign = GetMethod(self._signs[1])(self._signs[2],self._signs[0])
    def 



