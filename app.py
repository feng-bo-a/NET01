import random
import json
import string

import requests
import yaml
from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from class_tools.log_tools import Log
from class_tools.sign_mgnt import SignManagement

# 读取数据库参数
with open('./config_yaml/database.yaml', 'r', encoding='utf-8') as db_file:
    data = yaml.safe_load(db_file)
    MYSQL_HOST = data['MYSQL_HOST']
    MYSQL_USER = data['MYSQL_USER']
    MYSQL_PASSWORD = data['MYSQL_PASSWORD']
    MYSQL_DB = data['MYSQL_DB']
# 数据库连接配置
app = Flask(__name__)
app.config['MYSQL_HOST'] = MYSQL_HOST
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DB
mysql = MySQL(app)
log = Log()


@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('home.html')
    elif request.method == 'POST':
        """保存页面传入的token值。1为德国属于法兰克福环境国家，2为新加坡属于新加坡环境国家。保存之后进入主页面"""
        name_de = request.form.get('de')
        name_sg = request.form.get('sg')
        if 100 > len(name_de) or len(name_de) > 1000:
            log.warning(f'输入的法兰克福token长度不正确,请检查{name_de}')
            return render_template('home.html', error="输入的token不正确,请检查")
        elif 100 > len(name_sg) or len(name_sg) > 1000:
            log.warning(f'输入的新加坡token长度不正确,请检查{name_sg}')
            return render_template('home.html', error="输入的token不正确,请检查")
        else:
            log.info(f'保存成功-->法兰克福token:{name_de},新加坡token:{name_sg}')
            try:
                with mysql.connection.cursor() as cur:
                    # 连接数据库,执行SQL保存Token
                    add_token = "INSERT INTO token_mgnt (token, region) VALUES (%s, %s)"
                    cur.execute(add_token, (name_de, 1))
                    cur.execute(add_token, (name_sg, 2))
                    mysql.connection.commit()
                return render_template('base.html')
            except Exception as err:
                log.error(f"插入token失败: {err}")
                return render_template('home.html', error="保存token失败,请检查")
    else:
        return render_template('home.html', error="提交方式不符，请检查")


# 同步TBOX
@app.route('/supplier/sync/tbox', methods=['GET', 'POST'])
def supplier_sync_tbox():
    if request.method == 'GET':
        random_str_11 = str(random.randint(10000000000, 19999999999))
        random_str_14 = str(random.randint(10000000000000, 19999999999999))
        tbox_sn = "TBOX" + random_str_14
        sim = "2024" + random_str_11
        bluetooth = "T2:H4:04:01"
        supplier_code = "9CD"
        supplier_name = "test"
        icc_id = "202404" + random_str_14
        imsi = "IMSI" + random_str_11
        imei = "IMEI" + random_str_11
        tbox_model = "P50"
        log.info(f'生成的TBOX表单数据:tbox_sn:{tbox_sn},icc_id_num:{icc_id}')
        return render_template('supplier_sync_tbox.html', tbox_sn=tbox_sn, sim_num=sim, bluetooth_num=bluetooth,
                               supplierCode_num=supplier_code, SupplierName_num=supplier_name, iccid_num=icc_id,
                               imsi_num=imsi, imei_num=imei, tboxModel_num=tbox_model)
    elif request.method == 'POST':
        tbox_form = request.form
        log.info(f'TBOX表单提交的数据: {tbox_form}')
        # 0.新增SIM数据(从表单中获取数据)
        tbox_sn = tbox_form.get('tbox-sn')
        sim = tbox_form.get('sim-num')
        bluetooth = tbox_form.get('bluetooth-num')
        supplier_code = tbox_form.get('supplierCode-num')
        icc_id = tbox_form.get('iccid-num')
        imsi = tbox_form.get('imsi-num')
        imei = tbox_form.get('imei-num')
        supplier_name = tbox_form.get('SupplierName-num')
        tbox_model = tbox_form.get('tboxModel-num')
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
            "msisdn": sim,
            "imsi": imsi,
            "iccid": icc_id,
            "ip": ip,
            "operatorId": 4
        }
        headers = {
            "Authorization": result_de,
            "Content-Type": "application/json"}
        resp = requests.post(url=url, json=req_body, headers=headers)
        resp_body = resp.json()
        code = resp_body['code']
        if code == 200:
            log.info(f'生成法兰克福环境SIM卡信息成功{req_body}')
        else:
            log.error(f'生成法兰克福环境SIM卡信息失败{resp_body}')
            result_data = f'生成法兰克福环境SIM卡信息失败:{resp_body}'
            return render_template('supplier_sync_tbox.html', result_data=result_data)
        # 生成新加坡环境SIM卡信息
        url = "https://backend-api.ap-southeast-1.netauat.com/mds/sim/2.0/addSim"
        req_body = {
            "msisdn": sim,
            "imsi": imsi,
            "iccid": icc_id,
            "ip": ip,
            "operatorId": 5
        }
        headers = {
            "Authorization": result_sg,
            "Content-Type": "application/json"}
        resp = requests.post(url=url, json=req_body, headers=headers)
        resp_body = resp.json()
        code = resp_body['code']
        if code == 200:
            log.info(f'生成新加坡环境SIM卡信息成功{req_body}')
        else:
            log.error(f'生成新加坡环境SIM卡信息失败{resp_body}')
            result_data = f'生成法兰克福环境SIM卡信息失败:{resp_body}'
            return render_template('supplier_sync_tbox.html', result_data=result_data)
        # 2.生成签名信息
        # 构造好body传给生成签名函数
        tbox_body = {"supplierCode": supplier_code, "supplierName": supplier_name, "syncTboxInfoList": [
            {"btAddr": bluetooth, "iccid": icc_id, "imei": imei, "imsi": imsi, "simno": sim,
             "tboxModel": tbox_model, "tboxSn": tbox_sn}]}
        tbox_body = json.dumps(tbox_body).replace(' ', '')  # 转为json格式字符串后，去除空格
        nonce, timestamp, sign = SignManagement.tbox_sign(tbox_body)  # 调用tbox签名函数获取签名信息
        # 3.调用同步接口(表单提交的数据，替换到body中)
        url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncTboxInfo'
        req_body = {"supplierCode":supplier_code,"supplierName":supplier_name,"syncTboxInfoList":[{"btAddr":bluetooth,"iccid":icc_id,"imei":imei,"imsi":imsi,"simno":sim,"tboxModel":tbox_model,"tboxSn":tbox_sn}]}
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
        code = resp_body['code']
        result_data = f'响应:{resp_body},---->请求地址:{url},---->请求体:{req_body}'
        if code == 200:
            log.info(f'请求地址:{url},请求体:{req_body}，请求头{headers},响应:{resp_body}')
        else:
            log.error(f'请求地址:{url},请求体:{req_body}，请求头{headers},响应:{resp_body}')
        return render_template('supplier_sync_tbox.html', result_data=result_data)


'''
# 同步TBOX
@app.route('/submit/tbox', methods=['POST', 'GET'])
def submit_tbox():
    tbox_data = request.form
    log.info(f'TBOX同步数据: {tbox_data}')
    # 0.新增SIM数据准备(从提交的表单中获取)
    tbox_sn = tbox_data.get('tbox-sn')
    sim_num = tbox_data.get('sim-num')
    bluetooth_num = tbox_data.get('bluetooth-num')
    supplier_code_num = tbox_data.get('supplierCode-num')
    icc_id_num = tbox_data.get('iccid-num')
    imsi_num = tbox_data.get('imsi-num')
    imei_num = tbox_data.get('imei-num')
    supplier_name_num = tbox_data.get('SupplierName-num')
    tbox_model_num = tbox_data.get('tboxModel-num')
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
    url_sim = "https://backend-api.eu-central-1.netauat.com/mds/sim/2.0/addSim"
    req_body_sim = {
        "msisdn": sim_num,
        "imsi": imsi_num,
        "iccid": icc_id_num,
        "ip": ip,
        "operatorId": 4
    }
    headers_sim = {
        "Authorization": result_de,
        "Content-Type": "application/json"}
    resp_sim = requests.post(url=url_sim, json=req_body_sim, headers=headers_sim)
    response_sim = resp_sim.json()
    code = response_sim['code']
    if code == 200:
        log.info(f'生成法兰克福环境SIM卡信息成功{req_body_sim}')
    else:
        log.error(f'生成法兰克福环境SIM卡信息失败{response_sim}')
        result_data = f'生成法兰克福环境SIM卡信息失败:{response_sim}'
        return render_template('supplier_sync_tbox.html', result_data=result_data)
    # 生成新加坡环境SIM卡信息
    url = "https://backend-api.ap-southeast-1.netauat.com/mds/sim/2.0/addSim"
    req_body = {
        "msisdn": sim_num,
        "imsi": imsi_num,
        "iccid": icc_id_num,
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
    # 构造好body传给生成签名函数
    tbox_body = {"supplierCode": supplier_code_num, "supplierName": supplier_name_num, "syncTboxInfoList": [
        {"btAddr": bluetooth_num, "iccid": icc_id_num, "imei": imei_num, "imsi": imsi_num, "simno": sim_num,
         "tboxModel": tbox_model_num, "tboxSn": tbox_sn}]}
    tbox_body = json.dumps(tbox_body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = SignManagement.tbox_sign(tbox_body)  # 调用tbox签名函数获取签名信息
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncTboxInfo'
    req_body_tbox = tbox_body
    headers = {
        "appid": "HOZON-B-HlaqXC2y",
        "appkey": "60ab04f63770c75f93fd92b7fd38e5823c272425a16ec2169e30de83e3073fc2",
        "appsecret": "758e69b2a63e4df3338faefd4b9dc2052781016646f03e91ca9f176ba7f985b5",
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign
    }
    resp_tbox = requests.post(url=url, data=req_body_tbox, headers=headers)
    resp_tbox_body = resp_tbox.json()
    code = resp_tbox_body['code']
    result_data = f'响应:{resp_tbox_body},---->请求地址:{url},---->请求体:{req_body_tbox}'
    if code == 200:
        log.info(f'请求地址:{url},请求体:{req_body_tbox}，请求头{headers},响应:{resp_tbox_body}')
    else:
        log.error(f'请求地址:{url},请求体:{req_body_tbox}，请求头{headers},响应:{resp_tbox_body}')
    return render_template('supplier_sync_tbox.html', result_data=result_data)
'''


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


# 同步HU
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
    # 构造好body传给生成签名函数
    body = {"huInfoList": [
        {"huHardwareVer": hu_hardwarever, "huModel": model_num, "huSn": hu_sn, "huSoftwareVer": hu_softwarever}],
        "supplierCode": suppliercode_num, "supplierName": suppliername_num}
    body = json.dumps(body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = SignManagement.hu_sign(body)  # 调用tbox签名函数获取签名信息
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncHuInfo'
    reque_body = json.loads(body)  # 字符串转位字典
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


# 同步CGW
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
    # 构造好body传给生成签名函数
    body = {"cgwInfoList": [
        {"cgwHardwareVer": cgw_hardwarever, "cgwModel": model_num, "cgwSn": cgw_sn, "cgwSoftwareVer": cgw_softwarever}],
        "supplierCode": suppliercode_num, "supplierName": suppliername_num}
    body = json.dumps(body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = SignManagement.cgw_sign(body)  # 调用cgw签名函数获取签名信息
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncCgwInfo'
    reque_body = json.loads(body)
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


# 同步ADCS
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
    # 构造好body传给生成签名函数
    body = {"adcsInfoList": [
        {"adcsSn": adcs_sn, "adcsHardwareVer": adcs_hardwarever, "adcsSoftwareVer": adcs_softwarever,
         "adcsModel": model_num, "adcsType": adcstype}], "supplierCode": suppliercode_num,
        "supplierName": suppliername_num}
    body = json.dumps(body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = SignManagement.adcs_sign(body)  # 调用adcs签名函数获取签名信息(adcs和mes下线和ECU电检签名体为同一个)
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/supplier/1.0/syncMdcInfo'
    reque_body = json.loads(body)
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


'''
# 校验token输入后，保存token到数据库
@app.route('/submit', methods=['POST'])
def submit_form():
    """保存页面传入的token值。1为德国属于法兰克福环境国家，2为新加坡属于新加坡环境国家。保存之后进入主页面"""
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
'''


# 生成MES下线数据
@app.route('/mes/vehicle/off/line', methods=['GET', 'POST'])
def mes_vehicle_off_line():
    vin_num = "LUZAP5000" + str(random.randint(1000000, 9999999)) + random.choice(list(string.ascii_uppercase))
    engine = "DJH2024" + str(random.randint(10000000, 99999999))
    # 查询TBOX、HU、ADCS、CGW列表，获取未被车辆绑定的零件信息
    url = "https://backend-api.eu-central-1.netauat.com/mds/tbox/2.0/listTboxs"
    req_body = {"pageNum": 1, "pageSize": 50, "vin": "", "addMethod": True}
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
    headers = {
        "Authorization": result_de,
        "Content-Type": "application/json"}
    resp = requests.post(url=url, json=req_body, headers=headers)
    resp_body = resp.json()
    tbox_list = resp_body['data']['records']
    tbox_sn, iccid_num, imsi_num, sim_num = "", "", "", ""
    for itme in tbox_list:
        vin = itme['vin']
        if vin:
            continue
        else:
            tbox_sn = itme['tboxSn']
            iccid_num = itme['iccid']
            imsi_num = itme['imsi']
            sim_num = itme['simno']
            break
    url = 'https://backend-api.eu-central-1.netauat.com/mds/adcs/1.0/listAdcsInfo'
    req_body = {"pageNum": 1, "pageSize": 50, "vin": "", "addMethod": True}
    resp = requests.post(url=url, json=req_body, headers=headers)
    resp_body = resp.json()
    adcs_list = resp_body['data']['records']
    adcs_sn = ""
    for itme in adcs_list:
        vin = itme['vin']
        if vin:
            continue
        else:
            adcs_sn = itme['adcsSn']
            break
    url = 'https://backend-api.eu-central-1.netauat.com/mds/cgw/1.0/listCgwInfo'
    req_body = {"pageNum": 1, "pageSize": 50, "vin": "", "addMethod": True}
    resp = requests.post(url=url, json=req_body, headers=headers)
    resp_body = resp.json()
    cgw_list = resp_body['data']['records']
    cgw_sn = ""
    for itme in cgw_list:
        vin = itme['vin']
        if vin:
            continue
        else:
            cgw_sn = itme['cgwSn']
            break
    url = 'https://backend-api.eu-central-1.netauat.com/mds/hu/2.0/listHus'
    req_body = {"pageNum": 1, "pageSize": 50, "startTime": None, "endTime": None, "vin": None, "huSn": None,
                "supplierCode": None, "hardwareVersion": None, "softVersion": None, "addMethod": True}
    resp = requests.post(url=url, json=req_body, headers=headers)
    resp_body = resp.json()
    cgw_list = resp_body['data']['records']
    hu_sn = ""
    for itme in cgw_list:
        vin = itme['vin']
        if vin:
            continue
        else:
            hu_sn = itme['huSn']
            break
    log.info(f'MES下线数据:{vin_num},{engine},{hu_sn},{tbox_sn},{iccid_num},{imsi_num},{sim_num},{adcs_sn},{cgw_sn}')
    return render_template('mes_vehicle_off_line.html', vin_num=vin_num, tbox_sn=tbox_sn, iccid_num=iccid_num,
                           imsi_num=imsi_num, sim_num=sim_num, adcs_sn=adcs_sn, cgw_sn=cgw_sn, engine=engine,
                           hu_sn=hu_sn)


# MES下线
@app.route('/submit/mes', methods=['POST'])
def submit_mes():
    # 1.提取表单数据
    form_data = request.form
    log.info(f"mes表单数据{form_data}")
    vin = form_data['vin-num']
    vsn = form_data['vsn-num']
    hu_sn = form_data['hu-sn']
    if vsn == "1":
        vsn = "S6660AACGAA2023"
    elif vsn == "2":
        vsn = "S7990AABEAA9527"
    tbox_sn = form_data['tbox-sn']
    iccid = form_data['iccid-num']
    imsi = form_data['imsi-num']
    handleflag = int(form_data['handleflag'])
    adcs_sn = form_data['adcs-sn']
    adcstype = form_data['adcstype']
    cgw_sn = form_data['cgw-sn']
    salescountry = form_data['salescountry']
    engine = form_data['engine']
    # 2.生成签名信息
    # 构造好body传给生成签名函数
    body = {"vin": vin, "vsn": vsn, "certPrintTime": "2024-01-0123:58:00",
            "engine": engine, "tbox": tbox_sn, "iccid": iccid,
            "imsi": imsi, "msisdn": "100014079424079", "meid": "505742479314403",
            "huseq": hu_sn, "huHardVersion": "H0.01", "huSoftVersion": "00.00.01", "icuseq": "",
            "icuHardVersion": "", "icuSoftVersion": "", "handleFlag": handleflag, "tboxPartNumber": "TBOX-95270000",
            "huPartNumber": "HU-95270000", "adcsDTO": [
            {"adcsSn": adcs_sn, "adcsHardwareVer": "H0.01", "adcsSoftwareVer": "00.00.01", "adcsType": adcstype,
             "adcsPartNumber": "ADCS-95270000"}], "adcsName": "MDC", "checkType": 1, "factoryCode": "1001",
            "cgwSn": cgw_sn, "cgwHardwareVer": "H0.01", "cgwSoftwareVer": "00.00.01",
            "cgwPartNumber": "CGW--95270000", "postpositionEngine": "HZDJH20240101", "powerplant": "HZDJH20240101",
            "powerType": 2, "salesCountry": salescountry, "modelYear": "2024"}
    body = json.dumps(body).replace(' ', '')  # 转为json格式字符串后，去除空格
    nonce, timestamp, sign = SignManagement.mes_sign(body)  # 调用mes_sign签名函数获取签名信息(adcs和mes下线和ECU电检签名体为同一个)
    # 3.调用同步接口(表单提交的数据，替换到body中)
    url = 'http://global-mdsdata-pub.carobo.cn/sync/synchrodata/2.0/vehicleOffline'
    reque_body = json.loads(body)
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
    if code == 20000:
        log.info(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    else:
        log.error(f'请求地址:{url},请求体:{reque_body}，请求头{headers},响应:{resp_body}')
    return render_template('mes_vehicle_off_line.html', result_data=result_data)


if __name__ == '__main__':
    app.run()
