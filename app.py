#!/usr/bin/env python3
import os
import string
import random
import mimetypes

from aiohttp import web

# TODO header nosniff

BASE_URI = 'tmp.thelink2012.xyz'
PATH_STORAGE = os.path.abspath(os.path.split(__file__)[0] + '/files')
MAX_UPLOAD_SIZE = 1024*1024*10   # 10MiB

USAGE = f"""{BASE_URI}(1)
    
NAME
        {BASE_URI} -- temporary box

SYNOPSIS
        curl -sF u=@file {BASE_URI}

EXAMPLES
        $ curl -sF u=@/path/to/file.png {BASE_URI}
        $ curl -sF u=@- < /path/to/file.png
        $ echo hi | curl -sF u=@-
        ^D

CAVEATS
        size limit is {MAX_UPLOAD_SIZE} bytes

SEE ALSO
        p.iotek.org
"""


def random_filename():
    """Outputs a random filename for the uploaded file."""
    charset = string.ascii_letters + string.digits
    return ''.join([random.choice(charset) for _ in range(6)])


async def upload_usage(request):
    return web.Response(text=USAGE)


async def upload(request):
    """POST request to upload a file into the server."""
    reader = await request.multipart()
    files_uploaded = []
    total_size = 0
    async for part in reader:
        _, extension = os.path.splitext(part.filename or '')
        resource_name = random_filename() + extension
        with open(os.path.join(PATH_STORAGE, resource_name), 'wb') as f:
            while True:
                if total_size >= MAX_UPLOAD_SIZE:
                    raise web.HTTPRequestEntityTooLarge();
                chunk = await part.read_chunk()
                if not chunk:
                    break
                total_size += len(chunk)
                f.write(chunk)
        files_uploaded.append(f'{BASE_URI}/{resource_name}')
    return web.Response(text='\n'.join(files_uploaded))


async def download(request):
    """
    GET request to retrieve a file from the server.

    This is a placeholder and using the web server as the
    content provider is a better alternative.
    """
    resource_name = request.match_info['resource']
    resource_path = f'{PATH_STORAGE}/{resource_name}' 
    _, extension = os.path.splitext(resource_name)

    if not os.path.isfile(resource_path):
        raise web.HTTPNotFound()

    content_type, encoding = mimetypes.guess_type(extension, strict=True)
    if content_type is None:
        content_type = 'application/octet-stream'

    response = web.FileResponse(resource_path)
    response.content_type = content_type
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


def app_factory():
    os.makedirs(PATH_STORAGE, exist_ok=True)
    app = web.Application()
    app.router.add_post('/', upload)
    app.router.add_get('/', upload_usage)
    res = app.router.add_resource('/{resource}')
    res.add_route('GET', download);
    return app


if __name__ == "__main__":
    app = app_factory()
    web.run_app(app)

