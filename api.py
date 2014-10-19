import requests
import time
import json
import os
import re
from sign import GetMethod
from urllib.parse import quote
import error
import utils
import logging
#########################################################################
# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1

# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig() 
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True
#########################################################################

CONFIG_JSON = './.config.json'
DEFAULT_CONFIG = {
    'aria2c_path':'http://localhost:6800/rpc',
    'Backend':'aria2_remote',
    'cache_request':True,
    'cookie':{}
}


def getTimestamp():
    return int(time.time() * 100)

class YunApi:
    def __init__(self):
        self.r = requests.Session()
        self.r.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2182.3 Safari/537.36'
        self.logined = False
        self.loadConfig()
    def loadConfig(self):
        if os.path.exists(CONFIG_JSON):
            with open(CONFIG_JSON) as fp:
                self.config = json.load(fp)
                self.syncCookie(False)
                self.checkLogin()
        else:
            self.config = DEFAULT_CONFIG
    def storeConfig(self):
        with open(CONFIG_JSON,'w') as fp:
            json.dump(self.config, fp,indent=4)
    def syncCookie(self,Dump=True):
        if Dump:
            require = ['BDUSS','BAIDUID','BAIDUPSID']
            self.config['cookie'].update({i:j for i,j in self.r.cookies.get_dict().items() if i in require})
        else:
            self.r.cookies.update(self.config.get('cookie'))
    def checkLogin(self):
        self.logined = self.r.get('https://pan.baidu.com/api/account/thirdinfo').json()['errno'] == 0
        # print(self.r.get('https://pan.baidu.com/api/account/thirdinfo').json())
        if not hasattr(self, 'sign'):
            self.fetchYunData()
        return self.logined
    def getToken(self):
        if hasattr(self,'token'):
            return self.token
        if not self.r.cookies.get('BAIDUID'):
            self.r.get('https://passport.baidu.com/v2/api/?getapi&tpl=netdisk&class=login')
        text = self.r.get('https://passport.baidu.com/v2/api/?getapi&tpl=netdisk&class=login').text
        self.token = re.search(r'[0-9a-z]{32}',text).group()
        if not self.token:
            raise error.ApiError
        else:
            return self.token
    def login(self,username,password,input_for_verify = input):
        token = self.getToken()
        # Check if we need a verify code
        url = 'https://passport.baidu.com/v2/api/?logincheck&token={}&tpl=netdisk&username={}'.format(token,quote(username))
        ret = json.loads(self.r.get(url).text[1:-1])
        if ret['codestring']:
            url = "https://passport.baidu.com/cgi-bin/genimage?{}".format(ret['codestring'])
            with open('verify.jpg','wb') as fp:
                fp.write(self.r.get(url).content)
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
            }).text
        url = re.search(r"(?<=encodeURI\(').+?(?='\))", html).group()
        self.r.get(url)
        self.logined = True
    def fetchYunData(self):
        html = self.r.get('http://pan.baidu.com/disk/home').text
        self._signs = re.findall(r"(?<=yunData\.sign\d\s=\s[\"']).+?(?=[\"'];)", html)
        self.bdstoken = re.search(r"(?<=yunData\.MYBDSTOKEN\s=\s[\"']).+?(?=[\"'];)", html).group()
        self.sign = GetMethod(self._signs[1])(self._signs[2],self._signs[0])
        self.timestamp = re.search(r"(?<=yunData\.timestamp\s=\s['\"])\d+(?=['\"];)", html).group()
    def getFileList(self,path):
        # if self.config.get('cache')
        ret = []
        page = 1
        while True:
            temp = self._getFileList(path,page)
            ret.extend(temp)
            if len(temp) < 100:
                break
            page += 1
        return ret
    def _getFileList(self,path,page=1):
        if not hasattr(self, 'bdstoken'):
            self.fetchYunData()
        ret = self.r.get('http://pan.baidu.com/api/list?channel=chunlei&clienttype=0&web=1&num=100&order=time&desc=1&app_id=250528&showempty=0',
            params = {
                "dir":path,
                "page":page,
                "bdstoken":self.bdstoken
            }).json()
        if ret['errno'] == 0:
            return ret['list']
    def getFilesLink(self,files,batch=False):
        def convert(f):
            return "[{}]".format(",".join(str(i) for i in f))
        type_ = 'batch' if batch else 'dlink'
        ret = self.r.get('http://pan.baidu.com/api/download?channel=chunlei&clienttype=0&web=1&app_id=250528',params={
            'sign':self.sign,
            'bdstoken':self.bdstoken,
            'type':type_,
            'fidlist':convert(files),
            'timestamp':self.timestamp
            }).json()
        if ret['errno'] == 0:
            return ret['dlink']
        else:
            raise error.ApiError(ret)

api = YunApi()


class DownloaderBase():
    def pre(self):
        pass
    def download(self,files):
        # here files should be like [{filename:,link:}]
        raise NotImplemented
    def showcommand(self):
        pass

class Aria2RemoteDownloader(DownloaderBase):
    def __init__(self):
        from xmlrpc.client import ServerProxy
        self.s = ServerProxy(api.config.get('aria2c_path')) 
    def download(self,files):
        for i in files:
            url = api.r.get(i['link'],allow_redirects=False).headers['Location']
            self.s.aria2.addUri([url],{'out':i['filename']})
            print('Add {} Success'.format(utils.shortStr(i['filename'],60)))
    def showcommand(self):
        raise NotImplemented


downloader = {
    'aria2_remote':Aria2RemoteDownloader,
}[api.config.get('Backend')]()
