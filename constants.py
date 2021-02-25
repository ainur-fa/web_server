# -*- coding: utf-8 -*-

FORBIDDEN = 403
OK = 200
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405

DEFAULT_CONFIG = {'WORKERS': 20,
                  'SOCKET_TIMEOUT': 30,
                  'BUFFSIZE': 1024,
                  'ROOT_DIR': 'httptest',
                  'HOST': 'localhost',
                  'PORT': 8080}


RESPONSE_HEADERS = {OK: b"HTTP/1.1 200 OK",
                    FORBIDDEN: b"HTTP/1.1 403 Forbidden",
                    NOT_FOUND: b"HTTP/1.1 404 Not Found",
                    METHOD_NOT_ALLOWED: b"HTTP/1.1 405 Method Not Allowed"}


MIME_TYPES = {'html': 'text/html',
              'css': 'text/css',
              'txt': 'text/plain',
              'js': 'text/javascript',
              'jpg': 'image/jpeg',
              'jpeg': 'image/jpeg',
              'png': 'image/png',
              'gif': 'image/gif',
              'swf': 'application/x-shockwave-flash'}
