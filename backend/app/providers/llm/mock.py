# @author zhangzhihao
"""LLM Provider 占位实现。"""

from app.providers.base import Message


class MockLLMProvider:
    """返回 mock 分镜脚本，M1 接入真实 LLM API。"""

    async def chat(self, messages: list[Message], **kwargs: object) -> str:
        # TODO: 接入 DeepSeek / OpenAI 等厂商
        user_content = messages[-1].content if messages else ""
        return (
            f'{{"story": "{user_content}", "shots": ['
            '{"id": 1, "narration": "开场", "visual": "远景镜头", "duration": 5}'
            "]}"
        )
