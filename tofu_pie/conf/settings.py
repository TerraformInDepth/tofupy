from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "tofu_pie"
    debug: bool = False
