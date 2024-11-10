
# SYRIN Webhook

Este projeto é uma API Webhook baseada em Flask que integra com RabbitMQ para processar e enviar notificações baseadas em texto para uma fila de mensagens. A API recebe uma entrada de texto via requisições HTTP POST e, em seguida, envia o texto para uma fila RabbitMQ, que pode ser processada posteriormente.

## Demo

![Application Demo](./driagrams/Syrin-Webhook.gif)

## Funcionalidades

- **Processamento de Texto para Fila**: A API aceita um payload JSON com texto ou dados de mensagem, em seguida, envia para uma fila RabbitMQ para processamento adicional.
- **Declaração de Filas**: No início, as filas necessárias do RabbitMQ são declaradas para garantir que existam antes do processamento.
- **Processamento Assíncrono**: O processamento de mensagens de texto é tratado em uma thread separada para garantir operações não bloqueantes para a API.
- **Configuração Baseada em Variáveis de Ambiente**: Credenciais e detalhes de conexão do RabbitMQ são carregados a partir de variáveis de ambiente.

## Como Funciona

### Endpoints

- **POST /api/text-to-speech**

  Este endpoint processa requisições contendo dados de texto ou mensagens e envia os dados para uma fila RabbitMQ. Dependendo do tipo de entrada, a mensagem é roteada para a fila `00_syrin_notification_warning` ou `00_syrin_notification_error`.

#### Exemplo de Requisição

```bash
curl -X POST http://localhost:5121/api/text-to-speech \
    -H "Content-Type: application/json" \
    -d '{"text": "Esta é uma mensagem de aviso."}'
```

#### Exemplo de Resposta

```json
{
  "message": "Requisição recebida do campo 'text', processamento em andamento."
}
```

### Filas RabbitMQ

- `00_syrin_notification_warning`: Fila para mensagens marcadas com nível de "aviso".
- `00_syrin_notification_error`: Fila para mensagens marcadas com nível de "erro".

### Variáveis de Ambiente

Os detalhes de conexão do RabbitMQ são configurados através das seguintes variáveis de ambiente:

- `RABBITMQ_HOST`: O nome do host ou IP do servidor RabbitMQ.
- `RABBITMQ_PORT`: A porta em que o RabbitMQ está ouvindo (padrão: 5672).
- `RABBITMQ_VHOST`: O virtual host utilizado no RabbitMQ.
- `RABBITMQ_USER`: O nome de usuário do RabbitMQ.
- `RABBITMQ_PASS`: A senha do RabbitMQ.

### Fluxo de Trabalho

1. **Declaração de Fila**: Quando o aplicativo Flask é iniciado, ele declara as filas necessárias (`00_syrin_notification_warning` e `00_syrin_notification_error`) para garantir que estejam disponíveis para publicação de mensagens.
2. **Manipulação de Mensagens**: Uma requisição POST é feita para o endpoint `/api/text-to-speech` com dados JSON contendo um campo `text` ou `msg`. Com base no campo e no conteúdo, a mensagem é roteada para a fila apropriada no RabbitMQ.
3. **Processamento Assíncrono**: A mensagem é enviada ao RabbitMQ em uma thread separada, garantindo que a API responda imediatamente e o texto seja processado em segundo plano.
4. **Publicação na Fila**: A mensagem é publicada no RabbitMQ com persistência habilitada (modo de entrega 2), garantindo que a mensagem não seja perdida caso o RabbitMQ reinicie.

## Executando a Aplicação

Para executar a aplicação, siga estas etapas:

1. **Configure o RabbitMQ**: Certifique-se de que você tenha o RabbitMQ instalado e em execução. Você pode usar um container Docker para o RabbitMQ:

    ```bash
    docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
    ```

2. **Clone o repositório** e navegue até o diretório do projeto:

    ```bash
    git clone https://github.com/syrin-alert/syrin-webhook
    cd syrin-webhook
    ```

3. **Instale as dependências**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Execute a API Flask**:

    ```bash
    python app.py
    ```

5. **Envie requisições**: Use ferramentas como `curl` ou Postman para enviar uma requisição POST ao endpoint `/api/text-to-speech`.

## Suporte ao Docker

Você também pode compilar e executar a aplicação usando Docker. Para isso:

1. **Compile a imagem Docker**:

    ```bash
    docker build -t ghcr.io/syrin-alert/syrin-webhook:1.0.1 .
    ```

2. **Execute o container Docker**:

    ```bash
    docker run -d -p 5121:5121 --env-file .env ghcr.io/syrin-alert/syrin-webhook:1.0.1
    ```

## Tecnologias Utilizadas

- **Flask**: Framework web para criar a API Webhook.
- **RabbitMQ**: Broker de mensagens utilizado para enfileirar e processar mensagens de texto.
- **Pika**: Biblioteca Python para interagir com o RabbitMQ.
- **Threading**: Para gerenciar o envio de mensagens de forma assíncrona.

## Licença

Este projeto é licenciado sob a licença MIT.
