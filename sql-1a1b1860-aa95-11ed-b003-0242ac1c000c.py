# Create connection to database

import pymysql

def create_connection():
    try:
        connection = pymysql.connect(host   = "localhost",
                                     user   = "root",
                                     passwd = "",
                                     db     = "ebola")
    
    except pymysql.Error as error:
        print ("connection error: ", error)
   
    return connection


def destroy_connection(conn):
    conn.close()

def run_insert(insert_stmt):
    is_success = True
    try:
        conn = create_connection()
        cur = conn.cursor()
        cur.execute(insert_stmt)
        results = cur.fetchall()

        widths = []
        columns = []
        tavnit = '|'
        separator = '+' 

        for cd in cur.description:
            widths.append(max(cd[2], len(cd[0])))
            columns.append(cd[0])

        for w in widths:
            tavnit += " %-"+"%ss |" % (w,)
            separator += '-'*w + '--+'

        print(separator)
        print(tavnit % tuple(columns))
        print(separator)
        for row in results:
            print(tavnit % row)
        print(separator)


        # for row in result:
            # print row
        conn.commit()
        destroy_connection(conn)

    except pymysql.Error as error:
        print ("insert error: ", error)
        is_success = False
    return is_success
