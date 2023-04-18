import pymysql
from config import create_connection


USERS_TABLE = "users"
CARTS_TABLE = "carts"
PRODUCTS_TABLE = "products"
INVOICES_TABLE = "invoices"
INVOICE_PRODUCTS_TABLE = "invoice_products"


class UsersRepository:

    def get_users():
        sql_query = (
            f"""
            SELECT id, first_name, last_name, username, email, password, INET_NTOA(ip_address)
            as ip_address, registration_date, activated
            FROM {USERS_TABLE}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchall()
        finally:
            connection.close()

    def get_user(id):
        sql_query = (
            f"""
            SELECT * FROM {USERS_TABLE} WHERE id=%s
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query, (id))
            user = cursor.fetchone()
            if not user:
                return None
            return {'firstName': user['first_name'],
                    'lastName': user['last_name'], 'username' : user['username']}
        finally:
            connection.close()

    def get_invoice(id):
        sql_query = ("select t2.id as id_invoice , t2.transaction_date, sum(t3.price * t1.quantity) as montant from  invoice_products as t1 inner join invoices  as t2 on  t2.id = t1.invoice_id inner join  products  as t3 on  t3.id = t1.product_id  and t2.user_id= %s group by  t2.id, t2.transaction_date order by  t2.transaction_date DESC")
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query, (id))
            return cursor.fetchall()
        finally:
            connection.close()

    def get_invoiceById(id):
        sql_query = ("select i.transaction_date, ip.invoice_id, p.name, ip.quantity, p.price from invoice_products as ip, products as p, invoices as i where invoice_id = %s and ip.product_id = p.id and ip.invoice_id = i.id;")
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query, (id))
            return cursor.fetchall()
        finally:
            connection.close()

    def add_product_to_cart(userId, productId, cart):
        sql_query = (
            f"""
            INSERT INTO {CARTS_TABLE} (user_id, product_id, quantity)
            VALUES({userId}, {productId}, {cart['quantity']})
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()
            return "Ok"
        except pymysql.err.IntegrityError:
            raise Exception('Duplicate')
        finally:
            connection.close()

    def get_cart(userId):
        sql_query = (
            f"""
            SELECT p.id, p.name, p.company, p.rating, p.image_url, p.price, c.quantity AS quantity
            FROM {PRODUCTS_TABLE} AS p INNER JOIN {CARTS_TABLE} AS c ON
            p.id=c.product_id
            WHERE c.user_id={userId}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchall()
        finally:
            connection.close()

    def delete_product_from_cart(userId, productId):
        sql_query = (
            f"""
            DELETE FROM {CARTS_TABLE} 
            WHERE user_id={userId} && product_id={productId}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()
            return "Ok"
        finally:
            connection.close()

    def delete_cart(userId):
        sql_query = (
            f"""
            DELETE FROM {CARTS_TABLE} 
            WHERE user_id={userId}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()
            return "Ok"
        finally:
            connection.close()

    def create_invoice(userId):
        sql_query = (
            f"""
            INSERT INTO {INVOICES_TABLE} (user_id)
            VALUES ({userId})
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()
            return "Ok"
        finally:
            connection.close()

    def get_invoice_id(userId):
        sql_query = (
            f"""
            SELECT id from {INVOICES_TABLE}
            WHERE user_id={userId}
            ORDER BY transaction_date DESC
            LIMIT 1
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            return cursor.fetchone()
        finally:
            connection.close()

    def update_cart_quantity(userId, productId, quantity):
        sql_query = (
            f"""
            UPDATE {CARTS_TABLE}
            SET quantity = {quantity}
            WHERE user_id = {userId} AND product_id = {productId};
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()
            return "Ok"
        finally:
            connection.close()

    def create_invoice_products_values_query(invoiceId, products):
        invoice_products_values = ""
        for product in products["products"]:
            invoice_products_values += "("
            invoice_products_values += str(invoiceId['id'])
            invoice_products_values += ","
            invoice_products_values += str(product['product']['productId'])
            invoice_products_values += ","
            invoice_products_values += str(product['product']['quantity'])
            invoice_products_values += "),"
        invoice_products_values = invoice_products_values[:-1]
        return invoice_products_values

    def create_invoice_products(userId, products, invoiceId):
        invoice_products_values = UsersRepository.create_invoice_products_values_query(invoiceId, products)
        print("Result:")
        print(invoice_products_values)
        sql_query = (
            f"""
            INSERT INTO {INVOICE_PRODUCTS_TABLE} (invoice_id, product_id, quantity)
            VALUES {invoice_products_values}
            """)
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()
            return "Ok"
        finally:
            connection.close()
