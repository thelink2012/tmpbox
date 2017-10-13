# tmpbox

This is a simple filebin, it (almost) only takes care of receiving POST requests and storing the posted files into the server. No databases are used whatsoever. The result is less than 200 lines of Python.

## Non Features

* Need the creation time of files? or is it the last access time? Does not matter. Use the filesystem stats instead.
* Need credentials? Use HTTP Basic Auth or something.
* Need a little more? Fork and improve for your needs.
* Found a bug or flaw? Would be glad to help :)

## Install

Python 3.6+ is needed, then install the required dependencies:
    
    $ pip install -r requirements.txt

To run, simply execute the `tmpbox.py` like in one of the following lines:

    $ python3 tmpbox.py --port=8080
    $ python3 tmpbox.py --path=/tmp/tmpbox.socket
    $ python3 --help  # for more options

## Usage

Just POST a multipart file form into the server, and you'll get a line-separated list of URLs representing the resources of the uploaded files, now with random names.

    $ curl -sF u=@/path/to/file.png https://example.com
    https://example.com/qUeiJO.png
    $ curl -sF u=@- https://example.com < /path/to/file.png
    https://example.com/piMeNTa.png
    $ echo hi | curl -sF u=@- https://example.com
    https://example.com/TeMer

Since for debugging purposes a GET method is provided, an additional feature of specifying any extension you want is provided. But remember, using the web server for serving is the way to go! You can mix both of course, using our GET as a fallback :)

For instance, you could access the response URLs above in the following manners:

    $ curl https://example.com/qUeiJO.png 
    $ curl https://example.com/qUeiJO.bin
    $ curl https://example.com/piMeNTA.pdf
    $ curl https://example.com/TeMer.txt
    $ curl https://example.com/TeMer.cpp

