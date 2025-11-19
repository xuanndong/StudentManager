import bcrypt
import os
from datetime import datetime, timedelta, timezone
from jose import jwt
from dotenv import load_dotenv


# Load .env file
load_dotenv()


""" Structure
H.P.S ~ Header.Payload.Signature
"""

class JWTService:
    def __init__(self) -> None:
        self.__secret_key: str = os.getenv("SECRET_KEY", "")
        self.__algorithm: str = os.getenv("ALGORITHM", "HS256")
        self.__access_exp: timedelta = timedelta(minutes=int(os.getenv('ACCESS_EXPIRE', 10)))
        self.__refresh_exp: timedelta = timedelta(days=int(os.getenv('REFRESH_EXPIRE', 3)))

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        exp = datetime.now(timezone.utc) + self.__access_exp
        to_encode.update({"exp": exp.timestamp(), "type": "access"})

        return jwt.encode(to_encode, self.__secret_key, self.__algorithm)
    

    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        exp = datetime.now(timezone.utc) + self.__refresh_exp
        to_encode.update({"exp": exp.timestamp(), "type": "refresh"})

        return jwt.encode(to_encode, self.__secret_key, self.__algorithm)
    

    def verify_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self.__secret_key, self.__algorithm)
            return payload
        except Exception as e:
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



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password=plain_password.encode('utf-8'),
        hashed_password=hashed_password.encode('utf-8')
    )



def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=10) # số mũ của 2 ==> 2 ^ rounds = số vòng lặp thực tế
    return bcrypt.hashpw(password=pwd_bytes, salt=salt).decode()


if __name__ == "__main__":
    password = "sherlock"
    hashed_pass = hash_password(password)
    print(verify_password(password, hashed_pass))