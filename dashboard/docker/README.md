## Configuração

### Instalar o Docker seguindo as orientação da página do desenvolvedor.
#Baixar arquivo build_dashboard.zip nesta pasta.
#Descompactar o .zip para uma pasta e executar o comando "docker-compose up -d" dentro da pasta onde está o arquivo docker-compose.yml.
#Acessar no browser o endereço localhost:8066.
#Para subir os logs de execução do tir basta enviar para a api em localhost:3333.

#OBS: Em caso das portas defaults(3333 ou 8066) estiverem em uso, basta alterar o arquivo docker-compose.yml na seção "ports" como no exemplo abaixo:
"8199:8080"
"8198:3333"
