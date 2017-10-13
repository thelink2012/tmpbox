#!/usr/bin/env python3
import os
import argparse
import string
import random
import mimetypes

from aiohttp import web


USAGE = """{HOST}(1)
    
NAME
        {HOST} -- temporary box

SYNOPSIS
        curl -sF u=@file {URI}

EXAMPLES
        $ curl -sF u=@/path/to/file.png {URI}
        $ curl -sF u=@- {URI} < /path/to/file.png
        $ echo hi | curl -sF u=@- {URI}
        ^D

CAVEATS
        size limit is {MAX_UPLOAD_SIZE} bytes
"""


def random_filename(app):
    """Outputs a random filename for the uploaded file."""
    return ''.join([random.choice(app['charset']) for _ in range(6)])


def uri(request):
    """Gets the URI for the application."""
    if request.app['https']:
        return 'https://' + request.headers['Host']
    else:
        return 'http://' + request.headers['Host']


async def help(request):
    """Display usage of the tool."""
    max_size = request.app['max_upload_size']
    return web.Response(text=USAGE.format(HOST=request.headers['Host'],
                                          URI=uri(request),
                                          MAX_UPLOAD_SIZE=max_size))


async def upload(request):
    """POST request to upload a file into the server."""
    reader = await request.multipart()
    files_uploaded = []
    total_size = 0
    max_upload_size = request.app['max_upload_size']
    async for part in reader:
        _, extension = os.path.splitext(part.filename or '')
        resource_name = random_filename(request.app) + extension
        with open(os.path.join(request.app['storage_path'], resource_name), 'wb') as f:
            while True:
                if total_size >= max_upload_size:
                    raise web.HTTPRequestEntityTooLarge();
                chunk = await part.read_chunk()
                if not chunk:
                    break
                total_size += len(chunk)
                f.write(chunk)
        files_uploaded.append(f'{uri(request)}/{resource_name}')
    return web.Response(text='\n'.join(files_uploaded))


async def download(request):
    """
    GET request to retrieve a file from the server.

    This is a placeholder and using the web server as the
    content provider is a better alternative.
    """

    resource_name = request.match_info['resource']
    resource_path = os.path.join(request.app['storage_path'], resource_name)
    basename, extension = os.path.splitext(resource_name)

    # If there is no such file in the storage path, try finding one with the 
    # same basename, as such the extension will only affect the mimetype.
    if not os.path.isfile(resource_path):
        for entry in os.scandir(request.app['storage_path']):
            if entry.name.startswith(basename):
                if (len(entry.name) == len(basename) or entry.name[len(basename)] == '.'):
                    resource_path = entry.path
                    break
        else:
            raise web.HTTPNotFound()

    content_type, _ = mimetypes.guess_type(resource_name, strict=True)
    if content_type is None:
        content_type = 'application/octet-stream'

    response = web.FileResponse(resource_path)
    response.content_type = content_type
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


def app_factory():
    """Factory for aiohttp development tools."""
    app = web.Application()
    app.router.add_post('/', upload)
    app.router.add_get('/', help)
    res = app.router.add_resource('/{resource}')
    res.add_route('GET', download);
    return app



parser = argparse.ArgumentParser(description="tmpbox server")
parser.add_argument('--path', help="Opens a Unix Socket at path")
parser.add_argument('--port', type=int, help="Opens a connection at port")
parser.add_argument('--https', action='store_true', help="Use HTTPS URLs")
parser.add_argument('--max-upload', help="The maximum size of a file in bytes",
                                    type=int, default=10*1024*1024)  # 10MiB
parser.add_argument('--charset', help="Set of characters used to form a id",
                                 default=string.ascii_letters + string.digits)
parser.add_argument('--storage-path', help="Path to store the uploaded files",
                                      default='files')

if __name__ == "__main__":
    app = app_factory()
    args = parser.parse_args()

    app['https'] = args.https
    app['max_upload_size'] = args.max_upload
    app['charset'] = args.charset

    if os.path.isabs(args.storage_path):
        app['storage_path'] = args.storage_path
    else:
        this_dir = os.path.join(os.path.split(__file__)[0])
        joined_path = os.path.join(this_dir, args.storage_path)
        app['storage_path'] = os.path.abspath(joined_path)

    assert not any(c in app['charset'] for c in ['/', '\\', '.'])
    os.makedirs(app['storage_path'], exist_ok=True)

    web.run_app(app, path=args.path, port=args.port)

