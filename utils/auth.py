# Standard Libraries
import os
from datetime import timedelta, timezone, datetime


# Local Modules

# Third-party Libraries
from jwt import PyJWTError, decode, encode
from dotenv import load_dotenv

load_dotenv()

""" Structure
H.P.S - Header.Payload.Signature
"""

class JWTService:
    def __init__(self) -> None:
        self.__secret_key: str = os.getenv("SECRET_KEY", '')
        self.__algorithm: str = os.getenv("ALGORITHM", 'HS256')
        self.__access_exp: timedelta = timedelta(
            minutes=int(os.getenv("ACCESS_EXP", 10))
        )
        self.__refresh_exp: timedelta = timedelta(
            days=int(os.getenv("REFRESH_EXP", 3))
        )


    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        exp = datetime.now(timezone.utc) + self.__access_exp
        to_encode.update({"exp": exp.timestamp(), "type": "access"})

        return encode(to_encode, self.__secret_key, self.__algorithm)


    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        exp = datetime.now(timezone.utc) + self.__refresh_exp
        to_encode.update({"exp": exp.timestamp(), "type": "refresh"})

        return encode(to_encode, self.__secret_key, self.__algorithm)


    def verify_token(self, token: str) -> dict | None:
        try:
            payload = decode(token, self.__secret_key, self.__algorithm)
            return payload
        except PyJWTError:
            return None

    
    def refresh_access_token(self, token: str) -> str | None:
        payload = self.verify_token(token)

        if not payload or payload.get("type") != "refresh" or payload.get("is_revoked") == True:
            return None
        
        new_payload = {
            k: v for k, v in payload.items() if k not in ["exp", "type"]
        }

        return self.create_access_token(new_payload)
    

jwt_service = JWTService()
