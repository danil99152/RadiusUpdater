import logging

from service.model import ModelService


class ModelApi:
    __slots__ = ['model']

    def __init__(self) -> None:
        self.model = ModelService()

    @staticmethod
    def ping() -> str:
        result_bool_obj: str = 'pong'
        return result_bool_obj

    async def update(self, filepath: str, ):
        logging.debug(filepath)
        result = self.model.update(filepath)
        return result
