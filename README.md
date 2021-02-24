## Веб-сервер частично реализующий протокол HTTP
### Описание
Сервер представляет собой простой HTTP сервер, реализующий методы GET и HEAD.
Возвращает файлы по произвольному пути в ROOT_DIR. Для конкурентной обрабоки входящих запросов, используются Thread-ы.


### Запуск
```python httpd.py```

при запуске позволяет задавать количество worker-ов, указав аргумент командной строки -w.

### Нагрузочные тесты сервера
Сервер запущенный с 20 worker-ми, на хосте с:
* Ubuntu 20 amd64
* 1 CPU / 4 Core / 4000 MHz
* 4Gb RAM

тестировался с помощью **wrk** в течении 5 минут, с количеством 100 открытых HTTP соединений.

__Результаты__
```
wrk -c100 -t1 -d5m http://127.0.0.1:8080/

Running 5m test @ http://127.0.0.1:8080/
  1 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    64.59ms   90.26ms   1.86s    95.46%
    Req/Sec   242.72     38.98   360.00     65.69%
  72517 requests in 5.00m, 6.98MB read
  Socket errors: connect 0, read 72534, write 0, timeout 23
  Non-2xx or 3xx responses: 72517
Requests/sec:    241.69
Transfer/sec:     23.84KB
```


### Совместимость
Python 3.6 +

### Тесты
Тесты брать из
[http-test-suite](https://github.com/s-stupnikov/http-test-suite)

Запуск тестов:</br>
```python3 -m unittest httpdtest.py```