import MySQLdb

class MySQLProcess:

    def __init__(self, host="uspto-db.cniiyfnr7znr.us-west-2.rds.amazonaws.com", port=3306,user="", passwd="",db="uspto_patents", charset="utf8"):
        # host="127.0.0.1", port=3306,user="", passwd="",db="qliu14", charset="utf8"
        # host="127.0.0.1", port=3306,user="qliu14", passwd="qliu14password",db="qliu14", charset="utf8"
        self._host = host
        self._port = port
        self._username = user
        self._password = passwd
        self._dbname = db
        self._charset = charset
        self._conn = None
        self._cursor = None

    def load(self,sql):
        if self._conn==None:
            self.connect()
            self._cursor.execute(sql)
            self._conn.commit()
            result = self._cursor.fetchall()  #fetchone(), fetchmany(n) 
            return result  #return affected rows
        else:
            self._cursor.execute(sql)
            self._conn.commit()
            result = self._cursor.fetchall()  #fetchone(), fetchmany(n) 
            return result  #return affected rows

    def execute(self, sql): # no parameters
        #try:
        if self._conn==None:
            self.connect()
            self._cursor.execute(sql)
            self._conn.commit()
            result = self._cursor.fetchall()  #fetchone(), fetchmany(n) 
            return result  #return affected rows
        else:
            self._cursor.execute(sql)
            self._conn.commit()
            result = self._cursor.fetchall()  #fetchone(), fetchmany(n) 
            return result  #return affected rows
        #finally:
            #self.close()
            #function "close()" can be added efficiently after multiple lines of SQL statements.

    # used to retrieve ID buy matching fields of values
    def query(self,sql):
        #try:
        if self._conn == None:
            self.connect()
            self._cursor.execute(sql)
            self._conn.commit()
            result=self._cursor.fetchone()
            return int(result[0])
        else:
            self._cursor.execute(sql)
            self._conn.commit()
            result=self._cursor.fetchone()
            return int(result[0])
        #finally:
            #self.close()

    # used to verify whether the applicationID is in the current table APPLICATION
    def verify(self,sql):
        if self._conn == None:
            self.connect()
            self._cursor.execute(sql)
            self._conn.commit()
            return self._cursor.fetchone()
        else:
            self._cursor.execute(sql)
            self._conn.commit()
            return self._cursor.fetchone() #None or not

    def executeMany(self, sql, params):
        #try:
        if self._conn == None:
            self.connect()
            count = self._cursor.executemany(sql, params)
            self._conn.commit()
            return count
        else:
            count = self._cursor.executemany(sql, params)
            self._conn.commit()
            return count
        #finally:
            #self.close()

    def executeParam(self, sql, param):
        #try:
        if self._conn == None:
            self.connect()
            self._cursor.execute(sql, param)
            self._conn.commit()
            result = self._cursor.fetchall()  #fetchone(), fetchmany(n) 
            return result  #return a tuple ((),())
        else:
            self._cursor.execute(sql, param)
            self._conn.commit()
            result = self._cursor.fetchall()  #fetchone(), fetchmany(n) 
            return result  #return a tuple ((),())
        #finally:
            #self.close()
            
    def connect(self):
        if self._conn == None:
            self._conn = MySQLdb.connect(host=self._host, user=self._username,
                                    passwd=self._password, db=self._dbname,
                                    port=self._port, charset=self._charset, local_infile=1)
            print "Connected successfully!"
        if self._cursor == None:
            self._cursor = self._conn.cursor()
    
    def close(self):
        if self._cursor != None:
            self._cursor.close()
            self._cursor = None
        if self._conn != None:
            self._conn.close()
            self._conn = None
        print 'Closed successfully!'
