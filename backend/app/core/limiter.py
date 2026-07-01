# @author zhangzhihao
"""全局限流器（slowapi）；测试环境由 conftest 关闭。"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
