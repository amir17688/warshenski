""" mysql File

    Arquivo onde se encontra todas as funções para trabalhar com o db
Todo:

    None

"""

import json
import mysql.connector as mysql
import src.settings as conf

class MySQL():
	"""
        MySQL class:
           	Todas as funções para manipulação do DB
    """
	def __init__(self):
		self.__connection = mysql.connect(**conf.DATABASE)
		self.cursor = self.__connection.cursor()

	def execute(self, query):
		"""
        	execute function:
           		Executa a query com tratamento de error
    	"""
		try:
			self.cursor.execute(query)
		except mysql.Error as error:
			print("Error: {}".format(error))
		return self.cursor

	def select(self, table):
		"""
        	select function:
           		Retorna todos os dados da tabela em formato JSON
    	"""
		aux_dict = dict()
		self.cursor.execute("SELECT * FROM {0}".format( table))
		json_data = {}
		for user in self.cursor:
			json_data[str(user[3])] = {}
			json_data[str(user[3])]['nome'] = user[0]
			json_data[str(user[3])]['sobrenome'] = user[1]
			json_data[str(user[3])]['endereco'] = user[2]
		return json.dumps(json_data)

	def insert(self, table, content):
		"""
        	insert function:
           		Recebe em JSON os dados e grava na tabela
    	"""
		nome = content["nome"]
		sobrenome = content["sobrenome"]
		endereco = content["endereco"]
		add_user = """INSERT INTO users (nome, sobrenome, endereco) VALUES (%s,%s,%s)"""

		data_user = (nome, sobrenome, endereco)
		try:
		    self.cursor.execute(add_user,data_user)
		except mysql.Error as error:
		    print("Error: {}".format(error))
		self.__connection.commit()
		self.cursor.lastrowid

	def delete_where(self, table, where):
		"""
        	delete_where function:
           		Deleta um campo especifico da tabela
    	"""
		try:
		    self.cursor.execute("DELETE FROM {0} WHERE {1}".format(table, where))
		except mysql.Error as error:
		    print("Erro: {}".format(error))
		self.__connection.commit()
		return self.cursor


	def update_where(self, table, info, where):
		"""
        	update_where function:
           		Atualiza um campo específico da tabela
    	"""
		try:
		    self.cursor.execute("UPDATE {0} SET {1} WHERE {2}".format(table, info, where))
		except mysql.Error as error:
		    print("Erro: {}".format(error))
		self.__connection.commit()
		return self.cursor

	def close(self):
		"""
        	close function:
           		fecha a conexao com o banco
    	"""
		self.__connection.close()

