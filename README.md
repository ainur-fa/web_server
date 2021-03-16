## Веб-сервер частично реализующий протокол HTTP
### Описание
Сервер представляет собой простой HTTP сервер, реализующий методы GET и HEAD.
Возвращает файлы по произвольному пути в ROOT_DIR. Для конкурентной обрабоки входящих запросов, используются Thread-ы.


### Запуск
```python httpd.py --config=[путь до файла с конфигурацией]```

Пример конфигурационного файла:
```
[config]
WORKERS = 30
SOCKET_TIMEOUT = 30
BUFFSIZE = 1024
ROOT_DIR = httptest
HOST = localhost
PORT = 8080
```


### Нагрузочные тесты сервера
Сервер запущенный с 20 worker-ми, на хосте с:
* Windows 10 x64
* CPU Intel Core i7-2600
* 32Gb RAM

Тестирование производилось с помощью *ApacheBench*:
ab.exe -n 50000 -c 100 -r http://localhost:8080/

__Результаты__
```
Server Software:        MyTestServer
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   902.198 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      5050000 bytes
HTML transferred:       0 bytes
Requests per second:    55.42 [#/sec] (mean)
Time per request:       1804.397 [ms] (mean)
Time per request:       18.044 [ms] (mean, across all concurrent requests)
Transfer rate:          5.47 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   18  92.1      0     510
Processing:    11 1781 254.6   1554    2067
Waiting:        2 1005 433.0   1026    1565
Total:         11 1799 254.9   2041    2067

Percentage of the requests served within a certain time (ms)
  50%   2041
  66%   2044
  75%   2046
  80%   2047
  90%   2049
  95%   2053
  98%   2057
  99%   2060
 100%   2067 (longest request)
```


### Совместимость
Python 3.6 +

### Тесты
Тесты брать из
[http-test-suite](https://github.com/s-stupnikov/http-test-suite)

Запуск тестов:</br>
```python3 -m unittest httpdtest.py```