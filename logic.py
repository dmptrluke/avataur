from hashlib import md5
from urllib.parse import urlencode

GRAVATAR_URL = "https://www.gravatar.com/avatar/{}?{}"


async def get_url(email, size) -> str:
    # get the URL we are going to need for Gravatar
    email_encoded = md5(email.lower().encode('utf8')).hexdigest()  # nosec

    if size > 512:
        size = 512

    parameters = urlencode({
        's': str(size),
        'd': '404'
    })

    return GRAVATAR_URL.format(email_encoded, parameters)
