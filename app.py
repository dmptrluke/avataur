import argparse
import json

import aiohttp
from aiohttp import web
from aiohttp.web_response import Response
from cryptography.fernet import Fernet, InvalidToken

from logic import get_url

parser = argparse.ArgumentParser()
parser.add_argument('--key')
parser.add_argument('--path')
parser.add_argument('--port')


routes = web.RouteTableDef()


async def client_session(app):
    app['client_session'] = aiohttp.ClientSession()
    yield
    await app['client_session'].close()


@routes.get('/avatar/{token}')
async def avatar(request):
    # process the input
    try:
        token = bytes(request.match_info['token'], 'utf8')
        data = request.app['fernet'].decrypt(token)
    except InvalidToken:
        raise web.HTTPNotFound

    data = json.loads(data)

    email = data['email']
    size = data.get('size', 128)
    fallback = data.get('fallback', None)

    url = await get_url(email, size)

    # fetch the avatar, and send it off
    async with request.app['client_session'].get(url) as resp:
        if resp.status == 404:
            if fallback:
                raise web.HTTPFound(fallback)
            else:
                raise web.HTTPNotFound

        data = await resp.read()

    return Response(body=data, content_type=resp.content_type)


def get_app():
    app = web.Application()
    app['args'] = parser.parse_args()
    app['fernet'] = Fernet(bytes(app['args'].key, 'ascii'))
    app.cleanup_ctx.append(client_session)
    app.add_routes(routes)
    return app


async def get_app_async():
    return get_app()

if __name__ == '__main__':
    application = get_app()
    web.run_app(application, path=application['args'].path, port=application['args'].port)
