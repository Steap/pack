import urllib.request
import random
import json

try:
    import log
except:
    from . import log
try:
    import useragents
except ModuleNotFoundError:
    try:
        from . import useragent
    except:
        'Module useragent do not exists'
try:
    from parseconfig import Parse
except ModuleNotFoundError:
    try:
        from .parseconfig import Parse
    except:
        'Module parseconfig do not exists'

import http.client
import urllib.error
import urllib.parse


class Crawl:
    """
    这个类设计用于请求url，在爬虫技术方面是一个核心模块
    :param url(str):            所有符合http或https协议的url
    :param timeout(int):        请求延时
    :param encoding(str):       解码方式，错误默认忽略
    :param maxtime(int):        最大重试次数
    :param data(str or dict):   POST方法使用，带上data默认使用post方式
    :param dataType(str):       数据类型，默认str，可选填：str或json
    :param isProxy(bool):       是否使用代理
    :param proxyPools(list):    代理池，如果isProxy=True，这里需传入代理ips，list形式
    :param crawlConfig(dict):   包括maxtime、encoding和timeout三个参数的字典类型数据，可以单独传进来，也可以在crawlConfig传入，以后者为最新参数更新标准（除开''和None），如：{'maxtime':5}
    :param urlConfig(dict):     请求头信息，如：{'User_Agent':'xxxxxxxxxxx','Referer':'xxxxxxxxxx'}
    :param **kwargs(key-value): 附加请求头信息，必须大写开头

    examples:
            (1)不加代理模式
            html = crawl.crawl('https://www.baidu.com', 10)

            (2)加代理模式
            html = crawl.crawl('https://www.baidu.com', isProxy=True, proxyPools=['82.28.11.170:2331','15.28.11.120:1331'])

            (3)post模式
            html = crawl.crawl('https://www.baidu.com', data={'name': 'xiaofeng', 'age': 25})
            or
            html = crawl.crawl('https://www.baidu.com', data={'name': 'xiaofeng', 'age': 25}, dataType='json')
            视网站需求而定
            (4)添加额外请求头或者修改默认请求头
            html = crawl.crawl('https://www.baidu.com',}, Host='baidu.com', Cookie='xxxxxx')
            or
            html = crawl.crawl('https://www.baidu.com',}, urlConfig={'Host': 'baidu.com', 'Cookie': 'xxxxxx'})
    """
    def __init__(self, url, timeout=5, encoding='utf8', maxtime=5, data=None, dateType='str', isProxy=False, proxyPools=None, crawlConfig=None, urlConfig=None, isBinary=False, **kwargs):
        self.url = url
        self.timeout = timeout
        self.maxtime = maxtime
        self.encoding = encoding
        self.data = data
        self.dataType = dateType
        self.isProxy = isProxy
        self.proxyPools = proxyPools
        self.crawlConfig = crawlConfig
        self.urlConfig = urlConfig
        self.isBinary = isBinary

        # 根据协议类型选择对应的代理类型
        self.protocol = url[:url.find(':')]
        self.kwargs = kwargs

        self.html = None

        self.parse_config()
        self.run()

    def get_proxy(self):
        '''
        获取代理，返回字典类型，每一次请求更换一次代理
        :return(dict):  形如{'http': '11.11.11.11:11'} 或者 {'https': '11.11.11.11:11'}
        '''
        if self.proxyPools and self.proxyPools[0] != '':
            self.isProxy = True
            self.proxyData = {self.protocol: 'http://' + random.choice(self.proxyPools)}
        else:
            self.proxyData = {}
        return self.proxyData

    def parse_config(self):
        '''
        配置处理函数，处理传进来的各种参数，以xxxConfig参数为最终形式，但不包括None和''参数
        其中：形如User-Agent等包含“-”字符的参数名，“-”需改为“_”
        :return(None):
        '''
        urlConfig_ = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:56.0) Gecko/20100101 Firefox/55.0'}

        crawlConfig_ = {'timeout': self.timeout,
                        'encoding': self.encoding,
                        'maxtime': self.maxtime}

        if not self.urlConfig:
            urlConfig_.update(
                {x.replace('_', '-'): self.kwargs[x] for x in self.kwargs if 65 <= ord(str(x)[0]) <= 90 and self.kwargs[x]})

        else:
            urlConfig_.update({x: self.urlConfig[x] for x in self.urlConfig if 65 <= ord(str(x)[0]) <= 90 and self.urlConfig[x]})

        if not self.crawlConfig:
            crawlConfig_.update({x: self.kwargs[x] for x in self.kwargs if
                                 type(x) == str and self.kwargs[x] is not None and x in ['maxtime', 'timeout', 'encoding']})
        else:
            crawlConfig_.update({x: self.crawlConfig[x] for x in self.crawlConfig if
                                 type(x) == str and self.crawlConfig[x] is not None and x in ['maxtime', 'timeout', 'encoding']})

        self.urlConfig, self.crawlConfig = urlConfig_, crawlConfig_
        # self.urlConfig = list(map(lambda x:(x, self.urlConfig[x]), self.urlConfig))

        # 是否随机切换请求头，慎用！！！
        try:
            if Parse.crawlConfig['shuffle']:
                self.urlConfig['User-Agent'] = random.choice(useragents.userAgents)
        except:
            pass


    def run(self):
        '''
        核心请求函数
        :return(str or None):   html，请求的html源码
        '''
        index = 0
        while index <= self.crawlConfig['maxtime']:
            try:
                try:
                    if self.isProxy or self.proxyPools:
                        proxy = self.get_proxy()
                        proxyHandler = urllib.request.ProxyHandler(proxy)
                        opener = urllib.request.build_opener(proxyHandler)
                    else:
                        opener = urllib.request.build_opener()
                    if not self.data:
                        req = urllib.request.Request(self.url, headers=self.urlConfig)
                    else:
                        if self.dataType == 'json':
                            data = json.dumps(self.data)
                        else:
                            data = urllib.parse.urlencode(self.data)
                        data = data.encode('utf8')
                        req = urllib.request.Request(self.url, headers=self.urlConfig, data=data)
                    res = opener.open(req)
                    if res.status != 200:
                        raise Exception('status code is not 200 ! ')
                    if self.isBinary:
                        self.html = res.read()
                    else:
                        self.html = res.read().decode(self.crawlConfig['encoding'], errors='ignore')
                    opener.close()
                    return self.html

                except http.client.BadStatusLine as e:
                    index += 1
                    log.error('BadStatusLine Error, URL:%s' % self.url)

                except urllib.error.URLError as e:
                    index += 0.2
                    log.error('URLError, URL:%s, ERROR:%s' % (self.url, str(e)))

                except Exception as e:
                    index += 1
                    log.error('Other Error, URL:%s, ERROR:%s' % (self.url, str(e)))
            except Exception as e:
                index += 1
                log.critical('...' + str(e))
        log.critical('Index is over than %s times,crawl fail, URL;%s' % (self.crawlConfig['maxtime'], self.url))
        self.html = None



crawl = Crawl
