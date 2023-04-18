import pymysql.cursors
from config import create_connection

PRODUCTS_TYPES_TABLE = "product_types"


class DepartmentsRepository:

    def get_departments():
        sql_query = (
            f"""
            SELECT name
            FROM {PRODUCTS_TYPES_TABLE}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchall()
        finally:
            connection.close()
