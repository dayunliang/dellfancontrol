#!/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import os
import time
import subprocess
import syslog
import signal
import logging
from logging.handlers import RotatingFileHandler

# 脚本参数和路径设置
pausetime = 10  # 循环暂停时间（秒）
ipmiexe = "/vmfs/volumes/datastore3/opt/ipmitool/ipmitool"  # IPMI工具路径
temp1 = 0.0  # CPU1温度
temp2 = 0.0  # CPU2温度
prevtemp1 = 0.0  # 上一次记录的CPU1温度
prevtemp2 = 0.0  # 上一次记录的CPU2温度
fanmode = "static"  # 风扇模式，默认静态模式
logmsg = ""  # 日志消息

log_file = "/var/log/fanctl.log"  # 日志文件路径
log_max_bytes = 5 * 1024 * 1024  # 日志文件大小（5 MB）
log_backup_count = 3  # 保留的备份日志文件数量

PIDFILE = "/var/run/fanctl.pid"  # PID文件路径
fanauto = ["raw", "0x30", "0x30", "0x01", "0x01"]  # IPMI命令 - 切换至自动风扇模式
fanmanual = ["raw", "0x30", "0x30", "0x01", "0x00"]  # IPMI命令 - 切换至手动/静态风扇模式
returntoauto = 65.0  # 当CPU温度高于等于此值时，切换回自动风扇模式
temp_thresholds = [45.0, 50.0, 55.0, 60.0, 65.0]  # CPU温度阈值，对应不同风扇速度设定点
# 风扇速度设置表
fanspeeds = {
    "FAN2": [
        ["raw", "0x30", "0x30", "0x02", "0x02", "0x0a"],   # 默认速度 10%
        ["raw", "0x30", "0x30", "0x02", "0x02", "0x0f"],   # 大于等于temp1时 15%
        ["raw", "0x30", "0x30", "0x02", "0x02", "0x14"],   # 大于等于temp2时 20%
        ["raw", "0x30", "0x30", "0x02", "0x02", "0x19"],   # 大于等于temp3时 25%
        ["raw", "0x30", "0x30", "0x02", "0x02", "0x1e"]    # 大于等于temp4时 30%
    ],
    "FAN3": [
        ["raw", "0x30", "0x30", "0x02", "0x03", "0x0a"],   # 默认速度 10%
        ["raw", "0x30", "0x30", "0x02", "0x03", "0x0f"],   # 大于等于temp1时 15%
        ["raw", "0x30", "0x30", "0x02", "0x03", "0x14"],   # 大于等于temp2时 20%
        ["raw", "0x30", "0x30", "0x02", "0x03", "0x19"],   # 大于等于temp3时 25%
        ["raw", "0x30", "0x30", "0x02", "0x03", "0x1e"]    # 大于等于temp4时 30%
    ],
    # FAN0, FAN1, FAN4, FAN5 初始设为默认速度 15%
    "FAN0": [["raw", "0x30", "0x30", "0x02", "0x00", "0x0f"]],
    "FAN1": [["raw", "0x30", "0x30", "0x02", "0x01", "0x0f"]],
    "FAN4": [["raw", "0x30", "0x30", "0x02", "0x04", "0x0f"]],
    "FAN5": [["raw", "0x30", "0x30", "0x02", "0x05", "0x0f"]]
}

# 设置日志记录
logger = logging.getLogger("fanctl")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_file, maxBytes=log_max_bytes, backupCount=log_backup_count)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 记录消息到日志文件和syslog
def log_message(message):
    logger.info(message)
    syslog.syslog(syslog.LOG_INFO, message)

# 切换风扇至自动模式
def autofan():
    result = subprocess.run([ipmiexe] + fanauto, capture_output=True)
    log_message(f"Set fans to auto mode: {result.returncode}, {result.stdout}, {result.stderr}")
    return

# 设置指定风扇的速度
def setfanspeed(fan, setspeed):
    global fanmode
    fanmode = 'static'
    result = subprocess.run([ipmiexe] + fanmanual, capture_output=True)
    log_message(f"Set fan mode to manual: {result.returncode}, {result.stdout}, {result.stderr}")

    result = subprocess.run([ipmiexe] + setspeed, capture_output=True)
    log_message(f"Set {fan} speed to {int(setspeed[-1], 16)}%: {result.returncode}, {result.stdout}, {result.stderr}")
    return

# 获取CPU温度
def getcputemps():
    temps = [0.0, 0.0]
    try:
        # 使用IPMI工具获取CPU温度
        ipmiproc = [ipmiexe, "sensor", "list"]
        result = subprocess.run(ipmiproc, capture_output=True)
        output = result.stdout.decode()
        
        # 解析IPMI输出以获取温度信息
        lines = output.splitlines()
        if len(lines) > 16:
            temp1_line = lines[14]
            temp2_line = lines[15]
            
            match_temp1 = re.search(r'(\d+\.\d+)', temp1_line)
            match_temp2 = re.search(r'(\d+\.\d+)', temp2_line)
            
            if match_temp1:
                temps[0] = float(match_temp1.group(1))
            if match_temp2:
                temps[1] = float(match_temp2.group(1))
        
        log_message(f"CPU1 Temp: {temps[0]}")
        log_message(f"CPU2 Temp: {temps[1]}")
    except Exception as ipmierror:
        # 发生异常时，切换风扇至自动模式并记录错误日志
        autofan()
        log_message(f"Cannot get IPMI temps: {ipmierror}")
        syslog.syslog(syslog.LOG_ERR, str(ipmierror))
    return temps

# 设置其他风扇的默认速度
def set_default_fan_speeds():
    for fan in ["FAN0", "FAN1", "FAN4", "FAN5"]:
        try:
            setfanspeed(fan, fanspeeds[fan][0])
        except Exception as ipmierror:
            log_message(f"Setting {fan} speed failed: {ipmierror}")
            syslog.syslog(syslog.LOG_ERR, str(ipmierror))

# 信号处理函数
def signal_handler(signal_id, frame):
    log_message(f"Signal ID - {signal.Signals(signal_id)} received")
    if signal_id == signal.SIGUSR1:
        os.remove(PIDFILE)  # 删除PID文件
        sys.exit(0)

# 注册信号处理函数
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGABRT, signal_handler)
signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGQUIT, signal_handler)
signal.signal(signal.SIGUSR1, signal_handler)

# 主程序入口
if __name__ == '__main__':
    log_message(f"Starting fan control - Interval of {pausetime} seconds")
    set_default_fan_speeds()  # 设置其他风扇的默认速度
    while True:
        # 在每次循环的开始添加分隔符
        log_message("="*40)
        try:
            temp1, temp2 = getcputemps()  # 获取CPU温度
        except Exception as ipmierror:
            autofan()  # 获取温度异常时切换风扇至自动模式
            log_message("Cannot get IPMI temps")
            temp1 = prevtemp1
            temp2 = prevtemp2

        # 处理每个风扇的温度和速度设定逻辑
        for i, (temp, prevtemp, fan) in enumerate(zip([temp1, temp2], [prevtemp1, prevtemp2], ["FAN2", "FAN3"])):
            log_message(f"Processing {fan} with temp {temp}C and prevtemp {prevtemp}C")
            log_message(f"Current fan mode: {fanmode}")
            log_message(f"Current temp thresholds: {temp_thresholds}")
            if temp != prevtemp:
                try:
                    if temp >= returntoauto and fanmode == "static":
                        autofan()
                        fanmode = "auto"
                        log_message(f"Temperature {temp}C >= {returntoauto}C, switching to auto mode")
                    else:
                        # 根据温度阈值设置风扇速度
                        if temp < temp_thresholds[0]:
                            setspeed = fanspeeds[fan][0]
                        elif temp >= temp_thresholds[0] and temp < temp_thresholds[1]:
                            setspeed = fanspeeds[fan][1]
                        elif temp >= temp_thresholds[1] and temp < temp_thresholds[2]:
                            setspeed = fanspeeds[fan][2]
                        elif temp >= temp_thresholds[2] and temp < temp_thresholds[3]:
                            setspeed = fanspeeds[fan][3]
                        elif temp >= temp_thresholds[3] and temp < temp_thresholds[4]:
                            setspeed = fanspeeds[fan][4]
                        elif temp >= temp_thresholds[4]:
                            autofan()
                            fanmode = "auto"
                            log_message(f"Temperature {temp}C >= {temp_thresholds[4]}C, switching to auto mode")
                            setspeed = fanspeeds[fan][0]  # 设置默认速度，当温度 >= 65°C时

                        setfanspeed(fan, setspeed)  # 设置风扇速度
                        log_message(f"Setting {fan} speed to {int(setspeed[-1], 16)}%")
                except Exception as ipmierror:
                    autofan()  # 设定风扇速度失败时切换风扇至自动模式
                    log_message(f"Setting fan speed failed: {ipmierror}")
                    syslog.syslog(syslog.LOG_ERR, str(ipmierror))
            if i == 0:
                prevtemp1 = temp  # 更新CPU1上次温度
            else:
                prevtemp2 = temp  # 更新CPU2上次温度
        
        # 记录CPU温度和风扇设定速度的对应关系
        fan_speed_info = (
            f"CPU1 Temp: {temp1}C, FAN2 Speed: {int(fanspeeds['FAN2'][min(4, sum(temp1 >= t for t in temp_thresholds))][-1], 16)}%\n"
            f"CPU2 Temp: {temp2}C, FAN3 Speed: {int(fanspeeds['FAN3'][min(4, sum(temp2 >= t for t in temp_thresholds))][-1], 16)}%"
        )
        log_message(f"CPU and Fan Speed Correspondence:\n{fan_speed_info}")

        time.sleep(pausetime)  # 暂停一段时间后继续执行

    sys.exit()  # 退�
