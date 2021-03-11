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
from responses import Response, NOTFOUND_RESPONSE, OTHER_RESPONSE
from constants import OK, MIME_TYPES, DEFAULT_CONFIG

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname).1s [%(threadName)s] %(message)s',
                    datefmt='%Y.%m.%d %H:%M:%S')

HOST = DEFAULT_CONFIG['HOST']
PORT = DEFAULT_CONFIG['PORT']
ROOT_DIR = DEFAULT_CONFIG['ROOT_DIR']
BUFFSIZE = DEFAULT_CONFIG['BUFFSIZE']
SOCKET_TIMEOUT = DEFAULT_CONFIG['SOCKET_TIMEOUT']
PATTERN = re.compile(r'(?P<method>[A-Z]*?)\s*(?P<resource>\S+)\sHTTP/1.(1|0).*\r\n\r\n', re.DOTALL)


def get_workers_count():
    """Init configuration"""
    ap = argparse.ArgumentParser()
    ap.add_argument("-w", metavar='<path>', dest='workers_count', help="workers count",
                    default=DEFAULT_CONFIG['WORKERS'])
    return int(ap.parse_args().workers_count)


WORKERS = get_workers_count()


def parse_request(request):
    math = PATTERN.search(request)
    return math.groupdict() if math else None


class Worker:

    def main_handler(self, queue):
        logging.info('Thread started')
        while True:
            connection = queue.get()
            logging.info('NEW TASK STARTED')
            try:
                parsed_request, raw_data = self.get_request(connection)
                logging.info(f'Received request: {raw_data}')
                logging.info(f'Parsed request: {parsed_request}')

                if parsed_request:
                    answer = self.router(parsed_request)
                    logging.info('CORRECT REQUEST')
                else:
                    answer = OTHER_RESPONSE.make_answer()
                    logging.info('Method Not Allowed')

                connection.sendall(answer)
                logging.info('Answer sent successfully')

            except Exception as e:
                raise e
            finally:
                try:
                    connection.close()
                except Exception as e:
                    logging.error(f'Error closing connection: {e}')
            queue.task_done()
            logging.info('TASK_DONE')

    def get_request(self, connection):
        raw_data = b''
        while True:
            try:
                chunk = connection.recv(BUFFSIZE)
                raw_data += chunk
                if not chunk or b'\r\n\r\n' in chunk:
                    break
            except Exception as e:
                break
        parsed_request = parse_request(raw_data.decode())
        return parsed_request, raw_data

    def get_file_data(self, file):
        file = Path(file).resolve()
        content = Path(file).read_bytes() if file.is_file() else (Path(file) / 'index.html').read_bytes()
        length = len(content)
        extension = Path(file).suffix[1:]
        return namedtuple('file', ['content', 'length', 'extension'])(content, length, extension)

    def validate_resource(self, resource):
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

    def method_handler(self, method, resource: str):
        valid_resourse = self.validate_resource(resource)
        if not valid_resourse:
            logging.info('Requested file is not allowed or not exist')
            return NOTFOUND_RESPONSE

        file = self.get_file_data(valid_resourse)
        return Response(code=OK,
                        content=file.content if method == 'GET' else None,
                        lengt=file.length,
                        mime_type=MIME_TYPES.get(file.extension),
                        method=method)

    def router(self, parsed_request):
        available_methods = ('GET', 'HEAD')
        method, resource = parsed_request.values()
        if method in available_methods:
            response = self.method_handler(method, unquote(resource))
            report = response.make_answer()
        else:
            logging.info(f'Method "{method}" is not allowed')
            report = OTHER_RESPONSE.make_answer()
        return report


def run_workers(count, clients_queue):
    worker = Worker()
    for _ in range(count):
        this_thread = Thread(target=worker.main_handler, args=(clients_queue,), daemon=False)
        this_thread.start()


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    logging.info('Starting server in {}:{} with {} worker(s)'.format(HOST, PORT, WORKERS))
    sock.bind((HOST, PORT))
    sock.listen(WORKERS)
    clients_queue = queue.Queue(WORKERS)
    run_workers(WORKERS, clients_queue)

    try:
        while True:
            logging.info('Wait connections ...')
            connection, client_address = sock.accept()
            connection.settimeout(SOCKET_TIMEOUT)
            logging.info('Connected to: %s', client_address)
            clients_queue.put(connection)
    except KeyboardInterrupt:
        sock.close()
        clients_queue.join()


if __name__ == '__main__':
    main()
