import psycopg2
import secretConstants

connectionString = (
    'dbname=' + secretConstants.DATABASE_NAME + 
    ' user=' + secretConstants.DATABASE_USER + 
    ' host=' + secretConstants.DATABASE_HOST + 
    ' password=' + secretConstants.DATABASE_PASSWORD +
    ' port=' + secretConstants.DATABASE_PORT
)
conn = None
result = None

def getAlcoholByName(name):
    name = fixTypingErrors(name)
    QUERY = (
        "SELECT barnivore_product_name, barnivore_status, barnivore_country " + 
        "FROM barnivore_product " +
        "WHERE lower(barnivore_product_name) like lower('% \%s %')"
    )
    
    try:
        conn = psycopg2.connect(connectionString)
        cur = conn.cursor()
        cur.execute(QUERY, (name))
        result = cur.fetchall()

    except(psycopg2.DatabaseError, e):
        print('Error %s' % e)    

    finally:
        if conn:
            conn.close()

    return result

def fixTypingErrors(name):
    name = name.lower() 
    if name == "guiness":
        name = "guinness"
    return name

#Uncomment for testing
#getAlcoholByName("guiness")


