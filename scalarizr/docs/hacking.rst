.. header:: Scalarizr tests coding rules

Старые bdd functional тесты переезжают в папку scalarizr с полным переписыванием кода на python 3.7 и заменой lettuce тест раннера на pytest.

Структура
=========

::

    /scalarizr
     │
     ├─ docs
     ├─ lib
     ├─ databases
     │  ├─ common
     │  │  ├─ redis.py
     │  │  └─ ...
     │  ├─ test_redis.py
     │  └─ ...
     ├─ lifecycle
     │  └─ ...
     ...
     ├─ plugins
     ├─ conftest.py
     └─ pytest.ini

Базовой директорией тестов является ``revizor-tests/scalarizr``. Из важного в ней лежат ``pytest.ini`` и рутовый ``conftest.py``.

Тесты сгруппированы по папкам так же, как и раньше - ``databases``, ``lifecycle`` etc.

В папке plugins находятся наши pytest плагины, которые обеспечивают корректный запуск тестов, консольный вывод, добавляют поддержку маркировки тестов, пропуска степов и т.п.

Миграция тестов
===============

Заменяем старые \*.feature файлы обычными питоньими модулями. При этом соблюдается следующий маппинг:

* feature-файл → модуль
* feature → тест-класс
* scenario → тест-метод
* step → блок кода либо вызов функции (последнее предпочтительнее, где это возможно)

Примерный результат должен выглядеть так:

Было

``lifecycle_linux.feature``

::

    Feature: Linux server lifecycle

        @ec2 @vmware @gce @boot
        Scenario: Bootstraping
            Given I have a clean and stopped farm
            And I add role to this farm with storages,noiptables

Стало

``test_lifecycle_linux.py``

.. code-block:: python

    class TestLifecycleLinux:
        @pytest.mark.boot
        @pytest.mark.platform('ec2', 'vmware', 'gce')
        def test_bootstrapping(self):
            farm = get_clean_farm()
            add_role_to_farm(farm, role_options=['storages', 'noiptables'])

При переводе соблюдаем именование для pytest: модуль ``test_*.py``, класс ``Test*``, метод ``test_*``.

Обязательно всем тест-классам и методам добавляем докстринг, как правило просто копируя соответствующие строки из feature-файлов. Это позволяет иметь наглядный вывод тест-сессии в консоль:

::

    ============================================================== test session starts ==============================================================
    platform darwin -- Python 3.7.0, pytest-3.8.0, py-1.5.4, pluggy-0.7.1
    rootdir: /Users/petro/scalr/src/revizor-tests/scalarizr, inifile: pytest.ini
    collected 3 items


      Linux server lifecycle
      In order to manage server lifecycle
      As a scalr user
      I want to be able to monitor server state changes

    √ Bootstrapping                                                                                     TestLifecycleLinux.test_bootstrapping [ 33%]
    ~ Verify szradm list-roles                                                                       TestLifecycleLinux.test_szradm_listroles [ ~ %]


Очередность тестов
------------------

Для соблюдения строгой очередности тест-методов реализован и подключен плагин ordering. За порядок тестов отвечает аттрибут класса ``order``, его наличие в тест-классе обязательно, так же как и наличие всех тест-методов класса в этом списке.

.. code-block:: python

    class TestLifecycleLinux:

        order = ('test_bootstrapping',
                 'test_szradm_listroles',
                 'test_attached_storages')

Маркеры и декораторы для пропуска по условию
============================================

Леттюсовские аттрибуты сценариев для тэгирования по поддерживаемому клауду (``@ec2 @gce`` etc) реализованы в виде pytest маркера ``platform`` и переносятся соответственно в новые тесты:

.. code-block:: python

    @pytest.mark.platform('ec2', 'vmware', 'gce')
    def test_bootstrapping(self):
        pass

Тесты, у которых в этом маркере нету клауда, для которого запущена тест-сессия, будут исключены из выборки. Отсутствие маркера ``platform`` значит, что тест актуальный для всех клаудов.

Пропуск отдельных степов по условию остается таким же (``run_only_if`` декоратор).

Остальные (не клауд) маркеры ставятся аналогично старым, при добавлении новых *обязательно* нужно зарегистрировать их в ``scalarizr/plugins/revizor.py:pytest_configure``. Посмотреть список уже существующих можно командой ``pytest --markers``.

Для исключения из сессии тестов с конкретными маркерами, используется стандартная pytest опция ``-m``:

::

    pytest -m "not szradm"

Фикстуры
========

Доступные фикстуры (в том числе кастомные, реализованные в conftest файлах и pytest плагинах) можно просмотреть с помощью команды

::

    pytest --fixtures

TODO: описать соглашение по использованию фикстур, готовые фикстуры, сохранение стейта. Добавить фикстурам докстринги.

Запуск
======

Базовая директория для запуска тестов - ``/revizor-tests/scalarizr``, так как в ней находятся ``pytest.ini`` и корневой ``conftest.py`` файлы.

Вместо экспортирования переменных окружения, входные данные для теста задаются аргументами командной строки pytest. Список аргументов можно увидеть командой ``pytest --help`` в секции custom options:

::

    pytest --help
    ...
    custom options:
      --te-id=TE_ID
      --farm-id=FARM_ID
      --platform=PLATFORM
      --dist=DIST

Запуск конкретного теста будет выглядеть примерно так:

::

    pytest --te-id=f3445f199cc0 --dist=ubuntu1404 --platform=gce -m 'not szradm' lifecycle/test_lifecycle_linux.py

Другие полезные опции:

--no-stop-farm          не терминейтить ферму после окончания теста
-x                      аналог --failfast в леттюсе - тест останавливается после первого зафейлившегося теста
--maxfail=n             остановить тестовую сессию после n фейлов


Общие рекомендации
==================

Type annotation
---------------

TODO
