import requests
import plugins
from plugins import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger

PRICE_CHECK_URL = "https://www.hhlqilongzhu.cn/api/yjcx.php"

@plugins.register(name="query_oil_price",
                  desc="查询油价",
                  version="1.0",
                  author="azad",
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
        if content.startswith("油价") and " " in content:
            province_query = content.split("油价", 1)[1].strip()
            province_name_for_display = province_query.replace("省", "")  # 去除省份名称中的“省”字
            logger.info(f"[{__class__.__name__}] 收到油价查询请求: {province_query}")
            reply = Reply()
            result = self.get_oil_price(province_name_for_display)
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
        params = {"msg": province}
        try:
            response = requests.get(url=PRICE_CHECK_URL, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                province_data = data["data"]["provinceData"]
                formatted_output = f"{province}的油价信息：\n"
                oil_types = ["GAS_92", "GAS_95", "GAS_98", "CHECHAI_0"]
                for oil_type in oil_types:
                    if oil_type in province_data:
                        if oil_type == "CHECHAI_0":
                            gas_type = "0号柴油"
                        else:
                            gas_type = f"{oil_type[4:].replace('_', '号')}汽油"
                        price = province_data[oil_type]
                        formatted_output += f"{gas_type}: {price}元/升\n"
                
                # 添加油价生效起始日期
                start_date = province_data.get("START_DATE", "未知")
                formatted_output += f"油价更新时间: {start_date}\n"
                
                return formatted_output.strip()
            else:
                logger.error(f"接口返回值异常: {response.text}")
                return None
        except Exception as e:
            logger.error(f"接口异常：{e}")
            return None
