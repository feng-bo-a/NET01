# 生成各个接口所需签名信息
import random
import urllib.parse
import hashlib
import datetime
import time

from class_tools.log_tools import Log

log = Log()
sha256_hash = hashlib.sha256()


class SignManagement:
    @staticmethod
    def tbox_sign(body):
        """
        生成TBOX同步签名信息
        :param body: 请求参数动态拼接(来源：从表带中获取-->拼接-->传入)
        :return: 调用该函数返回11位随机数、当前时间戳13位、签名体。
        """
        nonce = str(random.randint(10000000000, 99999999999))
        timestamp = str(int((time.mktime((datetime.datetime.now()).timetuple())) * 1000)).zfill(13)
        str_result = 'POST/sync/supplier/1.0/syncTboxInfoappid:HOZON-B-HlaqXC2yappkey:60ab04f63770c75f93fd92b7fd38e5823c272425a16ec2169e30de83e3073fc2nonce:' + nonce + 'timestamp:' + timestamp + 'json:' + body + '758e69b2a63e4df3338faefd4b9dc2052781016646f03e91ca9f176ba7f985b5'
        log.info(f'按签名规则拼接后最终字符串{str_result}')
        url_encode = urllib.parse.quote(str_result, safe='')
        sha256_hash.update(url_encode.encode())
        sign_tbox = sha256_hash.hexdigest()
        log.info(f'header参数nonce:{nonce},timestamp:{timestamp},sign:{sign_tbox},')
        return nonce, timestamp, sign_tbox

    @staticmethod
    def hu_sign(body):
        nonce = str(random.randint(10000000000, 99999999999))
        timestamp = str(int((time.mktime((datetime.datetime.now()).timetuple())) * 1000)).zfill(13)
        str_result = 'POST/sync/supplier/1.0/syncHuInfoappid:HOZON-B-nWqHH40iappkey:066913e9a675edc8824ea43111867ae38d32647764aebf08410b58576ad555afnonce:' + nonce + 'timestamp:' + timestamp + 'json:' + body + '83fa27d77a6550cb37e5f4c53a8d56a07f7be3f2e0cc01f1a7ce0b7ee4d9a563'
        log.info(f'签名规则拼接后字符串{str_result}')
        url_encode = urllib.parse.quote(str_result, safe='')
        sha256_hash.update(url_encode.encode())
        sign_hu = sha256_hash.hexdigest()
        log.info(f'header参数nonce:{nonce},timestamp:{timestamp},sign:{sign_hu},')
        return nonce, timestamp, sign_hu

    @staticmethod
    def cgw_sign(body):
        nonce = str(random.randint(10000000000, 99999999999))
        timestamp = str(int((time.mktime((datetime.datetime.now()).timetuple())) * 1000)).zfill(13)
        str_result = 'POST/sync/supplier/1.0/syncCgwInfoappid:HOZON-B-CXstNkfrappkey:32334dd8e7e59c387f998a8a860eb95c981ac0c827617a7e8c3062b839ccf566nonce:' + nonce + 'timestamp:' + timestamp + 'json:' + body + '72c07da1ec131cb8a4537fd6e8458b73f0a82e3781cd36ff5439bb23f71a1b3b'
        log.info(f'签名规则拼接后字符串{str_result}')
        url_encode = urllib.parse.quote(str_result, safe='')
        sha256_hash.update(url_encode.encode())
        sign_cgw = sha256_hash.hexdigest()
        log.info(f'header参数nonce:{nonce},timestamp:{timestamp},sign:{sign_cgw},')
        return nonce, timestamp, sign_cgw

    @staticmethod
    def adcs_sign(body):
        nonce = str(random.randint(10000000000, 99999999999))
        timestamp = str(int((time.mktime((datetime.datetime.now()).timetuple())) * 1000)).zfill(13)
        str_result = 'POST/sync/supplier/1.0/syncMdcInfoappid:HOZON-B-N50QDZE2appkey:1a22a5662170a8006599f97889bb2c71f4d13035f8346c914c3688a597b5f768nonce:' + nonce + 'timestamp:' + timestamp + 'json:' + body + '304c3cd6061e288e8e9c99c98befc88e1f34be6e30c4f7630f253ff299e1e236'
        log.info(f'签名规则拼接后字符串{str_result}')
        url_encode = urllib.parse.quote(str_result, safe='')
        sha256_hash.update(url_encode.encode())
        sign_adcs = sha256_hash.hexdigest()
        log.info(f'header参数nonce:{nonce},timestamp:{timestamp},sign:{sign_adcs},')
        return nonce, timestamp, sign_adcs

    @staticmethod
    def mes_sign(body):
        nonce = str(random.randint(10000000000, 99999999999))
        timestamp = str(int((time.mktime((datetime.datetime.now()).timetuple())) * 1000)).zfill(13)
        str_result = 'POST/sync/synchrodata/2.0/vehicleOfflineappid:HOZON-B-N50QDZE2appkey:1a22a5662170a8006599f97889bb2c71f4d13035f8346c914c3688a597b5f768nonce:' + nonce + 'timestamp:' + timestamp + 'json:' + body + '304c3cd6061e288e8e9c99c98befc88e1f34be6e30c4f7630f253ff299e1e236'
        log.info(f'签名规则拼接后字符串{str_result}')
        url_encode = urllib.parse.quote(str_result, safe='')
        sha256_hash.update(url_encode.encode())
        sign_adcs = sha256_hash.hexdigest()
        log.info(f'header参数nonce:{nonce},timestamp:{timestamp},sign:{sign_adcs},')
        return nonce, timestamp, sign_adcs


if __name__ == '__main__':
    pass
    '''
    body = {"supplierCode":"9CD","supplierName":"LONG","syncTboxInfoList":[{"btAddr":"20:24:01","iccid":"202401142489029","imei":"IMEI20147835049","imsi":"IMSI20106640139","simno":"100010418258699","tboxModel":"P50","tboxSn":"TBOX20240115113675"}]}
    tbox_body = json.dumps(body).replace(' ', '')
    nonce, timestamp, sign = SignManagement.tbox_sign(tbox_body)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncTboxInfo'
    req_body = {"supplierCode":"9CD","supplierName":"LONG","syncTboxInfoList":[{"btAddr":"20:24:01","iccid":"202401142489029","imei":"IMEI20147835049","imsi":"IMSI20106640139","simno":"100010418258699","tboxModel":"P50","tboxSn":"TBOX20240115113675"}]}

    headers = {
        "appid": "HOZON-B-HlaqXC2y",
        "appkey": "60ab04f63770c75f93fd92b7fd38e5823c272425a16ec2169e30de83e3073fc2",
        "appsecret": "758e69b2a63e4df3338faefd4b9dc2052781016646f03e91ca9f176ba7f985b5",
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign
    }
    resp = requests.post(url=url, json=req_body, headers=headers)
    resp_body = resp.json()
    print(resp_body)
    '''
