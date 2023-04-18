import help_functions
import tabulate


def process_help(id, tokens, query):
    help_functions.display_help(tokens)


def process_purchase(id, tokens, query):
    # query for purchase data and print results
    print("\tpurchase command " + str(tokens))
    pass


def process_id(id, tokens, query):
    # query for item lookup by id
    if len(tokens) == 0:
        print("\tusage: id [item id]")
        return

    products = query.find_product_by_id(tokens[0])

    if products is None or len(products) == 0:
        print("\tNo products found")
    else:
        print(tabulate.tabulate([("UPC", "Name", "Weight", "Description")] + products))


def process_brand(id, tokens, query):
    # query for brand data and print results
    if len(tokens) == 0:
        print("\tusage: brand [brand name|brand id]")
        return

    brand = query.find_brand_by_id(tokens[0]) if tokens[0].isdigit() else query.find_brand_by_name(tokens[0])

    if len(brand) == 0:
        print("\tNo brands found")
    else:
        print(tabulate.tabulate([("id", "Brand Name")] + brand))


def process_type(id, tokens, query):
    # query for type data and print results
    print("\ttype command " + str(tokens))
    pass


def process_lookup(id, tokens, query):
    # query for item data and print results

    if len(tokens) == 0:
        print("\tusage: lookup [item name|item id|keyword|UPC]")
        return

    products = query.find_products_by_name(tokens[0])
    products += query.find_products_by_desc(tokens[0])
    products += query.find_products_by_upc(tokens[0])

    if products is None or len(products) == 0:
        print("\tNo products found")
    else:
        print(tabulate.tabulate([("UPC", "Name", "Weight", "Description")] + products))


def process_userinfo(id, tokens, query):
    # query for current user data and print results
    print("\tuserinfo command id=" + str(id))
    pass