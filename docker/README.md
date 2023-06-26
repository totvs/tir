Exemplo de arquivo de configuração do TIR
```json
{
    "Url": "http://10.173.7.146:8091", 
    "Browser": "Firefox",
    "Environment": "P1212210MNTDBEXP",
    "User": "admin",
    "Password": "1234",
    "Language": "pt-br",
    "TimeOut": 120,
    "Headless": true,
    "DebugLog": true,
    "ScreenShot": false
}

Build local:

docker build -t tir . 
#foi criado como tir( mas pode colocar o nome da imagem desejada)

para rodar:
docker run --rm -ti -v ${PWD}:/local -v /etc/passwd:/etc/passwd -v /etc/groups:/etc/groups -e DISPLAY=:0 -u $(id -u):$(id -g) tir:latest python3 /local/ATFA036T
ESTSUITE.py
ou
docker run --rm -ti -v ${PWD}:/local tir:latest python3 /local/ATFA036TESTSUITE.py

Para dashboard:
https://totvs.github.io/tir-docs/dashboard/configurandoTIR/

Instalar o Docker seguindo as orientação da página do desenvolvedor.
Baixar arquivo build_dashboard.zip.
Descompactar o .zip para uma pasta e executar o comando "docker-compose up -d" dentro da pasta onde está o arquivo docker-compose.yml
Acessar no browser o endereço localhost:8066.
Para subir os logs de execução do tir basta enviar para a api em localhost:3333

OBS: Em caso das portas defaults(3333 ou 8066) estiverem em uso, basta alterar o arquivo docker-compose.yml na seção "ports" como no exemplo abaixo
 ports:
    - "8199:8080"
    - "8198:3333"

```

Exemplo de script python do TIR
```python3
#Executar via TESTSUITE sempre (para TIR local)

TESTCASE

# Import from our package the class you're going to use
from tir import Webapp
import unittest

class ATFA036(unittest.TestCase):

    @classmethod
    def setUpClass(inst):
        inst.oHelper = Webapp()
        inst.oHelper.Setup('SIGAATF', '01052016', 'T1', 'D MG 01 ')
        inst.oHelper.Program('ATFA036')

    @classmethod
    def test_ATFA036_CT001(self):

        self.oHelper.WaitShow('Baixa de Ativos')
        self.oHelper.SetKey( key = "F12", wait_show="Parametros", step = 3)
        self.oHelper.SetValue('Visualização ?','Tipos de Ativo')
        self.oHelper.SetButton('OK')
        self.oHelper.SetButton('X')

        self.oHelper.Program("ATFA036")
        self.oHelper.SearchBrowse('D MG 01 1000000002004 01')
        self.oHelper.SetButton("Visualizar")
        self.oHelper.CheckResult('N1_CBASE', '1000000002')
        self.oHelper.CheckResult('N1_ITEM', '004 ')
        self.oHelper.CheckResult('N1_AQUISIC', '01/12/2015')
        self.oHelper.SetButton("Fechar")

        self.oHelper.AssertTrue()

    @classmethod
    def tearDownClass(inst):
        inst.oHelper.TearDown()  

if __name__ == '__main__':
    unittest.main()

TESTSUITE

from ATFA036TESTCASE import ATFA036
import unittest

suite = unittest.TestSuite()
suite.addTest(ATFA036('test_ATFA036_CT001'))

runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
```

Exemplo de execução do TIR com a interface
```bash
docker run --rm -it \
-v ${PWD}:/local \
-v /etc/passwd:/etc/passwd \
-v /etc/groups:/etc/groups \
-v /tmp/.X11-unix/X0:/tmp/.X11-unix/X0 \
-e HOME=/tmp \
-e DISPLAY=:0 \
-u $(id -u):$(id -g) \
tir:latest python3 ./local/script.py

docker run --rm -ti -v ${PWD}:/local -v /etc/passwd:/etc/passwd -v /etc/groups:/etc/groups -e DISPLAY=:0 -u $(id -u):$(id -g) tir:latest python3 /local/ATFA036TESTSUITE.py
ou
docker run --rm -ti -v ${PWD}:/local tir:latest python3 /local/ATFA036TESTSUITE.py


```
