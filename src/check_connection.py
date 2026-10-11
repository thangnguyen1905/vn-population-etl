import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# 1. Xác định thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Đọc thông tin từ file .env
load_dotenv(BASE_DIR / ".env")

# 3. Kết nối PostgreSQL
try:
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5
    ) as conn:

        # 4. Tạo cursor để thực thi SQL
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    current_database(),
                    current_user,
                    version();
            """)

            result = cursor.fetchone()

            print("Connection successful!")
            print("Database:", result[0])
            print("User:", result[1])
            print("PostgreSQL:", result[2])

except psycopg.Error as e:
    print("Connection failed!")
    print("Error:", e)