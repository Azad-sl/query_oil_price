import requests
import plugins
from plugins import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger

# 新的油价查询API的基础URL
OIL_PRICE_API_URL = "https://api.qqsuu.cn/api/dm-oilprice"

@plugins.register(name="query_oil_price",
                  desc="查询油价",
                  version="1.0",
                  author="Azad",
                  desire_priority=100)
class query_oil_price(Plugin):

    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info(f"[{__class__.__name__}] inited")

    def get_help_text(self, **kwargs):
        help_text = "发送【油价 对应省份】查询对应省份的油价"
        return help_text

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return
        content = e_context["context"].content.strip()
        # 检查是否是油价查询的指令
        if content.startswith("油价") and " " in content:
            province = content.split("油价", 1)[1].strip()
            logger.info(f"[{__class__.__name__}] 收到油价查询请求: {province}")
            reply = Reply()
            result = self.get_oil_price(province)
            if result:
                reply.type = ReplyType.TEXT
                reply.content = result
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                reply.type = ReplyType.ERROR
                reply.content = "获取油价失败，请稍后再试。"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS

    def get_oil_price(self, province):
        params = {"prov": province}
        try:
            response = requests.get(url=OIL_PRICE_API_URL, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data["code"] == 200:
                    province_data = data["data"]
                    formatted_output = f"{province_data['prov']}的油价信息（更新时间：{province_data['time']}）：\n"
                    oil_types = ["p0", "p89", "p92", "p95", "p98"]
                    for oil_type in oil_types:
                        if oil_type in province_data:
                            price = province_data[oil_type]
                            if oil_type == "p0":
                                gas_type = "0号柴油"
                            elif oil_type == "p89":
                                gas_type = "89号汽油"
                            else:
                                gas_type = f"{oil_type[1:]}号汽油"
                            formatted_output += f"{gas_type}: {price}元/升\n"
                    return formatted_output.strip()
                else:
                    logger.error(f"API返回错误信息: {data['msg']}")
                    return None
            else:
                logger.error(f"接口返回值异常: 状态码 {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"接口异常：{e}")
            return None
