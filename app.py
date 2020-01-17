import os
from hashlib import md5
from urllib.parse import urlencode

import aiohttp
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from sanic import Sanic
from sanic.exceptions import abort
from sanic.response import raw

load_dotenv()

GRAVATAR_URL = "https://www.gravatar.com/avatar/{}?{}"

app = Sanic(__name__)
f = Fernet(bytes(os.getenv("KEY"), 'ascii'))


@app.listener('before_server_start')
def init(app, loop):
    app.aiohttp_session = aiohttp.ClientSession(loop=loop)


@app.listener('after_server_stop')
def finish(app, loop):
    loop.run_until_complete(app.aiohttp_session.close())
    loop.close()


@app.route('/avatar/<email>')
async def avatar(request, email):
    # process the input
    try:
        email = f.decrypt(bytes(email, 'ascii'))
    except InvalidToken:
        abort(404)

    size = request.args.get('s', default='64')

    # get the URL we are going to need for Gravatar
    email_encoded = md5(email.lower()).hexdigest()  # nosec
    parameters = urlencode({
        's': str(size),
        'd': '404'
    })

    url = GRAVATAR_URL.format(email_encoded, parameters)

    # fetch the avatar, and send it off
    async with app.aiohttp_session.get(url) as resp:
        if resp.status == 404:
            abort(404)

        data = await resp.read()
        return raw(data, content_type=resp.content_type)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
