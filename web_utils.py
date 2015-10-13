# coding: utf-8
from collections import OrderedDict
from urllib import request, parse


def firefox_url_req(url: str) -> request.Request:
    headers = OrderedDict([
        ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0'),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Accept-Language', 'en-us,en;q=0.8,zh-tw;q=0.5,zh;q=0.3'),
        ('Accept-Encoding', 'gzip, deflate'),
        ('Connection', 'keep-alive'),
        ('Pragma', 'no-cache'),
        ('Cache-Control', 'no-cache')
    ])
    return request.Request(url, headers=headers)

"""
def get_http_resp_content(url:str) -> str:
    req = firefox_url_req(url)
    with request.urlopen(req) as fin:
        content_encoding = fin.info().get("Content-Encoding").lower().strip()
        content_type = fin.info().get("Content-Type")
        content_charset = next(( _ for _ in content_type.split(';') if _.startswith("charset=")),
                                "charset=UTF-8" )
        content_charset = content_charset.split(sep='=', maxsplit=1)[1]
        if 'gzip' in content_encoding:
            from io import BytesIO
            import gzip
            gzdata = BytesIO(fin.readall())
            gzfile = gzip.GzipFile(fileobj=gzdata)
            data = gzfile.read()
        else:
            data = fin.readall()
        return data.decode(content_charset)
"""

def get_http_resp_content(url:str) -> str:
    data, content_charset, _ =  get_http_resp_content_bin(url)
    if not data:
        return ""
    return data.decode(content_charset)



def get_http_resp_content_bin(url:str) -> (bytes, str, str):
    """
    returns (content:bytes, char_set, content_type)
    """
    req = firefox_url_req(url)
    try:
        with request.urlopen(req) as resp:
            content_encoding = resp.info().get("Content-Encoding", failobj="").lower().strip()
            content_type = resp.info().get("Content-Type", failobj="")
            content_charset = next(( _ for _ in content_type.split(';') if _.startswith("charset=")),
                                    "charset=UTF-8" )
            content_charset = content_charset.split(sep='=', maxsplit=1)[1]
            if 'gzip' in content_encoding:
                from io import BytesIO
                import gzip
                gzdata = BytesIO(resp.readall())
                gzfile = gzip.GzipFile(fileobj=gzdata)
                return gzfile.read(), content_charset, content_type
            else:
                return resp.readall(), content_charset, content_type
    except Exception as ex:
        import traceback
        traceback.print_exc()
        print(ex)
        return None,None,None

