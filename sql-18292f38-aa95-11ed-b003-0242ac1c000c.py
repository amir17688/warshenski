#!/usr/bin/python3

import psycopg2

class TimescalePoster:

    def __init__(self, host, port, database, username, password):
        self.connection = psycopg2.connect(dbname=database, host=host, port=port, user=username, password=password)

    """
    Inserts data into an existing table. On failure due to not enough columns
    will automatically add columns to the table as necessary.
    Takes:
    tableName - string of the table being inserted into
    timeStamp - the timeStamp of the insertion
    tableObj - a dict of key/value pairs to insert
    """
    def insertData(self, tableName, timeStamp, tableObj):
        cols = ""
        vals = ""
        for key in tableObj:
            cols = cols + ", %s"
            vals = vals + ", %s"

        nameList = []
        valList = []
        nameList.append(tableName)
        for key in tableObj:
            nameList.append(key)
            valList.append(tableObj[key])

        nameList = nameList + valList

        cursor = self.connection.cursor()
        try:
            cursor.execute("INSERT INTO %s (TIMESTAMP" + cols + ") VALUES (%s," + vals + ")", nameList)
            print('posted successfully!')
            self.connection.commit()
        except psycopg2.Error as e:
            cursor.close();
            print("Insert Error: %s".format(e))

            #was this error due to adding a field?
            if e == missing_column:
                print("Attempting to alter table!")
                #column_name = err.toString().split("\"")[1];
                columnName = ""

                params = []
                try:
                    t = self.__getType(tableObj[columnName]);
                    params.append(tableName);
                    params.append(columnkName);
                    params.append(t);
                except TypeError as e:
                    print("Got a type error %s".format(e))
                    print('Error with field %s'.format(columnName))
                    print('Table alteration failed')
                    raise e

                #print(params)
                try:
                    cursor = self.connection.cursor()
                    cursor.execute("ALTER TABLE %s ADD COLUMN %s %s", params)
                    self.connection.commit()
                except psycopg2.Error as e:
                    print("Failed to alter table with error e".format(e))

                print("Table alteration succeeded - attempting to insert again")

                try:
                    self.insertData(tableName, timeStamp, tableObj)
                    print('posted successfully!')
                except:
                    print("Unexpected error when reinserted!")

            #was this error due to missing the table entirely?
            elif e == missing_table:
                try:
                    self.createTable(tableName, tableObj)
                    print("Created table successfully - reinserting")
                except psycopg2.Error as e:
                    print("Failed to create table??: %s".format(e))
                    raise

                try:
                    self.insertData(tableName, timeStamp, tableObj)
                    print('posted successfully!')
                except:
                    print("Unexpected error when reinserted!")
                    raise

    """
    A private function that maps a type in python to a type in postgres
    Supports Strings, bools, numbers and arrays

    Raises a typerror on failure
    """
    def __getType(self, value):
        t = type(value)
        if(t is str):
            return 'TEXT'
        elif(t is bool):
            return 'BOOLEAN'
        elif(t is int):
            return 'DOUBLE PRECISION'
        elif(t is float):
            return 'DOUBLE PRECISION'
        elif(t is list):
            t2 = type(value[0])
            if(t2 is str):
                return 'TEXT[]'
            elif(t2 is bool):
                return 'BOOLEAN[]'
            elif(t2 is int):
                return 'DOUBLE PRECISION[]'
            elif(t2 is float):
                return 'DOUBLE PRECISION[]'
            else:
                raise TypeError('Only supports strings, booleans, numbers and arrays of the former')
        else:
            raise TypeError('Only supports strings, booleans, numbers and arrays of the former')

    """
    Creates a timescaledb table with at least a timestamp field. Partitions table
    by time.
    Takes:
    tableName - string of the table being inserted into
    tableObj - a dict of key/value pairs to start the table with
    """
    def createTable(self, tableName, tableObj):
        #find the number of columns in the in the tableobj and create
        #placeholders
        cols = ""
        for key in tableObj:
            cols = cols + ", %s %s"

        #map the type of those objects to the correct postgres type
        nameList = []
        nameList.append(tableName)
        for key in tableObj:
            try:
                t = self.__getType(tableObj[key])
                nameList.append(key)
                nameList.append(t)
            except TypeError as e:
                print('Error with object %s at key %s with value %s'.format(tableObj, key, tableObj[key]))
                print("Caught error %s".format(e))
                raise e

        cursor = self.connection.cursor()

        try:
            cursor.execute("CREATE TABLE %s (TIMESTAMP TIMESTAMPTZ NOT NULL" + cols + ")", nameList)
        except psycopg2.Error as e:
            print("CREATE TABLE Error: %s".format(e))

        self.connection.commit()

    """
    Checks if a table exists
    takes:
    tableName - name of the table
    """
    def tableExists(self, tableName):
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",tableName)
        except psycopg2.Error as e:
            return False

        return True

