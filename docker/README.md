## Exemplo de arquivo de configuração do TIR
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
```
## Build local
```
docker build -t tir . 
Foi criado como tir, mas pode colocar o nome da imagem desejada.
```

## Exemplo de script python do TIR
```python3
Executar via TESTSUITE localmente 
```

## Exemplo de execução do TIR com a interface
```bash
docker run --rm -ti \
-v ${PWD}:/local \
-v /etc/passwd:/etc/passwd \
-v /etc/groups:/etc/groups \
-e DISPLAY=:0 \
-u $(id -u):$(id -g) \
tir:latest python3 /local/SCRIPTTESTSUITE.py
```
