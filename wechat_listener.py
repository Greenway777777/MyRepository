# coding:utf-8
import itchat
from itchat.content import TEXT
from itchat.content import *
import time
import re
import os
import importlib,sys

importlib.reload(sys)


msg_information = {}
face_bug=None  #针对表情包的内容


@itchat.msg_register([TEXT, PICTURE, FRIENDS, CARD, MAP, SHARING, RECORDING, ATTACHMENT, VIDEO],isFriendChat=True, isGroupChat=True, isMpChat=True)
def handle_receive_msg(msg):
    global face_bug
    msg_time_rec = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())   #接受消息的时间
    # ActualNickName : 实际 NickName(昵称) 群消息里(msg)才有这个值
    if 'ActualNickName' in msg:
        from_user = msg['ActualUserName'] #群消息的发送者,用户的唯一标识
        msg_from = msg['ActualNickName']#发送者群内的昵称
        friends = itchat.get_friends(update=True)#获取所有好友
        for f in friends:
            if from_user == f['UserName']: #如果群消息是好友发的
                if f['RemarkName']: # 优先使用好友的备注名称，没有则使用昵称
                    msg_from = f['RemarkName']
                else:
                    msg_from = f['NickName']
                break
        groups = itchat.get_chatrooms(update=True)#获取所有的群
        for g in groups:
            if msg['FromUserName'] == g['UserName']:#根据群消息的FromUserName匹配是哪个群
                group_name = g['NickName']
                group_menbers = g['MemberCount']
                break
        group_name = group_name + "(" + str(group_menbers) +")"
        #否则的话是属于个人朋友的消息
    else:
        if itchat.search_friends(userName=msg['FromUserName'])['RemarkName']:#优先使用备注名称
            msg_from = itchat.search_friends(userName=msg['FromUserName'])['RemarkName']
        else:
            msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName'] #在好友列表中查询发送信息的好友昵称
        group_name = ""
    msg_time = msg['CreateTime'] #信息发送的时间
    msg_id = msg['MsgId']    #每条信息的id
    msg_content = None      #储存信息的内容
    msg_share_url = None    #储存分享的链接，比如分享的文章和音乐
    print(msg['Type'])
    print(msg['MsgId'])
    if msg['Type'] == 'Text' or msg['Type'] == 'Friends':     #如果发送的消息是文本或者好友推荐
        msg_content = msg['Text']
        print(msg_content)

    #如果发送的消息是附件、视屏、图片、语音
    elif msg['Type'] == "Attachment" or msg['Type'] == "Video" \
            or msg['Type'] == 'Picture' \
            or msg['Type'] == 'Recording':
        msg_content = msg['FileName']    #内容就是他们的文件名
        msg['Text'](str(msg_content))    #下载文件
        # print msg_content
    elif msg['Type'] == 'Card':    #如果消息是推荐的名片
        msg_content = msg['RecommendInfo']['NickName'] + '的名片'    #内容就是推荐人的昵称和性别
        if msg['RecommendInfo']['Sex'] == 1:
            msg_content += '性别为男'
        else:
            msg_content += '性别为女'

        print(msg_content)
    elif msg['Type'] == 'Map':    #如果消息为分享的位置信息
        x, y, location = re.search(
            "<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*", msg['OriContent']).group(1, 2, 3)
        if location is None:
            msg_content = r"纬度->" + x.__str__() + " 经度->" + y.__str__()     #内容为详细的地址
        else:
            msg_content = r"" + location
    elif msg['Type'] == 'Sharing':     #如果消息为分享的音乐或者文章，详细的内容为文章的标题或者是分享的名字
        msg_content = msg['Text']
        msg_share_url = msg['Url']       #记录分享的url
        print(msg_share_url)
    face_bug=msg_content

#将信息存储在字典中，每一个msg_id对应一条信息
    msg_information.update(
        {
            msg_id: {
                "msg_from": msg_from,
                "msg_time": msg_time,
                "msg_time_rec": msg_time_rec,
                "msg_type": msg["Type"],
                "msg_content": msg_content,
                "msg_share_url": msg_share_url,
                "group_name":group_name
            }
        }
    )
     #自动删除130秒之前的消息，避免数据量太大后引起内存不足
    del_info = []
    for k in msg_information:
        m_time = msg_information[k]['msg_time'] #取得消息时间
        if int(time.time()) - m_time > 180:
            del_files(path)
            del_info.append(k)
    if del_info:
        for i in del_info:
            msg_information.pop(i)


##这个是用于监听是否有消息撤回
@itchat.msg_register(NOTE, isFriendChat=True, isGroupChat=True, isMpChat=True)
def information(msg):
    #这里如果这里的msg['Content']中包含消息撤回和id，就执行下面的语句
    if '撤回了一条消息' in msg['Content']:
        old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)   #在返回的content查找撤回的消息的id
        old_msg = msg_information.get(old_msg_id)    #得到消息
        print(old_msg)
        if len(old_msg_id)<11:  #如果发送的是表情包
            itchat.send_file(face_bug,toUserName='filehelper')
        else:  #发送撤回的提示给文件助手
            msg_body = "火眼金睛号提示您：" + "\n" \
                       + old_msg.get('msg_time_rec') + "\n" \
                       + old_msg['group_name'] \
                       + old_msg.get('msg_from') + " 撤回了一条 " + old_msg.get("msg_type") + " 消息" + "\n" \
                       + "内容如下⇣" + "\n" \
                       + r"" + old_msg.get('msg_content')
            #如果是分享的文件被撤回了，那么就将分享的url加在msg_body中发送给文件助手
            if old_msg['msg_type'] == "Sharing":
                msg_body += "\n就是这个链接➣ " + old_msg.get('msg_share_url')
            # 将撤回消息发送到文件助手
            itchat.send_msg(msg_body, toUserName='filehelper')
            # 有文件的话也要将文件发送回去
            if old_msg["msg_type"] == "Picture" \
                    or old_msg["msg_type"] == "Recording" \
                    or old_msg["msg_type"] == "Video" \
                    or old_msg["msg_type"] == "Attachment":
                file = '@fil@%s' % (old_msg['msg_content'])
                itchat.send(msg=file, toUserName='filehelper')
                os.remove(old_msg['msg_content'])
            # 删除字典旧消息
            msg_information.pop(old_msg_id)
def del_files(path):
    for root , dirs, files in os.walk(path):
        for name in files:
            if name.endswith(".gif") or name.endswith(".mp4") or name.endswith(".png") or name.endswith(".jpg"):
                os.remove(os.path.join(root, name))
                print ("Delete File: " + os.path.join(root, name))
path=os.path.split(os.path.realpath(__file__))[0]
itchat.auto_login(hotReload=True)
itchat.run()
