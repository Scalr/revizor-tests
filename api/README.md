# Scalr API v.2 testing framework

Revizor2 надстройка основанная на Python 3, предназначена для автоматизации тестирования Scalr API, с простым, сжатым синтаксисом
опирающимся на [Scalr API Documentation](https://api-explorer.scalr.com) и использующая [pytest](https://docs.pytest.org/en/latest/) в качестве
утилиты написания тестов.

# Основные положения

## Установка
```bash
git clone git@github.com:Scalr/revizor.git /revizor
echo 'export PYTHONPATH="$PYTHONPATH:/revizor/src"' >> ~/.bash_profile
source ~/.bash_profile

sudo pip3 install -U -r /revizor/requirements.txt

git clone git@github.com:Scalr/revizor-tests.git /revizor-tests
sudo pip3 install -U -r /revizor-tests/api/requirements.txt
```

## Запуск тестов

### Аргументы командной строки

```bash
--te-id или --test-environment-id: Не создавать новое тестовое окружение использовать существующее.
Значение по умолчанию: None

--te-br или --test-environment-branch: Указывает ветку на базе которой создается тестовое окружение.
Значение по умолчанию: master

--te-notes: Добавляет комментарий к создаваемому тестовому окружению. Значание по умолчанию: ''

--te-creation-timeout или --te-ct: Устанавливает время доступа к запущенному ранее или создаваемому
контейнеру, по истечении указанного времени тест считается не пройденным.
Значение по умолчанию: 300

--te-no-delete: Указывает на необходимость сохранить запущенный или используемый контейнер по
окончании работы тестов. Значение по умолчанию: False

--flex-validation или --fv: Производить валидацию результатов api запросов на соответствие swagger
спецификации средствами сторонней библиотеки flex. Значение по умолчанию: False
```

### Пример запуска набора тестов с созданием тестового окружения, его сохранением и выполнением flex валидации

```bash
cd ~/revizor-tests/api
pytest --fv --te-no-delete tests/user/farms/test_farms.py
```

### Пример запуска кейса с использованием созданного ранее тестового окружения без его сохранения и выполненим flex валидации

```bash
cd ~/revizor-tests/api
pytest --fv --te-id 25b68333623a tests/user/farms/test_farms.py::TestEmptyFarm::test_deploy_empty_farm
```

# Написание тестов

## Общие положения:

Основным элементом api запроса является фикстура `api - session="module"`.
```python
@pytest.fixture(scope='module', autouse=True)
def api(request, fileutil):
    session = AppSession(request, fileutil)
    request.addfinalizer(session.close)
    return session
```
Данная фикстура является инстансом `AppSession - revizor-tests/api/plugins/app_session.py` класса имплементирующего функционал api
вызов и верификации request/response на соответствие  swagger спецификации.  Спецификация загружается со `Scalr` сервера на этапе
инициализации теста в зависимости от значения переменной `app_level`. Переменная определяется для каждого модуля содержащего описание
теста, после импорта используемых библиотек, зависит от уровня `API` запросов.
```python
import pytest

app_level='account'
.
.
.
```
Переменная может иметь одно из следующих значений `(user|account|global|system)`. Уровень `user` является дефолтным  и
не требует установки, т.е. тесты описывающие api запросы уровня `user` ее могут не содержать. Загруженная спецификация
сохраняется во временной папке, используется повторно при следующих запусках тестов того же `app_level`.

## Константы:

Наиболее часто встречающимся аргументом api запросов является платформа и связанные с ней атрибуты
`(name|location|instance_type|network|zone|subnet|resource_group|storage_account)`. Для работы с данным аргументом предусмотрен
набор констант `api/utils/consts.py` описывающих основные платформы `(AZURE|EC2|GCE|VMWARE|CLOUDSTACK|OPENSTACK)`

### Пример использования констант

```python
from api.utils.consts import Platform

# получение имени платформы передаваемого в api запрос
Platform.EC2
Platform.EC2.name

# получение атрибутов платформы
Platform.EC2.location
Platform.EC2.subnet

# использования списка платформ в запросах

for platform in (Platform.EC2, Platform.GCE):
    if platform.is_gce:
        body = dict(
            alias='{}-{}'.format(alias, platform),
            cloudLocation=platform.location,
            cloudPlatform=platform,
            instanceType={'id': platform.instance_type},
            availabilityZones=platform.zone,
            role={'id': role_id},
            networking=platform.network
        )
        # добавление роли в ферму
        resp = api.create(
            "/api/v1beta0/user/envId/farms/farmId/farm-roles/",
            params=dict(
                envId=env_id,
                farmId=farm_id),
            # передача body c предварительно удаленными пустыми полями, (None, {}, [])
            body=remove_empty_values(body))

# добавление дополнительных атрибутов к платформе в случае необходимости
class Platform(object):

    AZURE = PlatformStore(name='azure',
                          .
                          .
                          .
                          ext_attr='ext_attr')

    var = Platform.AZURE.ext_attr
```
## Конструирование api запросов:
Основой любого api теста является запрос. Данный framework в части конструирования запросов ориентирован на существующую
[Scalr API Documentation](https://api-explorer.scalr.com). Написание запроса начинается с открытия страницы спецификации
интересующего вызова и повторения описательной части документации в тесте средствами python.

### Пример простого запроса уровня user: [OS: List](https://api-explorer.scalr.com/user/os/get.html)
Страница документации начинается с заголовка `OS:List` кратко обозначающего область применения запроса и действие выполняемое
в рамках данной области. В описываемом случае областью применения является `OS`, а действием `List`. Далее документация содержит
описание точки входа в удаленное приложение `api endpoint`, перечисление обязательных и не обязательных параметров передаваемых
приложению, их расшифровку. Опираясь на выше изложенное напишем вызов удаленного метода приложения указав в качестве основы,
фикстуру 'api'. Действие, выполняемое над областью применения запроса, будет методом `api` фикстуры, точка входа в приложение, набор
обязательных и не очень аргументов параметрами предаваемыми в метод `api` фикстуры.

`Важно:` В качестве вызываемого метода фиксткры `api` указывается не тип api запроса `(get|post|patch|delete)`, а `lowercase` действие
над областью применения запроса указанное в заголовке `(list|get|create|delete|copy|.........)`

```python
api.list(
    # endpoint
    '/api/v1beta0/user/envId/os/',
    # обязательные параметры
    params=dict(
        envId='envId'
    )
)
```

### Пример запроса уровня user с расширенным списком передаваемых параметров: [Images: Create](https://api-explorer.scalr.com/user/images/post.html)
```python
body = {
  "architecture": "i386",
  "cloudFeatures": {
    "type": "ImageCloudFeatures"
  },
  "cloudImageId": "string",
  "cloudInitInstalled": true,
  "cloudLocation": "string",
  "cloudPlatform": "ec2",
  "deprecated": true,
  "name": "string",
  "os": {
    "id": "string"
  },
  "scalrAgentInstalled": true,
  "size": 1,
  "type": "string"
}

api.create(
    # endpoint
    '/api/v1beta0/user/envId/images/',
    # обязательные параметры
    params=dict(
        envId='envId'),
    # расширенные параметры
    body=body)
)
```

### Пример простых тестов с  написанием запросов демонстрирующих основные методы передачи аргументов приложению
#### Передача обязательных параметров

```python
import pytest


class TestPassRequiredParameters(object):

    def test_os_get(self, api):
        # required params
        env_id = "5"
        os_id = "ubuntu-14-04"
        # Execute request
        resp = api.get(
            "/api/v1beta0/user/envId/os/osId/",
            params=dict(
                envId=env_id,
                osId=os_id))
        assert resp.box_repr.data.id == os_id
```

#### Передача обязательных параметров, сужение выборки путем фильтрации возвращаемых данных средствами api

```python
import pytest


class TestPassQueryFilters(object):

    def test_list_images(self, api):
        # required params
        env_id = 5
        # data filters
        platform = "ec2"
        os_id = "ubuntu-14-04"
        scope = "environment"
        agent_installed = True
        resp = api.list(
            "/api/v1beta0/user/envId/images/",
            params=dict(envId=env_id),
            filters=dict(
                cloudPlatform=platform,
                os=os_id,
                scalrAgentInstalled=agent_installed,
                scope=scope
            )
        )
        assert all(image.os.id == os_id for image in resp.box_repr.data)
```

#### Передача body в POST запросах

```python
import six
import pytest


class TestPassBodyToQuery(object):

    api = None
    env_id = 5

    @pytest.fixture(autouse=True, scope='class')
    def bootstrap(self, request, api):
        request.cls.api = api

    def create_role(self, os_id, role_category, role_name, builtin_automation=None):
        if isinstance(builtin_automation, six.string_types):
            builtin_automation = [builtin_automation]
        resp = self.api.create(
            "/api/v1beta0/user/envId/roles/",
            params=dict(envId=self.env_id),
            body=dict(
                builtinAutomation=builtin_automation,
                category={"id": role_category},
                name=role_name,
                os={"id": os_id}))
        return resp.box_repr.data

    def get_role(self, role_id):
        resp = self.api.get(
            "/api/v1beta0/user/envId/roles/roleId/",
            params=dict(
                envId=self.env_id,
                roleId=role_id
            )
        )
        return resp.box_repr.data

    def test_create_role(self):
        # required param
        builtin_automation = "base"
        os_id = "ubuntu-14-04"
        role_category = "9"
        role_name = "tmp-role-api-test"
        # Create role by api call
        created_role = self.create_role(
            os_id=os_id,
            role_category=role_category,
            role_name=role_name,
            builtin_automation=builtin_automation
        )
        role = self.get_role(created_role.id)
        assert role.name == role_name
```
При внимательном рассмотрении обучающих примеров можно заметить, что все используемые запросы возвращают атрибут
`resp.box_repr`, который является расширением стандартного [requests.Response.json](http://docs.python-requests.org/en/master/api/#requests.Response)
реализованый на безе сторонний библиотеки[python-box](https://github.com/cdgriffith/Box) позволяющей обращаться к словарям с расширенной dot
нотификацией.