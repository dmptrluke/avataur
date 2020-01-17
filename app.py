import argparse
from hashlib import md5
from urllib.parse import urlencode

import aiohttp
from aiohttp import web
from aiohttp.web_response import Response
from cryptography.fernet import Fernet, InvalidToken

parser = argparse.ArgumentParser()
parser.add_argument('--key')
parser.add_argument('--path')
parser.add_argument('--port')

GRAVATAR_URL = "https://www.gravatar.com/avatar/{}?{}"

routes = web.RouteTableDef()


async def client_session(app):
    app['client_session'] = aiohttp.ClientSession()
    yield
    await app['client_session'].close()


@routes.get('/avatar/{email}')
async def avatar(request):
    # process the input
    try:
        email = app['fernet'].decrypt(bytes(request.match_info['email'], 'ascii'))
    except InvalidToken:
        raise web.HTTPNotFound

    size = request.query.get('s', default='64')

    # get the URL we are going to need for Gravatar
    email_encoded = md5(email.lower()).hexdigest()  # nosec
    parameters = urlencode({
        's': str(size),
        'd': '404'
    })

    url = GRAVATAR_URL.format(email_encoded, parameters)

    # fetch the avatar, and send it off
    async with app['client_session'].get(url) as resp:
        if resp.status == 404:
            # todo: placeholder
            raise web.HTTPNotFound

        data = await resp.read()

    return Response(body=data, content_type=resp.content_type)


if __name__ == '__main__':
    app = web.Application()
    args = parser.parse_args()

    app.cleanup_ctx.append(client_session)

    app['fernet'] = Fernet(bytes(args.key, 'ascii'))

    app.add_routes(routes)
    web.run_app(app, path=args.path, port=args.port)
