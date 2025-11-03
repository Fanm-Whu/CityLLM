from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

class ParseResult(BaseModel):
    """解析结果数据结构"""
    location: str = Field(..., description="提取出的地点信息，如未明确提及则为空字符串")
    time: str = Field(..., description="提取出的时间信息，如未明确提及则为空字符串")
    data_requirement: str = Field(..., description="用户的数据需求描述")
    original_input: str = Field(..., description="原始用户输入文本")

class InterParserAgent:
    """自然语言解析Agent，将用户输入解析为结构化数据"""

    def __init__(self, llm):
        # 解析提示模板
        self.parse_prompt = PromptTemplate(
            input_variables=["input"],
            template="""
            你的任务是从用户输入中提取以下结构化信息:
            1. 地点 (location): 明确的地址或POI名称
            2. 时间 (time): 具体时间点或时间段
            3. 数据需求 (data_requirement): 用户需要什么数据
            4. 原始输入 (original_input): 完整的原始输入内容

            按以下JSON格式输出:
            {{
                "location": "...",
                "time": "...",
                "data_requirement": "...",
                "original_input": "..."
            }}

            用户输入:
            {input}
            """
        )
        self.parser_chain = LLMChain(
            llm=llm,
            prompt=self.parse_prompt,
            output_key="parsed"
        )

    def parse(self, user_input: str) -> ParseResult:
        """解析用户输入"""
        response = self.parser_chain.run(input=user_input)
        # 返回结构化结果
        return ParseResult.parse_raw(response)