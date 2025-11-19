from .db import SessionLocal
from .models import User
from .auth import hash_password

def create_user(email: str, password: str):
    db = SessionLocal()
    try:
        user = User(
            email=email,
            password_hash=hash_password(password)
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    create_user("demo@example.com", "demo123")
