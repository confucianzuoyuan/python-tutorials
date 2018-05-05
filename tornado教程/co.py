import random
import time
from tornado import gen
from tornado.ioloop import IOLoop


@gen.coroutine
def get_url(url):
    wait_time = random.randint(1, 4)
    yield gen.sleep(wait_time)
    print('URL {} took {}s to get!'.format(url, wait_time))
    raise gen.Return((url, wait_time))


@gen.coroutine
def outer_coroutine():
    before = time.time()
    coroutines = [get_url(url) for url in ['URL1', 'URL2', 'URL3']]
    result = yield coroutines
    after = time.time()
    print(result)
    print('total time: {} seconds'.format(after - before))


if __name__ == '__main__':
    IOLoop.current().run_sync(outer_coroutine)