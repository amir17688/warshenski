"""
All queries and commands that the user makes in the retail application
"""
import psycopg2

ONLINE_STORE_ID = 1


class Query:
    def __init__(self, dbname, user, password, host, port=5432):
        self.db_conn = psycopg2.connect(
            host = host,
            dbname = dbname,
            user = user,
            password = password,
            port = port
        )
        self.cursor = self.db_conn.cursor()

    def commit(self):
        self.db_conn.commit()

    def __del__(self):
        self.cursor.close()
        self.db_conn.close()
    
    def login(self, customer_id):
        self.customer_id = customer_id
    
    def find_product_by_id(self, product_id):
        self.cursor.execute(
            'SELECT upc, name, weight, description FROM product WHERE id = \'%s\';',
            (product_id,)
        )
        return self.cursor.fetchall()

    def find_products_by_desc(self, product_desc):
        self.cursor.execute(
            'SELECT upc, name, weight, description FROM product WHERE description ILIKE \'%%%s%%\';',
            (product_desc,)
        )
        return self.cursor.fetchall()
    
    def find_products_by_name(self, product_name):
        self.cursor.execute(
            'SELECT upc, name, weight, description FROM product WHERE name ILIKE \'%%%s%%\';',
            (product_name,)
        )
        return self.cursor.fetchall()
    
    def find_products_by_upc(self, product_upc):
        self.cursor.execute(
            'SELECT upc, name, weight, description FROM product WHERE upc ILIKE \'%%%s%%\';',
            (product_upc,)
        )
        return self.cursor.fetchall()

    def find_product_by_type(self, product_type):
        self.cursor.execute("""
            SELECT *
            FROM product
            WHERE id IN (
                SELECT product_id
                FROM product_to_types
                WHERE product_type_id = %s
            )
            """, (product_type,)
        )
        return self.cursor.fetchall()
    
    def find_brand_by_id(self, brand_id):
        self.cursor.execute(
            'SELECT * FROM brand WHERE id = %s;',
            (brand_id,)
        )
        return self.cursor.fetchall()
    
    def find_brand_by_name(self, brand_name):
        self.cursor.execute(
            'SELECT * FROM brand WHERE name ILIKE \'%' + brand_name + '%\';'
        )
        return self.cursor.fetchall()
    
    def find_type_by_name(self, type_name):
        self.cursor.execute(
            'SELECT * FROM product_type WHERE name = %s;',
            (type_name,)
        )
        return self.cursor.fetchone()

    def _purchase_by_product(self, product, quantity):
        """Internal API, do not use externally"""

        # verify our store sells this product
        product_id = product[0]
        store_id = ONLINE_STORE_ID
        customer_id = self.customer_id
        self.cursor.execute("""
            SELECT product_id
            FROM store_sells_product
            WHERE product_id = %s
            AND store_id = %s;
            """,
            (product_id, store_id,)
        )
        results = self.cursor.fetchall()
        if len(results) == 0:
            # we don't sell this product
            raise Exception('Sorry, we do not sell this product in the store!')
        
        # create a purchase
        self.cursor.execute("""
            WITH current_purchase AS (
                INSERT INTO purchase (datetime, store_id, customer_id)
                VALUES (NOW(), %(store_id)s, %(customer_id)s)
                RETURNING id AS purchase_id
            )
            INSERT INTO product_in_purchase (product_id, purchase_id)
            VALUES (%(product_id)s, (SELECT purchase_id FROM current_purchase));
            """,
            {
                'store_id': store_id,
                'customer_id': customer_id,
                'product_id': product_id
            }
        )
        
        self.db_conn.commit()

    def purchase_by_product_id(self, product_id, quantity):
        product = self.find_product_by_id(product_id)
        self._purchase_by_product(product, quantity)

    def purchase_by_product_name(self, product_name, quantity):
        product = self.find_products_by_name(product_name)
        self._purchase_by_product(product, quantity)

    def purchase_by_product_upc(self, product_upc, quantity):
        product = self.find_products_by_upc(product_upc)
        self._purchase_by_product(product, quantity)

    def find_customer(self, username):
        self.cursor.execute(
            'SELECT * FROM customer WHERE LOWER(username) = LOWER(\'' + username + '\');'
        )
        return self.cursor.fetchone()
