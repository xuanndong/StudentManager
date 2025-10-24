# Standard Libraries

# Local Modules

# Third-party Libraries
import bcrypt

class PasswordService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            plain_password_bytes = plain_password.encode('utf-8')
            hashed_password_bytes = hashed_password.encode('utf-8')

            return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
        except (ValueError, TypeError):
            return False

    
    @staticmethod
    def get_password_hash(password: str) -> str:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()

        hashed_bytes = bcrypt.hashpw(password_bytes, salt)

        return hashed_bytes.decode('utf-8')


password_service = PasswordService()
