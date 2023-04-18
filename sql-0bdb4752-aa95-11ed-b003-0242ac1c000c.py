"""
desc: application for end users to access retail data
"""
import queries
import configparser
import customer_commands
import help_functions


def init():
    # init database and what not
    config = configparser.ConfigParser()
    config.read('config.ini')
    return queries.Query(
        host     = config['database']['host'],
        dbname   = config['database']['dbname'],
        user     = config['database']['user'],
        password = config['database']['pass']
    )


def handle_query(tokens, id, query):
    # handle each type of queries

    commands = {
        "help":     customer_commands.process_help,
        "id":       customer_commands.process_id,
        "purchase": customer_commands.process_purchase,
        "brand":    customer_commands.process_brand,
        "itemtype": customer_commands.process_type,
        "userinfo": customer_commands.process_userinfo,
        "lookup":   customer_commands.process_lookup
    }

    command = commands.get(tokens[0], "invalid")
    if command == "invalid":
        print("\tinvalid command \"" + tokens[0] + "\"")
    else:
        command(id, tokens[1:], query)


def create_new_user(username, query):
    print("first name: ", end="")
    fname = input()
    print("last name: ", end="")
    lname = input()
    print("phone number (xxxxxxxxxxx): ", end="")
    phone = input()
    phone = int(phone) if phone.isdigit() else None
    print("email: ", end="")
    email = input()
    print("street address: ", end="")
    street = input()
    print("city: ", end="")
    city = input()
    print("state: ", end="")
    state = input()
    print("zipcode: ", end="")
    zip = input()
    zip = int(zip) if zip.isdigit() else None
    print("country: ", end="")
    country = input()

    # create new user with (username, fname, lname, phone, email, addr)
    #return new id

    query.cursor.execute(
        'SELECT MAX(frequent_shopper_id) FROM customer;'
    )

    freq_shop_id = query.cursor.fetchone()[0] + 1

    query.cursor.execute(
        'INSERT INTO customer (first_name, last_name, phone_number, username, email, frequent_shopper_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;',
        (fname, lname, phone, username, email, freq_shop_id)
    )

    customer_id = query.cursor.fetchone()[0]

    query.cursor.execute(
        'INSERT INTO address (address_line, zipcode, city, state, country) VALUES (%s, %s, %s, %s, %s) RETURNING id;',
        (street, zip, city, state, country)
    )

    address_id = query.cursor.fetchone()[0]

    query.cursor.execute(
        'INSERT INTO customer_to_address (customer_id, address_id) VALUES (%s, %s);',
        (customer_id, address_id)
    )

    query.commit()

    print("user " + username + " created ✓")
    return freq_shop_id


def username_to_id(username, query):
    user = query.find_customer(username)

    if user is not None:
        print("Welcome Back", user[1], user[2])
        return user[7]

    return create_new_user(username, query)


def get_customer_id(query):
    print("username: ", end="")
    username = input()

    while len(username) == 0:
        print("username must exceed zero characters.\nusername: ", end="")
        username = input()

    return username_to_id(username, query)


def main():
    query = init()
    print("##################################")
    print("#       retail application       #")
    print("##################################")
    id = get_customer_id(query)
    print("\n     type 'help' for query info")
    print("     enter 'quit' to exit\n")
    print(">", end="")
    line = input()
    line.replace("\\s*", " ")
    tok = line.split()
    while len(tok) > 0 and tok[0] != "quit" and tok[0] != "exit":
        handle_query(tok, id, query)
        print(">", end="")
        line = input()
        line = line.replace("\\s*", " ")
        tok = line.split()


if __name__ == "__main__":
    main()
