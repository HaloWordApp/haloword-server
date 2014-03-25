from flask import Flask, Response
import redis
import requests

app = Flask(__name__)
redis_store = redis.StrictRedis(host='localhost', port=6233, db=0)

API_URL = "http://www.dictionaryapi.com/api/v1/references/collegiate/xml/{}?key=6d9366e8-dc95-4b44-931a-ff90bc8f96bd"


@app.route("/webster/query/<word>")
def index(word):
    text = ""

    if not redis_store.exists(word):
        print "Not cached:", word
        text = requests.get(API_URL.format(word)).text
        redis_store.set(word, text)
    else:
        text = redis_store.get(word)

    redis_store.incr(word + ":count")

    headers = {"Cache-Control": "max-age=%d" % (3600 * 24 * 7,)}
    return Response(response=text,
                    status=200,
                    mimetype="application/xml",
                    headers=headers)


@app.route("/webster/list/")
def word_list():
    keys = sorted(redis_store.keys())
    html = "<pre>" + "\n".join(keys)
    html += "\n\nTotal: {}".format(len(keys)) + "</pre>"
    return html


@app.route("/webster/count/")
def request_count():
    keys = redis_store.keys(pattern="*:count")
    results = [{"key": key[:-6], "value": redis_store.get(key)} for key in keys]
    results = sorted(results, key=lambda r: r["value"], reverse=True)

    formated_results = ["{:>8}  {}".format(result["value"], result["key"]) for result in results]
    html = "<pre>" + "\n".join(formated_results)
    html += "\n\nTotal: {}".format(len(keys)) + "</pre>"

    return html


if __name__ == "__main__":
    app.debug = True
    app.run()
