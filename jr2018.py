import requests
import zlib
import json
import datetime
import logging
import pickle
import base64
import time

from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()


# 初始化日志程序
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt='[%(asctime)s]%(levelname)s:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')
# 配置日志输出到文件
file_logging = logging.FileHandler('auto.log')
file_logging.setLevel(logging.INFO)
file_logging.setFormatter(formatter)
logger.addHandler(file_logging)


# 格式化服务器返回数据
def parse_data(data):
    data = zlib.decompress(data)
    data = json.loads(data.decode('utf-8'))
    return data


# base64编码
def get_base64(data):
    data = base64.b64encode(data.encode('utf-8'))
    data = str(data, 'utf-8')
    return data


# 格式化资源数据
def packer_result(data):
    resources = data['newAward']
    fuel = resources.get('2', 0)
    ammo = resources.get('3', 0)
    steel = resources.get('4', 0)
    alum = resources.get('9', 0)
    fastBuild = resources.get('141', 0)
    shipBlueprint = resources.get('241', 0)
    fastRepair = resources.get('541', 0)
    equiptBlueprint = resources.get('741', 0)
    return {
        '油': fuel,
        '弹': ammo,
        '钢': steel,
        '铝': alum,
        '船图': shipBlueprint,
        '装备图': equiptBlueprint,
        '快修': fastRepair,
        '快建': fastBuild
        }


# 获取远征资源
def get_result(session, server_id, exploreId):
    url = 'http://s{}.jr.moefantasy.com/explore/getResult/{}/&gz=1'.format(server_id, exploreId)
    try:
        r = session.get(url)
        data = parse_data(r.content)
        data = packer_result(data)
    except Exception as e:
        logger.error('回收远征失败, error:{0}'.format(e))
    if data.get('bigSuccess', None):
        print('大成功')
    msg = '远程成功,获取资源{0}'.format(data)
    logger.info(msg)


# 开始远征
def start_expedition(session, server_id, fleetId, exploreId):
    expedition_name = '-'.join(str(exploreId).split('000'))
    url = 'http://s{}.jr.moefantasy.com/explore/start/{}/{}/&gz=1&market=2&channel=100011&version=3.1.0'.format(server_id, fleetId, exploreId)
    try:
        session.get(url)
    except Exception as e:
        logger.error('远征创建失败,error:{0}'.format(e))
    else:
        msg = '第{}舰队开始远征{}'.format(fleetId, expedition_name)
        logger.info(msg)


# 检查远征状态
def check_expedition(session, server_id):
    expedition_url = 'http://s{}.jr.moefantasy.com/api/initGame/&gz=1'.format(
        server_id)
    r = session.get(expedition_url)
    expedition_data = parse_data(r.content)
    data = list()
    for expStatusData in expedition_data['pveExploreVo']['levels']:
        fleetId = expStatusData['fleetId']
        exploreId = expStatusData['exploreId']
        if expStatusData['endTime'] < expedition_data['systime']:
            get_result(session, server_id, exploreId)
            start_expedition(session, server_id, fleetId, exploreId)
            msg = '第{}舰队远征完成'.format(fleetId)
            data.append(msg)
        else:
            endTime = expStatusData['endTime']
            endTime = datetime.datetime.fromtimestamp(endTime)
            msg = '第{}舰队正在远征, 收获时间：{}'.format(fleetId, endTime)
            data.append(msg)
        if data:
            with open('status.log', 'wb') as f:
                pickle.dump(data, f)


@sched.scheduled_job('interval', seconds=180)
def main():
    username_input = ''
    password_input = ''
    # 登陆获取cookie
    username = get_base64(username_input)
    password = get_base64(password_input)
    t = int(time.time() * 1000)
    login_url = 'http://login.jr.moefantasy.com/index/passportLogin/{0}/{1}/&t={2}&e=514bf3697307b044&gz=1&market=2&channel=0&version=3.3.0'.format(username, password, t)

    r = requests.get(login_url).content
    login_data = parse_data(r)
    cookie_dict = {'hf_skey': login_data['hf_skey']}

    # 设置cookie
    session = requests.session()
    session.cookies = requests.utils.cookiejar_from_dict(
        cookie_dict, cookiejar=None, overwrite=True)

    # 登陆胡德服务器
    user_id = login_data['userId']
    server_id = 2
    server_url = 'http://s{}.jr.moefantasy.com//index/login/{}?gz=1'.format(
        server_id, user_id)
    r = session.get(server_url)
    server_data = parse_data(r.content)
    login_status = server_data.get('loginStatus', 0)
    if login_status == 0:
        logger.error('登陆失败')
        raise ('登陆失败')
    check_expedition(session, server_id)


sched.start()
