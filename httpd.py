#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from urllib.parse import unquote
import re
import logging
import argparse
import configparser
from pathlib import Path
import queue
from threading import Thread
from responses import Response, NOTFOUND_RESPONSE, OTHER_RESPONSE
from constants import OK, MIME_TYPES

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname).1s [%(threadName)s] %(message)s',
                    datefmt='%Y.%m.%d %H:%M:%S')

PATTERN = re.compile(r'(?P<method>[A-Z]*?)\s*(?P<resource>\S+)\sHTTP/1.(1|0).*\r\n\r\n', re.DOTALL)


def init_config():
    """Init configuration"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", metavar='<path>', dest='config', help="path to config file", default='settings.ini')
    conf_file = parser.parse_args().config

    if not Path(conf_file).exists():
        raise Exception('Config file not found')

    return conf_file


def parse_config(conf_file):
    """Parsig configuration file"""
    try:
        cp = configparser.ConfigParser()
        cp.read(conf_file)
        cp_section = cp['config']
        host = cp_section.get('HOST')
        port = int(cp_section.get('PORT'))
        root_dir = cp_section.get('ROOT_DIR')
        buffsize = int(cp_section.get('BUFFSIZE'))
        socket_timeout = int(cp_section.get('SOCKET_TIMEOUT'))
        workers = int(cp_section.get('WORKERS'))
        return host, port, root_dir, buffsize, socket_timeout, workers
    except:
        raise Exception('Config file parsing error')


def parse_request(request):
    math = PATTERN.search(request)
    return math.groupdict() if math else None


def get_request(connection, buffsize):
    raw_data = b''
    while True:
        try:
            chunk = connection.recv(buffsize)
            raw_data += chunk
            if not chunk or b'\r\n\r\n' in chunk:
                break
        except Exception as e:
            break
    return raw_data


def validate_path(path, root_dir):
    resource = unquote(path).split('?')[0][1:]  # without args and first "/"
    resource_path = Path(resource).resolve()

    if any([resource_path.is_file() and resource.endswith('/'),
            not resource_path.exists(),
            Path(root_dir).resolve() not in resource_path.parents,
            resource_path.is_dir() and not resource_path.joinpath('index.html').exists(),
            ]):
        return False

    logging.info(f'Requested file "{resource_path}" FOUND')
    return resource_path if resource_path.is_file() else resource_path / 'index.html'


class RequestHandler:

    available_methods = ('GET', 'HEAD')

    def __init__(self, clients_queue, buffsize, root_dir):
        self.queue = clients_queue
        self.buffsize = buffsize
        self.root_dir = root_dir
        self.method = None
        self.resource = None

    def run(self):
        logging.info('Thread started')

        while True:
            connection = self.queue.get()
            logging.info('NEW TASK STARTED')
            try:
                raw_data = get_request(connection, self.buffsize)
                logging.info(f'Received request: {raw_data}')

                parsed_request = parse_request(raw_data.decode())
                logging.info(f'Parsed request: {parsed_request}')

                if parsed_request:
                    self.method, self.resource = parsed_request.values()
                    answer = self.make_report()
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
            self.queue.task_done()
            logging.info('TASK_DONE')

    def make_report(self):
        if self.method in self.available_methods:
            response = self.make_response()
            report = response.make_answer()
        else:
            logging.info(f'Method "{self.method}" is not allowed')
            report = OTHER_RESPONSE.make_answer()
        return report

    def make_response(self):
        valid_resourse = validate_path(unquote(self.resource), self.root_dir)
        if not valid_resourse:
            logging.info('Requested file is not allowed or not exist')
            return NOTFOUND_RESPONSE

        return Response(code=OK,
                        content=valid_resourse.read_bytes() if self.method == 'GET' else None,
                        lengt=valid_resourse.stat().st_size,
                        mime_type=MIME_TYPES.get(valid_resourse.suffix[1:]),
                        method=self.method)


def main():
    HOST, PORT, ROOT_DIR, BUFFSIZE, SOCKET_TIMEOUT, WORKERS = parse_config(init_config())
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(WORKERS)
    logging.info('Starting server in {}:{} with {} worker(s)'.format(HOST, PORT, WORKERS))

    clients_queue = queue.Queue(WORKERS)
    for _ in range(WORKERS):
        this_thread = Thread(target=RequestHandler(clients_queue, BUFFSIZE, ROOT_DIR).run, daemon=False)
        this_thread.start()

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
