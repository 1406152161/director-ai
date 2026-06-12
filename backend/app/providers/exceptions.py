# @author zhangzhihao
"""Provider 层异常定义。"""


class ProviderError(Exception):
    """Provider 调用基础异常。"""


class ProviderAuthError(ProviderError):
    """API 认证失败（401）。"""


class ProviderBadRequestError(ProviderError):
    """请求参数错误（400）。"""


class ProviderTimeoutError(ProviderError):
    """请求超时。"""
