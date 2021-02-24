# -*- coding: utf-8 -*-
from datetime import datetime
from constants import *

CRLF = b'\r\n'


class Response:

    def __init__(self, code=None, content=None, mime_type=None, lengt=None, method=None):
        self.code = code
        self.content = content
        self.mime_type = mime_type
        self.lengt = lengt
        self.method = method

    def make_answer(self):
        report = [RESPONSE_HEADERS.get(self.code),
                  f'Date: {datetime.today().strftime("%a, %d %b %Y %H:%M:%S %Z")}'.encode(),
                  b'Server: MyTestServer',
                  b'Connection: close', ]
        if self.content:
            report.extend([f'Content-Length: {self.lengt}'.encode(),
                           f'Content-Type: {self.mime_type}'.encode()])

        report.append(CRLF + self.content) if self.method == 'GET' else report.append(CRLF)
        return CRLF.join(report)


FORBIDDEN_RESPONSE = Response(code=403)
NOTFOUND_RESPONSE = Response(code=404)
OTHER_RESPONSE = Response(code=405)
