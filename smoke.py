# import psutil
# import win32com.client
import json
import time
import os
import re
import subprocess
import datetime
import http.client
from ftplib import FTP
import signal            


#################新包检测################

reqheaders={'Content-type':'application/json'}
            
ftp=FTP()        

def exit(signum, frame):
    print('程序退出，断开连接.')
    ftp.quit() 
signal.signal(signal.SIGINT, exit)
signal.signal(signal.SIGTERM, exit)       

# ip = "10.10.43.155"
# dir_base = "/test/"
ip = "10.10.75.224"
# ip = "192.168.1.108"
dir_base = "/pub/xl9/InstallPack/10.1.0.x/"
# log_dir = 'D:\\Git\\xl9checklist\\'
log_dir = 'D:\\AutoTest\\thunderx\\'

ftp.connect(ip)
ftp.login()

today0 = ""

#检查指定的目录是否有新文件
def checknewfile(dir,files):
    #先获取当前的文件
    try:
        nowfiles = ftp.nlst(dir)
    except Exception as e:
        print(e)
        return []
    print(nowfiles)
    #和上次获取的比较，如果不一致，则有新文件
    dif = set(nowfiles)-set(files)
    if  dif != set():
        #新文件可能正在上传，所以要等上传完成，判断方法是一段时间内文件大小无变化则上传完成
        dict = {} #记录文件的大小
        for f in dif:
            if "/" in f: #有的返回带路径，有的不带，这里处理一下
                fl = f
            else:
                fl = dir+"/"+f
            print(fl)
            dict[f] = ftp.size(fl)
        while True: #循环监控文件大小
            time.sleep(10)
            flag = True
            for f in dif:
                if "/" in f: #有的返回带路径，有的不带，这里处理一下
                    fl = f
                else:
                    fl = dir+"/"+f
                tmpsize = ftp.size(fl)
                if tmpsize != dict[f]: #判断文件大小是否变化
                    dict[f] = tmpsize
                    flag = False
            print(dict)
            if flag: #所有文件的大小都没有变化，退出循环
                break
        # print("new files:"+str(dif))
        
        have_log = 0
        for f in dif:
            file = os.path.split(f)[1] # 取文件名
            mo = re.match("[a-zA-Z]+(\d+)\.(\d+)\.(\d+)\.(\d+)",file)
            if mo:
                print(mo.group(1),mo.group(2),mo.group(3),mo.group(4))
                if int(mo.group(4))%2 == 0: #pr版才获取更新内容
                    oldcwd = os.getcwd()
                    print(oldcwd) 
                    since = ""
                    try:
                        with open("sincetime.txt") as f:
                            since = f.read()
                    except Exception as e:
                        print(e)
                    if since == "" or since[0] != "\"":
                        since = "\""+since+"\""
                    print(since)
                    until = datetime.datetime.now() - datetime.timedelta(minutes=10)
                    until = "\""+str(until)+"\""
                    print(until)
                    with open("sincetime.txt","w") as f:
                        f.write(until)    
                        
                    os.chdir(log_dir) 
                    # print(os.getcwd())
                    cmd = "git pull"
                    print(cmd)
                    os.system(cmd)
                    cmd = "git shortlog --no-merges --since="+since+" --until="+until
                    print(cmd)
                    sub=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
                    sub.wait()
                    changelog = sub.stdout.read().decode()
                    have_log = 1
                    print(changelog)
                    os.chdir(oldcwd)
                    # print(os.getcwd())
                    break

        conn=http.client.HTTPSConnection('oapi.dingtalk.com') #提醒
        url = []
        for f in dif:
            if "/" in f: #有的返回带路径，有的不带，这里处理一下
                fl = f
            else:
                fl = dir+"/"+f
            url.append("ftp://"+ip+fl)
            # pkgreqdata={"msgtype": "link", "link": {"title":"新包","text":url,"messageUrl":url}}
        if have_log == 1:
            content = "新包："+"\n".join(url)+"\n修改内容:\n"+changelog
        else:
            content = "新包："+"\n".join(url)
        pkgreqdata={"msgtype": "text", "text": {"content": content}}
        pkgdata=json.dumps(pkgreqdata)
        # conn.request('POST', '/robot/send?access_token=f2542b18cf2aba67775a209fa9341337a1a2fc9388ceb45f439eea9f87856c9e', pkgdata, reqheaders)
        conn.request('POST', '/robot/send?access_token=5690f1251e1c4fb8582de4f7321805632dc822bfdd6255224e71df753fab2f9a', pkgdata, reqheaders)
        res=conn.getresponse()
        # print(res.status)
        # print(res.msg)
    return nowfiles
#########################################

# main loop
for i in range(0,144000): # 100 days
# for i in range(0,2):

    if i % 60 == 0: # record the time every one hour
        print("\n")
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

#############新包检测################
    if os.path.exists("check_dir.txt"):
        with open("check_dir.txt") as f:
            dir_base = f.read()
    today = time.strftime('%y%m%d',time.localtime())
    if today != today0: #过了一天，要重新获取
        today0 = today
        yt = datetime.date.today() - datetime.timedelta(days=1)
        yesterday = str(yt).replace("-","")[2:]

        #获取今天和昨天目录的文件
        try:
            tfiles = ftp.nlst(dir_base+today)
        except Exception as e:
            print(e)
            tfiles = []
            
        try:
            yfiles = ftp.nlst(dir_base+yesterday)
        except Exception as e:
            print(e)
            yfiles = []
            
        # print(tfiles)
        # print(yfiles)
    tfiles = checknewfile(dir_base+today,tfiles)
    yfiles = checknewfile(dir_base+yesterday,yfiles)
#####################################
    
    time.sleep(60)
    
    
