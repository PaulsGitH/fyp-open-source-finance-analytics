import os
from dotenv import load_dotenv, find_dotenv


def main():
    # Load variables from the nearest .env file
    load_dotenv(find_dotenv())

    print(f"DB user: {os.getenv('DB_USER')}")
    print(f"DB password: {os.getenv('DB_PASSWORD')}")
    print(f"DB name: {os.getenv('DB_NAME')}")
    print(f"Database URL: {os.getenv('DATABASE_URL')}")


if __name__ == "__main__":
    main()
