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

# 配置日志记录
log_file = '/var/log/fanctl.log'
log_max_size = 10 * 1024 * 1024  # 最大日志文件大小（字节），这里设置为10MB
log_backup_count = 5  # 保留的旧日志文件数量

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 设置日志处理器为RotatingFileHandler
handler = RotatingFileHandler(log_file, maxBytes=log_max_size, backupCount=log_backup_count)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 全局变量设置
pausetime = 10  # 循环暂停时间（秒）
ipmiexe = "/vmfs/volumes/datastore1/opt/ipmitool/ipmitool"  # IPMI工具路径
temp = 0.0  # 当前CPU温度
prevtemp = 0.0  # 上一次记录的CPU温度
fanmode = "static"  # 风扇模式，默认为静态
logmsg = ""  # 日志消息

PIDFILE = "/var/run/fanctl.pid"  # PID文件路径
# IPMI命令 - 切换至自动风扇模式
fanauto = ["0x30", "0x30", "0x01", "0x01"]  
# IPMI命令 - 切换至手动/静态风扇模式
fanmanual = ["0x30", "0x30", "0x01", "0x00"]  
returntoauto = 65.0  # 当CPU温度高于等于此值时，切换回自动风扇模式
temp1 = 40.0  # 温度阈值1
temp2 = 45.0  # 温度阈值2
temp3 = 50.0  # 温度阈值3
temp4 = 55.0  # 温度阈值4
# 风扇速度设置（以十六进制表示的百分比）
fanspeed0 = ["0x30", "0x30", "0x02", "0xff", "0x19"]  # 25%
fanspeed1 = ["0x30", "0x30", "0x02", "0xff", "0x1c"]  # 28%
fanspeed2 = ["0x30", "0x30", "0x02", "0xff", "0x1e"]  # 30%
fanspeed3 = ["0x30", "0x30", "0x02", "0xff", "0x23"]  # 35%
fanspeed4 = ["0x30", "0x30", "0x02", "0xff", "0x28"]  # 40%

current_fanspeed = None  # 当前风扇速度

# 切换风扇至自动模式
def autofan():
    global fanmode
    rawtxt = ["raw"] + fanauto
    result = subprocess.run([ipmiexe] + rawtxt, capture_output=True)
    fanmode = "auto"
    logger.info(f"Switched to auto fan mode: {result}")
    return

# 设置风扇速度
def setfanspeed(setspeed):
    global current_fanspeed
    speed_percentage = int(setspeed[-1], 16)  # 将风扇速度从十六进制转换为整数表示的百分比
    if current_fanspeed != speed_percentage:  # 如果当前速度与目标速度不同，则设置新速度
        try:
            ipmiproc = [ipmiexe, "raw"] + setspeed
            subprocess.run(ipmiproc, check=True, capture_output=True)
            current_fanspeed = speed_percentage
            logger.info(f"Set fan speed to {speed_percentage}% (from {prevtemp}C to {temp}C)")
        except subprocess.CalledProcessError as e:
            autofan()  # 设置失败时切换至自动模式
            logger.error(f"Setting fan speed failed: {e}")

# 启用手动风扇模式
def enable_manual_mode():
    global fanmode
    try:
        ipmiproc = [ipmiexe, "raw"] + fanmanual
        subprocess.run(ipmiproc, check=True, capture_output=True)
        fanmode = "static"
        logger.debug(f"Manual fan mode enabled: {ipmiproc}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Enabling manual mode failed: {e}")

# 获取CPU温度
def getcputemp():
    curtemp = 0
    try:
        ipmiproc = [ipmiexe, "sensor", "reading", "Temp"]
        result = subprocess.run(ipmiproc, capture_output=True, check=True)
        parsetemp = re.compile(r'(\d+(\.\d+)?)')  # 正则表达式匹配温度值
        match = parsetemp.search(result.stdout.decode())
        if match:
            curtemp = float(match.group())  # 提取并转换温度值
        else:
            raise ValueError("CPU temperature pattern not found")
        logger.debug(f"Current CPU temperature: {curtemp}")
    except (subprocess.CalledProcessError, ValueError) as ipmierror:
        autofan()  # 获取温度失败时切换至自动模式
        logger.error(f"Cannot get IPMI temp: {ipmierror}")
    return curtemp

# 信号处理函数
def signal_handler(signal_id, frame):
    logmsg = f"Signal ID - {signal.Signals(signal_id)} received"
    logger.info(logmsg)
    if signal_id == signal.SIGUSR1:
        if os.path.exists(PIDFILE):
            os.remove(PIDFILE)
        sys.exit(0)

# 注册信号处理函数
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGABRT, signal_handler)
signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGQUIT, signal_handler)
signal.signal(signal.SIGUSR1, signal_handler)

if __name__ == '__main__':
    logmsg = f"Starting fan control - Interval of {pausetime} seconds"
    logger.info(logmsg)

    # 确保在开始时启用手动模式
    enable_manual_mode()

    while True:
        try:
            temp = getcputemp()  # 获取当前CPU温度
        except Exception as ipmierror:
            autofan()  # 获取温度失败时切换至自动模式
            logger.error(f"Cannot get IPMI temp: {ipmierror}")

        if temp != prevtemp:  # 如果温度变化
            try:
                if temp >= returntoauto and fanmode == "static":
                    autofan()  # 温度高于阈值时切换至自动模式
                    logger.info(f"Switching to auto mode at {temp}C")
                elif temp < returntoauto and fanmode == "auto":
                    enable_manual_mode()  # 温度低于阈值时切换回手动模式
                    logger.info(f"Returning to manual mode at {temp}C")

                if fanmode == "static":
                    # 根据温度设置风扇速度
                    if temp >= temp4 and prevtemp < temp4:
                        setfanspeed(fanspeed4)
                    elif temp >= temp3 and prevtemp < temp3:
                        setfanspeed(fanspeed3)
                    elif temp >= temp2 and prevtemp < temp2:
                        setfanspeed(fanspeed2)
                    elif temp >= temp1 and prevtemp < temp1:
                        setfanspeed(fanspeed1)
                    elif temp < temp1 and prevtemp >= temp1:
                        setfanspeed(fanspeed0)
                    elif temp < temp4 and prevtemp >= temp4:
                        setfanspeed(fanspeed3)
                    elif temp < temp3 and prevtemp >= temp3:
                        setfanspeed(fanspeed2)
                    elif temp < temp2 and prevtemp >= temp2:
                        setfanspeed(fanspeed1)
            except Exception as ipmierror:
                autofan()  # 设置风扇速度失败时切换至自动模式
                logger.error(f"Setting fan speed failed: {ipmierror}")
        prevtemp = temp  # 更新上一次温度记录
        time.sleep(pausetime)  # 暂停一段时间后继续执行

sys.exit()
