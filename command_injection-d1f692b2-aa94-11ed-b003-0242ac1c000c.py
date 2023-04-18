import sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, scoped_session

engine = sqlalchemy.create_engine('mysql+pymysql://root:bajtastore@127.0.0.1/mydb')
Session = scoped_session(sessionmaker(bind=engine))

s = Session()

def select_row_from_mysql_command(command_str):
    ''' function for selecting a specific row  '''
    ''' OUPUT: a list of elements in the selected row '''

    sql = text(str(command_str))
    return s.execute(sql).fetchall()


def insert_into_mysql_command(command_str):
        ''' the function inserts data depending from a command_str '''

        sql = text(str(command_str))
        s.execute(sql)
        s.commit()
