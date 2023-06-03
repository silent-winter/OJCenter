import json
import logging
from datetime import datetime
from http.cookies import SimpleCookie

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from OJcenter.Tool import redisTool, systemTool, userTool, messageTool


class BaseConsumer(AsyncJsonWebsocketConsumer):
    """vscode统一consumer类

    websocket消息统一采用如下json格式：
    {
        "type": "${msg_type}"
        "body": {
            ...
        }
    }
    通过type转发到不同handler处理

    """

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.group_name = None
        self.username = None

    async def connect(self):
        is_auth = await self.check_auth()
        if not is_auth:
            await self.accept()
            await self.close(code=4003)
            return
        # 防止多开, 检查group里是否有其他连接
        count = getattr(self.channel_layer, self.group_name, 0)
        setattr(self.channel_layer, self.group_name, count + 1)
        if count > 0:
            # 已经有其他连接, 关闭本连接
            await self.accept()
            await self.close(code=4004)
        else:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        if self.group_name:
            count = getattr(self.channel_layer, self.group_name, 0)
            setattr(self.channel_layer, self.group_name, count - 1)
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def check_auth(self):
        cookie_header = next((x[1] for x in self.scope['headers'] if x[0].decode('utf-8').lower() == 'cookie'), None)
        if cookie_header:
            cookie_str = cookie_header.decode('utf-8')
            cookies = SimpleCookie(cookie_str)
            session_id = cookies.get('PHPSESSID')
            if not session_id:
                return False
            session_id = session_id.value
            self.username = systemTool.getPHPUserName(session_id)
            if self.username is None:
                return False
            self.group_name = 'user_' + self.username
            return True
        else:
            return False

    async def receive_json(self, content, **kwargs):
        logging.info("websocket data from {}: {}".format(self.username, json.dumps(content)))
        msg_type = content['type']
        await {
            'check-status': self.handle_check_status,
            # 'heartbeat': self.handle_heartbeat,
            'unlock-time': self.handle_unlock_time,
            'refresh-info': self.handle_refresh_info,
            'query-notice': self.handle_query_notice,
            'save-log': self.handle_save_log
        }[msg_type](content['body'])

    async def handle_check_status(self, body):
        """
        用户复制、粘贴等行为处理
        """
        userTool.updateUserStatus(self.username, body["status"], body["detail"])

    async def handle_unlock_time(self, body):
        """
        实时更新解封时间
        """
        unlock_time = await userTool.get_unlock_time(self.username)
        if unlock_time is None:
            await self.send_json({"type": "unlock-time", "body": {"result": -1}})
            return
        now = timezone.now()
        date = datetime.strptime(unlock_time, '%Y-%m-%d %H:%M:%S')
        diff = date - now
        days, remaining_seconds = diff.days, diff.seconds
        # 获取小时和剩余的秒数
        hours, remaining_seconds = divmod(remaining_seconds, 3600)
        # 获取分钟和剩余的秒数
        minutes, seconds = divmod(remaining_seconds, 60)
        response_msg = {"type": "unlock-time",
                        "body": {"result": 1, "days": days, "hours": hours, "minutes": minutes, "seconds": seconds}}
        await self.send_json(response_msg)

    # async def handle_heartbeat(self, body):
    #     """
    #     心跳包，接受消息后刷新用户token过期时间
    #     """
    #     session_id = body['session']
    #     username = systemTool.getPHPUserName(session_id)
    #     if username is None:
    #         # response_msg = {"type": "heartbeat", "body": {"result": 1, "order": None}}
    #         await self.close(code=4999)
    #     else:
    #         order = 0 if redisTool.queryUser(self.username) else systemTool.getOrder(self.username)
    #         response_msg = {"type": "heartbeat", "body": {"result": 1, "order": order}}
    #         await self.send_json(response_msg)

    async def handle_refresh_info(self, body):
        """
        统计当前系统在线人数（keys UserToken:*）, 并刷新页面信息
        """
        count = redisTool.countUser()
        order = 0 if redisTool.queryUser(self.username) else systemTool.getOrder(self.username)
        lock = await userTool.is_lock(self.username)
        response_msg = {"type": "refresh-info",
                        "body": {"result": 1, "count": count, "order": order, "lock": 1 if lock else 0}}
        await self.send_json(response_msg)

    async def handle_query_notice(self, body):
        """
        查询数据库是否有即时通知
        """
        content = await messageTool.query_message_new(self.username)
        if content:
            await self.send_json({'type': "notice", 'body': {'message': content}})

    async def handle_save_log(self, body):
        """
        保存消息阅读记录
        """
        await messageTool.save_message_read_log(self.username, body['notification_id'])

    async def send_notice_message(self, event):
        await self.send_json(event['message'])

    async def close_ws(self, event):
        await self.close(code=4005)
