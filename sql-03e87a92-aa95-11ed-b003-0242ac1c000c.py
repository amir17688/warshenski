from modules import sql


class Post:
    def __init__(self,conn):
        self.conn=conn;

    def getAllPosts(self,userid):
        sqlText="select users.name,post.comment,post.postid,(select Count(*) from post_like \
                where post.postid = post_like.postid) as like,\
                (select Count(*) from post_like where post.postid =post_like.postid \
                and post_like.userid=%d) as flag from users,post \
                where post.userid=users.userid and (post.userid in \
                (select friendid from friends where userid =%d) or post.userid=%d )\
                order by post.date desc;"%(userid,userid,userid)
        result=sql.queryDB(self.conn,sqlText)
        return result;
    
    def getPostsByPostid(self,postid):
        sqlText="select users.name,post.comment from users,post where \
                users.userid=post.userid and post.postid=%d"%(postid)
        result=sql.queryDB(self.conn,sqlText)
        return result;
    
    def getPostLike(self,postid):
        sqlText="select userid from post_like where postid=%d"%(postid)
        result=sql.queryDB(self.conn,sqlText)
        return result;

    def likePost(self,postid,userid):
        sqlText="insert into post_like values(%d,%d);"%(postid,userid)
        result=sql.insertDB(self.conn,sqlText)
        return result;

    def dislikePost(self,postid,userid):
        sqlText="delete from post_like where postid=%d and userid=%d;"%(postid,userid)
        result=sql.deleteDB(self.conn,sqlText)
        return result;

    def insertData(self,userid,post):
        sqlText="insert into post(userid,date,comment) \
                values(%d,current_timestamp(0),'%s');"%(userid,post);
        result=sql.insertDB(self.conn,sqlText)
        return result;


    def deletePost(self,postid):
        sqlText="delete from post where post.postid=%d"%(postid)
        result=sql.deleteDB(self.conn,sqlText)
        return result;
