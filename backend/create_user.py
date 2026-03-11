import sys
from backend.db import SessionLocal
from backend.models import User
from backend.auth import hash_password


def create_user(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User already exists: {email}")
            return

        user = User(
            email=email,
            password_hash=hash_password(password),
        )

        db.add(user)
        db.commit()

        print(f"User created: {email}")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m backend.create_user <email> <password>")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    create_user(email, password)
