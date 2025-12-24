from typing import List
from pydantic import BaseModel


class OperatorConfig(BaseModel):
    name: str
    url: str
    priority: int
    timeout: int = 5


OPERATORS: List[OperatorConfig] = [
    OperatorConfig(name="operator_1", url="http://mock_operator_1:9000/send", priority=1),
    OperatorConfig(name="operator_2", url="http://mock_operator_2:9001/send", priority=2),
    OperatorConfig(name="operator_3", url="http://mock_operator_3:9002/send", priority=3),
]
