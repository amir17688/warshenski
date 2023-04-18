#!/usr/bin/env python3
import psycopg2


def get_top_articles(cur, order, limit):
    """Fetches the top articles.

    Fetches the number of top articles in the specified
    order.

    Args:
        cur(obj): The cursor to execute the query.
        order(str): The order to view the rows in.
        limit(int): The number of rows to view.

    Return:
        True if success, False otherwise.
    """
    query = '''SELECT articles.title, COUNT(*) as views
            FROM log, articles
            WHERE log.path LIKE '%'||articles.slug AND
            log.method = 'GET'
            GROUP BY articles.title
            ORDER BY views {}
            LIMIT {}'''.format(order, limit)
    rows = get_data(cur, query)

    # Write data to txt file.
    if rows is not None:
        file = open("top_articles_report.txt", "w")
        for row in rows:
            file.write("\"{}\" - {} views \n".format(row[0], row[1]))
        file.close()

        return True
    else:
        return False


def get_top_authors(cur, order):
    """Fetches the top authors.

    Args:
        cur(obj): The cursor to execute the query.
        order(str): The order to view the rows in.

    Return:
        True if success, False otherwise.
    """
    query = '''SELECT authors.name, COUNT(*) as views
            FROM authors, articles, log
            WHERE authors.id = articles.author AND
            log.path LIKE '%'||articles.slug AND
            log.method = 'GET'
            GROUP BY authors.name
            ORDER BY views {}'''.format(order)
    rows = get_data(cur, query)

    # Write data to txt file.
    if rows is not None:
        file = open("top_authors_report.txt", "w")
        for row in rows:
            file.write("{} - {} views \n".format(row[0], row[1]))
        file.close()

        return True
    else:
        return False


def get_error_days(cur, error_percent):
    """Fetches the days in which requests led to errors.

    Fetches the days in which the specified percentage
    of requests led to errors.

    Args:
        cur(obj): The cursor to execute the query.
        error_percent(int): The percentage of requests that led to errors.

    Return:
        True if success, False otherwise.
    """
    query = '''SELECT to_char(log_errors.date, 'Mon DD YYYY'),
            round((log_errors.errors * 100
            / log_requests.total::numeric), 2) as percent
            FROM log_errors, log_requests
            WHERE log_errors.date = log_requests.date AND
            log_errors.errors * 100
            / log_requests.total::numeric > {}
            ORDER BY log_errors.date'''.format(error_percent)
    rows = get_data(cur, query)

    # Write data to txt file.
    if rows is not None:
        file = open("error_report.txt", "w")
        for row in rows:
            file.write("{} - {}% errors \n".format(row[0], row[1]))
        file.close()

        return True
    else:
        return False


def get_data(cur, query):
    """Fetches the data specified in the query.

    Args:
        cur(obj): The cursor to execute the query.
        query(str): The query to execute.

    Return:
        The data or None if there is an error.
    """
    try:
        cur.execute(query)
        return cur.fetchall()
    except psycopg2.Error:
        cur.connection.rollback()
        return None


def setup_connection(db_name):
    """Sets up the database connection.

    Sets up a Postgre database connection with passed in
    database's name.

    Args:
        db_name(str): The name of the database to connect to.

    Returns:
        A cursor to the database.
    """
    try:
        return psycopg2.connect(dbname=db_name)
    except psycopg2.Error as e:
        print(e)


def main():
    """Main function to run the code."""
    conn = setup_connection("news")

    if conn is not None:
        cur = conn.cursor()
        # Create top articles report.
        if get_top_articles(cur, "DESC", 3):
            print("Successful creating top articles report.")
        else:
            print("Error creating top articles report.")
        # Create top authors report.
        if get_top_authors(cur, "DESC"):
            print("Successful creating top authors report.")
        else:
            print("Error creating top authors report.")
        # Create error report.
        if get_error_days(cur, 1):
            print("Successful creating daily error percentage report.")
        else:
            print("Error creating daily error percentage report.")

        conn.close()

main()
