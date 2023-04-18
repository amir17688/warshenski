import pymysql
from config import create_connection

PRODUCTS_TABLE = "products"
PRODUCTS_TYPES_TABLE = "product_types"
REVIEWS_TABLE = "reviews"
USERS_TABLE = "users"


class ProductsRepository:

    def get_products(filters):
        offset = (filters['page'] - 1) * filters['perPage']
        sql_query = (
            f"""
            SELECT p.id, p.ean, p.name, p.description, pt.name AS type, p.company, p.price, p.rating, p.weight, p.quantity, p.image_url
            FROM {PRODUCTS_TABLE} AS p INNER JOIN {PRODUCTS_TYPES_TABLE} AS pt ON
            p.product_type_id=pt.id
            WHERE p.rating >= {filters['rating']}
            ORDER BY p.id LIMIT {offset}, {filters['perPage']}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchall()
        finally:
            connection.close()

    def get_department_products(filters, department):
        offset = (filters['page'] - 1) * filters['perPage']
        sql_query = (
            f"""
            SELECT p.id, p.ean, p.name, p.description, pt.name AS type, p.company, p.price, p.rating, p.weight, p.quantity, p.image_url
            FROM {PRODUCTS_TABLE} AS p INNER JOIN {PRODUCTS_TYPES_TABLE} AS pt ON
            p.product_type_id=pt.id
            WHERE p.rating >= {filters['rating']}
            AND pt.name = '{department}'
            ORDER BY p.id LIMIT {offset}, {filters['perPage']}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchall()
        finally:
            connection.close()

    def search_products(filters, search):
        offset = (filters['page'] - 1) * filters['perPage']
        sql_query = (
            f"""
            SELECT p.id, p.ean, p.name, p.description, pt.name AS type, p.company, p.price, p.rating, p.weight, p.quantity, p.image_url
            FROM {PRODUCTS_TABLE} AS p INNER JOIN {PRODUCTS_TYPES_TABLE} AS pt ON
            p.product_type_id=pt.id
            WHERE p.rating >= {filters['rating']}
            AND p.name LIKE '%{search}%'
            ORDER BY p.id LIMIT {offset}, {filters['perPage']}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchall()
        finally:
            connection.close()

    def get_total_products(filters):
        sql_query = (
            f"""
            SELECT COUNT(p.id) AS total
            FROM products AS p
            WHERE p.rating >= {filters['rating']}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return int(cursor.fetchone()["total"])
        finally:
            connection.close()

    def get_total_departments_products(filters, department):
        sql_query = (
            f"""
            SELECT COUNT(p.id) AS total
            FROM products AS p INNER JOIN {PRODUCTS_TYPES_TABLE} AS pt ON
            p.product_type_id=pt.id
            WHERE p.rating >= {filters['rating']}
            AND pt.name = '{department}'
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return int(cursor.fetchone()["total"])
        finally:
            connection.close()

    def get_product(productId):
        sql_query = (
            f"""
            SELECT p.ean, p.name, p.description, pt.name AS type, p.company, p.price, p.rating, p.weight, p.quantity, p.image_url
            FROM {PRODUCTS_TABLE} AS p INNER JOIN {PRODUCTS_TYPES_TABLE} AS pt ON
            p.product_type_id=pt.id WHERE p.id={productId}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchone()
        finally:
            connection.close()

    def get_product_reviews(productId, filters):
        offset = (filters['page'] - 1) * filters['perPage']
        sql_query = (
            f"""
            SELECT u.username, r.id, r.title, r.comment, r.rating, r.timestamp
            FROM {PRODUCTS_TABLE} p, {REVIEWS_TABLE} r, {USERS_TABLE} u
            WHERE p.id={productId} && r.user_id=u.id && r.product_id=p.id
            ORDER BY r.id DESC 
            LIMIT {offset}, {filters['perPage']}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchall()
        finally:
            connection.close()

    def get_total_searched_products(filters, search):
        sql_query = (
            f"""
            SELECT COUNT(p.id) AS total
            FROM {PRODUCTS_TABLE} AS p INNER JOIN {PRODUCTS_TYPES_TABLE} AS pt ON
            p.product_type_id=pt.id
            WHERE p.rating >= {filters['rating']}
            AND p.name LIKE '%{search}%'
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return int(cursor.fetchone()["total"])
        finally:
            connection.close()

    def get_total_product_reviews(productId):
        sql_query = (
            f"""
            SELECT COUNT(r.id) AS total
            FROM {REVIEWS_TABLE} AS r
            WHERE r.product_id={productId}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return int(cursor.fetchone()["total"])
        finally:
            connection.close()

    def add_product_review(productId, userId, review):
        sql_query = (
            f"""
            INSERT INTO {REVIEWS_TABLE} (user_id, product_id, title, comment, rating)
            VALUES({userId}, {productId}, '{review['title']}',
            '{review['comment']}', {review['rating']})
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()
        except pymysql.err.IntegrityError:
            raise Exception('Duplicate')
        finally:
            connection.close()
