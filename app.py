import random
import json
import requests
import yaml
from flask import Flask, render_template, request
from flask_mysqldb import MySQL

from class_tools.log_tools import Log
from class_tools.sign_mgnt import SignManagement

log = Log()
with open('./config_yaml/database.yaml', 'r', encoding='utf-8') as db_file:
    data = yaml.safe_load(db_file)
    MYSQL_HOST = data['MYSQL_HOST']
    MYSQL_USER = data['MYSQL_USER']
    MYSQL_PASSWORD = data['MYSQL_PASSWORD']
    MYSQL_DB = data['MYSQL_DB']

app = Flask(__name__)
app.config['MYSQL_HOST'] = MYSQL_HOST
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DB
mysql = MySQL(app)


@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


# 生成TBOX数据
@app.route('/supplier/sync/tbox', methods=['GET', 'POST'])
def supplier_sync_tbox():
    tbox_sn = "TBOX" + str(random.randint(10000000000000, 19999999999999))
    sim_num = "2024" + str(random.randint(10000000000, 19999999999))
    bluetooth_num = "T2:H4:04:01"
    supplierCode_num = "9CD"
    SupplierName_num = "test"
    iccid_num = "202404" + str(random.randint(10000000000000, 19999999999999))
    imsi_num = "IMSI" + str(random.randint(10000000000, 19999999999))
    imei_num = "IMEI" + str(random.randint(10000000000, 19999999999))
    tboxModel_num = "P50"
    return render_template('supplier_sync_tbox.html', tbox_sn=tbox_sn, sim_num=sim_num, bluetooth_num=bluetooth_num,
                           supplierCode_num=supplierCode_num, SupplierName_num=SupplierName_num, iccid_num=iccid_num,
                           imsi_num=imsi_num, imei_num=imei_num, tboxModel_num=tboxModel_num)


# 操作同步TBOX
@app.route('/submit/tbox', methods=['POST'])
def submit_tbox():
    tbox_data = request.form
    log.info(f'同步数据信息: {tbox_data}')
    # 0.新增SIM数据准备(从提交的表单中获取)
    tbox_sn = tbox_data.get('tbox-sn')
    sim_num = tbox_data.get('sim-num')
    bluetooth_num = tbox_data.get('bluetooth-num')
    supplierCode_num = tbox_data.get('supplierCode-num')
    iccid_num = tbox_data.get('iccid-num')
    imsi_num = tbox_data.get('imsi-num')
    imei_num = tbox_data.get('imei-num')
    SupplierName_num = tbox_data.get('SupplierName-num')
    tboxModel_num = tbox_data.get('tboxModel-num')
    ip = "IP.2024.04.01"
    # 获取token--> authorization
    try:
        with mysql.connection.cursor() as cur:
            de_token = "SELECT * FROM token_mgnt WHERE region = 1 ORDER BY id DESC LIMIT 1;"
            sg_token = "SELECT * FROM token_mgnt WHERE region = 2 ORDER BY id DESC LIMIT 1;"
            cur.execute(de_token)
            result_de = cur.fetchone()[1]
            log.info(f'获取法兰克福token:{result_de}')
            cur.execute(sg_token)
            result_sg = cur.fetchone()[1]
            log.info(f'获取新加坡token:{result_sg}')
    except Exception as err:
        log.error(f"获取token失败: {err}")
    # 1.生成各环境的SIM信息(因为供应商不知道同步到哪个国家,所以每个环境都同步到,确保同步成功,每个服务都创建相同SIM信息)
    # 生成法兰克福环境SIM卡信息
    url = "https://backend-api.eu-central-1.netauat.com/mds/sim/2.0/addSim"
    req_body = {
        "msisdn": sim_num,
        "imsi": imsi_num,
        "iccid": iccid_num,
        "ip": ip,
        "operatorId": 4
    }
    headers = {
        "Authorization": result_de,
        "Content-Type": "application/json"}
    resp = requests.post(url=url, json=req_body, headers=headers)
    response = resp.json()
    code = response['code']
    if code == 200:
        log.info(f'生成法兰克福环境SIM卡信息成功{req_body}')
    else:
        log.error(f'生成法兰克福环境SIM卡信息失败{response}')
        result_data = f'生成法兰克福环境SIM卡信息失败:{response}'
        return render_template('supplier_sync_tbox.html', result_data=result_data)
    # 生成新加坡环境SIM卡信息
    url = "https://backend-api.ap-southeast-1.netauat.com/mds/sim/2.0/addSim"
    req_body = {
        "msisdn": sim_num,
        "imsi": imsi_num,
        "iccid": iccid_num,
        "ip": ip,
        "operatorId": 5
    }
    headers = {
        "Authorization": result_sg,
        "Content-Type": "application/json"}
    resp = requests.post(url=url, json=req_body, headers=headers)
    response = resp.json()
    code = response['code']
    if code == 200:
        log.info(f'生成新加坡环境SIM卡信息成功{req_body}')
    else:
        log.error(f'生成新加坡环境SIM卡信息失败{response}')
        result_data = f'生成法兰克福环境SIM卡信息失败:{response}'
        return render_template('supplier_sync_tbox.html', result_data=result_data)
    # 2.生成签名信息
    sign = SignManagement()
    # 构造好body传给生成签名函数
    body = {"supplierCode":supplierCode_num,"supplierName":SupplierName_num,"syncTboxInfoList":[{"btAddr":bluetooth_num,"iccid":iccid_num,"imei":imei_num,"imsi":imsi_num,"simno":sim_num,"tboxModel":tboxModel_num,"tboxSn":tbox_sn}]}
    body = json.dumps(body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = sign.tbox_sign(body)  # 调用tbox签名函数获取签名信息
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncTboxInfo'
    reque_body = {"supplierCode":supplierCode_num,"supplierName":SupplierName_num,"syncTboxInfoList":[{"btAddr":bluetooth_num,"iccid":iccid_num,"imei":imei_num,"imsi":imsi_num,"simno":sim_num,"tboxModel":tboxModel_num,"tboxSn":tbox_sn}]}
    headers = {
        "appid": "HOZON-B-HlaqXC2y",
        "appkey": "60ab04f63770c75f93fd92b7fd38e5823c272425a16ec2169e30de83e3073fc2",
        "appsecret": "758e69b2a63e4df3338faefd4b9dc2052781016646f03e91ca9f176ba7f985b5",
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign
    }
    resp = requests.post(url=url, json=reque_body, headers=headers)
    resp_body = resp.json()
    code = resp_body['code']
    result_data = f'响应:{resp_body},---->请求地址:{url},---->请求体:{reque_body}'
    if code == 200:
        log.info(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    else:
        log.error(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    return render_template('supplier_sync_tbox.html',result_data=result_data)


# 生成HU数据
@app.route('/supplier/sync/hu', methods=['GET', 'POST'])
def supplier_sync_hu():
    hu_sn = "HUSN" + str(random.randint(10000000000000, 19999999999999))
    hu_hardwarever = "H0.01"
    hu_softwarever = "00.00.01"
    suppliercode_num = "9AD"
    suppliername_num = "test"
    model_num = "P50"
    return render_template('supplier_sync_hu.html', hu_sn=hu_sn, hu_hardwarever=hu_hardwarever,
                           hu_softwarever=hu_softwarever, suppliercode_num=suppliercode_num,
                           suppliername_num=suppliername_num, model_num=model_num)


# 操作同步HU
@app.route('/submit/hu', methods=['POST'])
def submit_hu():
    hu_data = request.form
    log.info(f'同步数据信息: {hu_data}')
    # 0.新增HU数据准备(从提交的表单中获取)
    hu_sn = hu_data.get('hu-sn')
    hu_hardwarever = hu_data.get('hu-hardwarever')
    hu_softwarever = hu_data.get('hu-softwarever')
    suppliercode_num = hu_data.get('suppliercode-num')
    suppliername_num = hu_data.get('suppliername-num')
    model_num = hu_data.get('model-num')
    # 1.获取token--> authorization
    try:
        with mysql.connection.cursor() as cur:
            de_token = "SELECT * FROM token_mgnt WHERE region = 1 ORDER BY id DESC LIMIT 1;"
            sg_token = "SELECT * FROM token_mgnt WHERE region = 2 ORDER BY id DESC LIMIT 1;"
            cur.execute(de_token)
            result_de = cur.fetchone()[1]
            log.info(f'获取法兰克福token:{result_de}')
            cur.execute(sg_token)
            result_sg = cur.fetchone()[1]
            log.info(f'获取新加坡token:{result_sg}')
    except Exception as err:
        log.error(f"获取token失败: {err}")
    # 2.生成签名信息
    sign = SignManagement()
    # 构造好body传给生成签名函数
    body = {"huInfoList":[{"huHardwareVer":hu_hardwarever,"huModel":model_num,"huSn":hu_sn,"huSoftwareVer":hu_softwarever}],"supplierCode":suppliercode_num,"supplierName":suppliername_num}
    body = json.dumps(body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = sign.hu_sign(body)  # 调用tbox签名函数获取签名信息
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncHuInfo'
    reque_body = {"huInfoList":[{"huHardwareVer":hu_hardwarever,"huModel":model_num,"huSn":hu_sn,"huSoftwareVer":hu_softwarever}],"supplierCode":suppliercode_num,"supplierName":suppliername_num}
    headers = {
        "appid": "HOZON-B-nWqHH40i",
        "appkey": "066913e9a675edc8824ea43111867ae38d32647764aebf08410b58576ad555af",
        "appsecret": "83fa27d77a6550cb37e5f4c53a8d56a07f7be3f2e0cc01f1a7ce0b7ee4d9a563",
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign
    }
    resp = requests.post(url=url, json=reque_body, headers=headers)
    resp_body = resp.json()
    code = resp_body['code']
    result_data = f'响应:{resp_body},---->请求地址:{url},---->请求体:{reque_body}'
    if code == 200:
        log.info(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    else:
        log.error(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    return render_template('supplier_sync_hu.html', result_data=result_data)


# 生成CGW数据
@app.route('/supplier/sync/cgw', methods=['GET', 'POST'])
def supplier_sync_cgw():
    cgw_sn = "CGW" + str(random.randint(100000000000000, 199999999999999))
    cgw_hardwarever = "H0.01"
    cgw_softwarever = "00.00.01"
    suppliercode_num = "9QD"
    suppliername_num = "test"
    model_num = "P50"
    return render_template('supplier_sync_cgw.html', cgw_sn=cgw_sn, cgw_hardwarever=cgw_hardwarever,
                           cgw_softwarever=cgw_softwarever, suppliercode_num=suppliercode_num,
                           suppliername_num=suppliername_num, model_num=model_num)


# 操作同步CGW
@app.route('/submit/cgw', methods=['POST'])
def submit_cgw():
    cgw_data = request.form
    log.info(f'同步数据信息: {cgw_data}')
    # 0.新增HU数据准备(从提交的表单中获取)
    cgw_sn = cgw_data.get('cgw-sn')
    cgw_hardwarever = cgw_data.get('cgw-hardwarever')
    cgw_softwarever = cgw_data.get('cgw-softwarever')
    suppliercode_num = cgw_data.get('suppliercode-num')
    suppliername_num = cgw_data.get('suppliername-num')
    model_num = cgw_data.get('model-num')
    # 1.获取token--> authorization
    try:
        with mysql.connection.cursor() as cur:
            de_token = "SELECT * FROM token_mgnt WHERE region = 1 ORDER BY id DESC LIMIT 1;"
            sg_token = "SELECT * FROM token_mgnt WHERE region = 2 ORDER BY id DESC LIMIT 1;"
            cur.execute(de_token)
            result_de = cur.fetchone()[1]
            log.info(f'获取法兰克福token:{result_de}')
            cur.execute(sg_token)
            result_sg = cur.fetchone()[1]
            log.info(f'获取新加坡token:{result_sg}')
    except Exception as err:
        log.error(f"获取token失败: {err}")
    # 2.生成签名信息
    sign = SignManagement()
    # 构造好body传给生成签名函数
    body = {"cgwInfoList":[{"cgwHardwareVer":cgw_hardwarever,"cgwModel":model_num,"cgwSn":cgw_sn,"cgwSoftwareVer":cgw_softwarever}],"supplierCode":suppliercode_num,"supplierName":suppliername_num}
    body = json.dumps(body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = sign.cgw_sign(body)  # 调用tbox签名函数获取签名信息
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncCgwInfo'
    reque_body = {"cgwInfoList":[{"cgwHardwareVer":cgw_hardwarever,"cgwModel":model_num,"cgwSn":cgw_sn,"cgwSoftwareVer":cgw_softwarever}],"supplierCode":suppliercode_num,"supplierName":suppliername_num}
    headers = {
        "appid": "HOZON-B-CXstNkfr",
        "appkey": "32334dd8e7e59c387f998a8a860eb95c981ac0c827617a7e8c3062b839ccf566",
        "appsecret": "72c07da1ec131cb8a4537fd6e8458b73f0a82e3781cd36ff5439bb23f71a1b3b",
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign
    }
    resp = requests.post(url=url, json=reque_body, headers=headers)
    resp_body = resp.json()
    code = resp_body['code']
    result_data = f'响应:{resp_body},---->请求地址:{url},---->请求体:{reque_body}'
    if code == 200:
        log.info(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    else:
        log.error(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    return render_template('supplier_sync_cgw.html', result_data=result_data)


# 生成ADCS数据
@app.route('/supplier/sync/adcs', methods=['GET', 'POST'])
def supplier_sync_adcs():
    adcs_sn = "ADCS" + str(random.randint(10000000000000, 19999999999999))
    adcs_hardwarever = "H0.01"
    adcs_softwarever = "00.00.01"
    suppliercode_num = "9QD"
    suppliername_num = "test"
    model_num = "P50"
    adcstype = "1"
    return render_template('supplier_sync_adcs.html', adcs_sn=adcs_sn, adcs_hardwarever=adcs_hardwarever,
                           adcs_softwarever=adcs_softwarever, suppliercode_num=suppliercode_num,
                           suppliername_num=suppliername_num, model_num=model_num, adcstype=adcstype)


# 操作同步ADCS
@app.route('/submit/adcs', methods=['POST'])
def submit_adcs():
    adcs_data = request.form
    log.info(f'同步数据信息: {adcs_data}')
    # 0.新增HU数据准备(从提交的表单中获取)
    adcs_sn = adcs_data.get('adcs-sn')
    adcs_hardwarever = adcs_data.get('adcs-hardwarever')
    adcs_softwarever = adcs_data.get('adcs-softwarever')
    suppliercode_num = adcs_data.get('suppliercode-num')
    suppliername_num = adcs_data.get('suppliername-num')
    model_num = adcs_data.get('model-num')
    adcstype = adcs_data.get('adcstype')
    # 1.获取token--> authorization
    try:
        with mysql.connection.cursor() as cur:
            de_token = "SELECT * FROM token_mgnt WHERE region = 1 ORDER BY id DESC LIMIT 1;"
            sg_token = "SELECT * FROM token_mgnt WHERE region = 2 ORDER BY id DESC LIMIT 1;"
            cur.execute(de_token)
            result_de = cur.fetchone()[1]
            log.info(f'获取法兰克福token:{result_de}')
            cur.execute(sg_token)
            result_sg = cur.fetchone()[1]
            log.info(f'获取新加坡token:{result_sg}')
    except Exception as err:
        log.error(f"获取token失败: {err}")
    # 2.生成签名信息
    sign = SignManagement()
    # 构造好body传给生成签名函数
    body = {"adcsInfoList":[{"adcsSn":adcs_sn,"adcsHardwareVer":adcs_hardwarever,"adcsSoftwareVer":adcs_softwarever,"adcsModel":model_num,"adcsType":adcstype}],"supplierCode":suppliercode_num,"supplierName":suppliername_num}
    body = json.dumps(body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = sign.adcs_sign(body)  # 调用tbox签名函数获取签名信息
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncMdcInfo'
    reque_body = {"adcsInfoList":[{"adcsSn":adcs_sn,"adcsHardwareVer":adcs_hardwarever,"adcsSoftwareVer":adcs_softwarever,"adcsModel":model_num,"adcsType":adcstype}],"supplierCode":suppliercode_num,"supplierName":suppliername_num}
    headers = {
        "appid": "HOZON-B-N50QDZE2",
        "appkey": "1a22a5662170a8006599f97889bb2c71f4d13035f8346c914c3688a597b5f768",
        "appsecret": "304c3cd6061e288e8e9c99c98befc88e1f34be6e30c4f7630f253ff299e1e236",
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign
    }
    resp = requests.post(url=url, json=reque_body, headers=headers)
    resp_body = resp.json()
    code = resp_body['code']
    result_data = f'响应:{resp_body},---->请求地址:{url},---->请求体:{reque_body}'
    if code == 200:
        log.info(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    else:
        log.error(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    return render_template('supplier_sync_adcs.html', result_data=result_data)


# 校验token输入后，保存token到数据库
@app.route('/submit', methods=['POST'])
def submit_form():
    """
    保存页面传入的token值。1为德国属于法兰克福环境国家，2为新加坡属于新加坡环境国家。
    :return: 保存之后进入主页面
    """
    name_de = request.form.get('de')
    name_sg = request.form.get('sg')
    if 100 > len(name_de) or len(name_de) > 1000:
        log.warning('输入的token长度不正确,请检查')
        return render_template('home.html', error="输入的token不正确,请检查")
    elif 100 > len(name_sg) or len(name_sg) > 1000:
        log.warning('输入的token长度不正确,请检查')
        return render_template('home.html', error="输入的token不正确,请检查")
    else:
        log.info(f'法兰克福token:{name_de},新加坡token:{name_sg}')
        try:
            with mysql.connection.cursor() as cur:
                add_token = "INSERT INTO token_mgnt (token, region) VALUES (%s, %s)"
                cur.execute(add_token, (name_de, 1))
                cur.execute(add_token, (name_sg, 2))
            mysql.connection.commit()
            return render_template('main_interface.html')
        except Exception as err:
            log.error(f"插入token失败: {err}")
            return render_template('home.html', error="保存token失败,请检查")


if __name__ == '__main__':
    app.run()
