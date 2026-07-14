from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Lichess
    lichess_api_url: str = "https://explorer.lichess.org"
    lichess_api_token: SecretStr = SecretStr("")

    # YouTube
    youtube_api_key: str = ""

    # Milvus
    milvus_host: str = "milvus-standalone"
    milvus_port: int = 19530
    milvus_collection_name: str = "chess_openings"

    # MongoDB
    mongo_uri: str = "mongodb://mongo:27017"
    mongo_db_name: str = "chess_agent"

    # Mistral AI (LLM pour formuler les réponses)
    mistral_api_key: str = ""
    mistral_model: str = "mistral-small"

    # Stockfish
    stockfish_path: str = "/usr/games/stockfish"


settings = Settings()
