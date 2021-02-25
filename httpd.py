#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from urllib.parse import unquote
import re
import logging
import argparse
from pathlib import Path
from collections import namedtuple
import queue
from threading import Thread
from responses import *
from constants import *

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname).1s [%(threadName)s] %(message)s',
                    datefmt='%Y.%m.%d %H:%M:%S')

HOST = DEFAULT_CONFIG['HOST']
PORT = DEFAULT_CONFIG['PORT']
ROOT_DIR = DEFAULT_CONFIG['ROOT_DIR']
BUFFSIZE = DEFAULT_CONFIG['BUFFSIZE']
SOCKET_TIMEOUT = DEFAULT_CONFIG['SOCKET_TIMEOUT']
PATTERN = re.compile(r'(?P<method>[A-Z]*?)\s*(?P<resource>\S+)\sHTTP/1.(1|0).*\r\n\r\n', re.DOTALL)


def init_config():
    """Init configuration"""
    ap = argparse.ArgumentParser()
    ap.add_argument("-w", metavar='<path>', dest='workers_count', help="workers count",
                    default=DEFAULT_CONFIG['WORKERS'])
    return int(ap.parse_args().workers_count)


WORKERS = init_config()


def parse_request(request):
    math = PATTERN.search(request)
    return math.groupdict() if math else None


class Worker:

    @classmethod
    def main_handler(cls, queue):
        logging.info('Thread started')
        while True:
            connection = queue.get()
            logging.info('NEW TASK STARTED')
            try:
                parsed_request, raw_data = cls.get_request(connection)
                logging.info(f'Received request: {raw_data}')
                logging.info(f'Parsed request: {parsed_request}')

                if parsed_request:
                    answer = cls.router(parsed_request)
                    logging.info('CORRECT REQUEST')
                else:
                    answer = OTHER_RESPONSE.make_answer()
                    logging.info('Method Not Allowed')

                connection.sendall(answer)
                logging.info('Answer sent successfully')

            except Exception as e:
                raise e
                # logging.error(e)
            finally:
                try:
                    connection.close()
                except Exception as e:
                    logging.error(f'Error closing connection: {e}')
            queue.task_done()
            logging.info('TASK_DONE')

    @classmethod
    def get_request(cls, connection):
        raw_data = b''
        while True:
            try:
                chunk = connection.recv(BUFFSIZE)
                raw_data += chunk
                if not chunk or len(chunk) < BUFFSIZE:
                    break
            except Exception as e:
                break
        parsed_request = parse_request(raw_data.decode())
        return parsed_request, raw_data

    @classmethod
    def get_file_data(cls, file):
        file = Path(file).resolve()
        content = Path(file).read_bytes() if file.is_file() else (Path(file) / 'index.html').read_bytes()
        length = len(content)
        extension = Path(file).suffix[1:]
        return namedtuple('file', ['content', 'length', 'extension'])(content, length, extension)

    @classmethod
    def validate_resource(cls, resource):
        resource = resource.split('?')[0][1:]  # without args and first "/"
        resource_path = Path(resource).resolve()

        if any([resource_path.is_file() and resource.endswith('/'),
                not resource_path.exists(),
                Path(ROOT_DIR).resolve() not in resource_path.parents,
                resource_path.is_dir() and not resource_path.joinpath('index.html').exists(),
                ]):
            return False

        logging.info(f'Requested file "{resource_path}" FOUND')
        return str(resource_path)

    @classmethod
    def method_handler(cls, method, resource: str):
        valid_resourse = cls.validate_resource(resource)
        if not valid_resourse:
            logging.info('Requested file is not allowed or not exist')
            return NOTFOUND_RESPONSE

        file = cls.get_file_data(valid_resourse)
        content_type = MIME_TYPES.get(file.extension)
        return Response(code=OK, content=file.content, lengt=file.length, mime_type=content_type, method=method)

    @classmethod
    def router(cls, parsed_request):
        available_methods = ('GET', 'HEAD')
        method, resource = parsed_request.values()
        if method in available_methods:
            response = cls.method_handler(method, unquote(resource))
            report = response.make_answer()
        else:
            logging.info(f'Method "{method}" is not allowed')
            report = OTHER_RESPONSE.make_answer()
        return report


class Munufacture:

    def __init__(self, workers):
        self.queue = queue.Queue(workers)
        [self._run_worker() for _ in range(workers)]

    def add_task(self, task):
        self.queue.put(task)

    def wait_task(self):
        self.queue.join()

    def _run_worker(self):
        this_thread = Thread(target=Worker.main_handler, args=(self.queue,), daemon=False)
        this_thread.start()


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    logging.info('Starting server in {}:{} with {} worker(s)'.format(HOST, PORT, WORKERS))
    sock.bind((HOST, PORT))
    sock.listen(WORKERS)
    tasks_queue = Munufacture(WORKERS)

    try:
        while True:
            logging.info('Wait connections ...')
            connection, client_address = sock.accept()
            connection.settimeout(SOCKET_TIMEOUT)
            logging.info('Connected to: %s', client_address)
            tasks_queue.add_task(connection)
    except KeyboardInterrupt:
        sock.close()
        tasks_queue.wait_task()


if __name__ == '__main__':
    main()
