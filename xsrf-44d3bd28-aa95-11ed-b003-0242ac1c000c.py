import os.path
import datetime
import tornado.ioloop
import tornado.web
import motor.motor_tornado
import crawl
import slugify
import bleach
import bs4

from copy import deepcopy
from tornado import gen
from tornado import escape
from tornado.options import define, options, parse_command_line

import sys


define("port", default=8888, help="run on the given port", type=int)
define("debug", default=True, help="run in debug mode")
define("title", default="The Newsreel")


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.settings['db']

    @property
    def collection(self):
        return self.settings['collection']


class MainHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        check_rss_updates(self.collection)
        cursor = self.collection.find().sort([('date', -1)])
        docs = yield cursor.to_list(length=20)
        self.render("index.html", title=options.title, items=docs)


class PostHandler(BaseHandler):
    @gen.coroutine
    def get(self, slug):
        doc = yield self.collection.find_one({'slug': slug})
        # if not doc:
        #     raise tornado.web.HTTPError(404)
        self.render("post.html", title=options.title, item=doc)


class PostNewHandler(BaseHandler):
    def get(self):
        try:
            error = self.get_argument("error")
        except:
            error = "All fields are required"
        self.render("new.html", title=options.title, error=error)

    @gen.coroutine
    def post(self):
        entry = {}
        author = self.get_argument("author", "Anonymous")
        title = self.get_argument("title")
        image = validate_image(self.get_argument("image"))
        html = self.get_argument("post-text")
        text = validate_html(html)
        if not title:
            error = u"?error=" + escape.url_escape("Title must be filled.")
            self.redirect("/new" + error)
        elif not html:
            error = u"?error=" + escape.url_escape("Post cannot be empty.")
            self.redirect("/new" + error)
        elif text is None:
            error = u"?error=" + escape.url_escape("Forbidden or invalid url detected in post body.")
            self.redirect("/new" + error)
        else:
            summary = generate_summary(text)
            slug = slugify.slugify(summary[:30])
            entry["author"] = author
            entry["date"] = datetime.datetime.now().replace(microsecond=0)
            entry["image"] = image
            entry["summary"] = summary
            entry["title"] = title
            entry["text"] = text
            entry["slug"] = slug
            yield self.collection.insert_one(entry)
            self.redirect("/post/" + slug)


def generate_summary(text):
    soup = bs4.BeautifulSoup(text, "lxml")
    return soup.get_text()[:200]


def validate_image(image):
    checklist = ["gif", "png", "jpg"]
    if image[-3:].lower() in checklist:
        return image
    else:
        return "http://ic.pics.livejournal.com/masio/8221809/287143/287143_original.gif"


def validate_html(text):
    sites = ['youtube.com', 'play.md', 'vimeo.com']
    soup = bs4.BeautifulSoup(text, "lxml")
    sources = soup.find_all('iframe', {"src": True})
    for source in sources:
        if not any(x in source['src'] for x in sites):
            return None
    tags = ['b', 'p', 'i', 'strong', 'em', 'img', 'iframe']
    attributes = {'img': ['src'], 'iframe': ['src']}
    return bleach.clean(text, tags, attributes)


def get_datetime(date):
    sliced_date = date[5:25]
    return datetime.datetime.strptime(sliced_date, '%d %b %Y %H:%M:%S')


def build_json_from_raw_data(ch_date=datetime.datetime(2000, 1, 1)):
    raw_data = crawl.get_sslowdown_data()
    result = []
    entry = {}
    for entry_key, entry_data in raw_data.items():
        date = get_datetime(entry_data["date"])
        if date > ch_date:
            entry["author"] = entry_data["author"]
            entry["date"] = date
            entry["image"] = entry_data["image"]
            entry["summary"] = entry_data["summary"]
            entry["title"] = entry_data["title"]
            entry["text"] = entry_data["text"]
            entry["slug"] = slugify.slugify(entry_data["summary"][:30])
            result.append(deepcopy(entry))
    return result


@gen.coroutine
def bulk_insert(collection, items):
    yield collection.insert_many(items)


@gen.coroutine
def check_rss_updates(collection):
    cursor = collection.find()
    cursor.sort([('date', -1)]).limit(1)
    document = None
    while (yield cursor.fetch_next):
        document = cursor.next_object()
    if document:
        date = document['date']
        articles = build_json_from_raw_data(ch_date=date)
    else:
        articles = build_json_from_raw_data()
    if len(articles) > 0:
        bulk_insert(collection, articles)


def main():
    # sys.setrecursionlimit(10000)

    parse_command_line()
    db = motor.motor_tornado.MotorClient().news
    collection = db.articles
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/post/(.+)", PostHandler),
            (r"/new", PostNewHandler),
        ],
        cookie_secret="__THERE_IS_NO_SECRET_COOKIE__",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        debug=options.debug,
        db=db,
        collection=collection,
    )
    print('Listening on http://localhost:{}'.format(options.port))
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
