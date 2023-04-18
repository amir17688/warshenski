from flask import Flask
from flask import request
from flask import Response
from recsys.algorithm.factorize import SVD
from pymemcache.client.hash import HashClient
import elasticache_auto_discovery
import pymysql
import logging
import hashlib
import time
import json
import sys

rds_host  = "recommendationdata.cnrjbhnycdir.eu-west-1.rds.amazonaws.com"
name = "blautj1"
password = "******"
db_name = "recommendationDB"

elasticache_config_endpoint = "reco-cache.chsu5z.cfg.euw1.cache.amazonaws.com:11211"
nodes = elasticache_auto_discovery.discover(elasticache_config_endpoint)
print nodes
nodes = map(lambda x: (x[1], int(x[2])), nodes)
print nodes
memcache_client = HashClient(nodes)
print memcache_client

try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except:
    sys.exit()

separator = '::'
app = Flask(__name__)

@app.route('/data')
def query():
    user = request.args.get('user_id')
    processedRow = ''
    hash_ids = []
    item_count = 0
    
    with conn.cursor() as cur:
        query = "SELECT movie_id, rating FROM recommendationDB.user_ratings WHERE user_id=" + user
        print query
        cur.execute(query)
        for row in cur:
            item_count += 1
            processedRow = processedRow + str(user) + separator + str(row[0]) + separator + str(row[1]) + separator + str(int(time.time())) + "\r\n"
            hash_ids.append(str(row[0]))
        print processedRow
        text_file = open("ratings.dat", "a")
        text_file.write(processedRow)
        text_file.close()
    
    print hash_ids
    hash = hashlib.sha1('.'.join(hash_ids)).hexdigest()
    print(hash)

    cache = memcache_client.get(hash)
    print cache
    if cache != None:    
        return Response(response=json.dumps({"results":json.loads(cache)}),
                        status=200,
                        mimetype="application/json")
    else:
        svd = SVD()
        svd.load_data(filename='./ratings.dat',
        sep=separator,
        format={'col':0, 'row':1, 'value':2, 'ids': int})

        recommendations = svd.recommend(int(user), is_row=False)
        recommendations_dict = dict(recommendations)

        films = "movie_id=" + str(recommendations.pop(0)[0])
        for recommendation in recommendations:
            films = films + " OR movie_id=" + str(recommendation[0])

        film_titles = []
        with conn.cursor() as cur:
            query = "SELECT movie_id, movie_title, movie_genre FROM recommendationDB.movies WHERE " + films 
            print query
            cur.execute(query)
            for row in cur:
                item_count += 1
                film_titles.append({"title": row[1],"genre": row[2], "relevance": recommendations_dict[row[0]], "movie_id": row[0]})

        memcache_client.set(hash, json.dumps(film_titles))

        return Response(response=json.dumps({"results":film_titles}),
                        status=200,
                        mimetype="application/json")
