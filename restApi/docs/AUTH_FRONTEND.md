# Integração do front-end: login, JWT e CSRF

## Visão geral

A API autentica o usuário por cookies, não por token no `localStorage`,
`sessionStorage` ou no cabeçalho `Authorization`.

Após o login, a API grava dois cookies `HttpOnly`:

- `access_token`: JWT de acesso, com validade de **15 minutos**;
- `refresh_token`: JWT de renovação, com validade de **7 dias**. A cada
  renovação o refresh token é rotacionado.

Como os cookies são `HttpOnly`, o JavaScript não consegue (e não deve) ler os
JWTs. O navegador os envia automaticamente quando a chamada usa credenciais.
O cookie `csrftoken`, por outro lado, pode ser lido pelo JavaScript e deve ser
enviado no cabeçalho `X-CSRFToken` em requisições que alteram dados.

> Todos os caminhos abaixo incluem o prefixo `/api/`. Exemplo local:
> `http://localhost:8000/api`.

## Configuração necessária

Use sempre `credentials: 'include'` no `fetch` (ou `withCredentials: true` no
Axios). Sem isso, o navegador não aceitará/enviará os cookies da API em uma
chamada cross-origin.

Em desenvolvimento, não misture hosts: se o front estiver em
`http://localhost:3000`, acesse a API por `http://localhost:8000`, e não por
`127.0.0.1`. Os hosts do front também precisam estar configurados no back-end
em `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS`.

## Fluxo de inicialização e login

1. Ao abrir a aplicação (antes de qualquer `POST`, `PUT`, `PATCH` ou `DELETE`),
   faça `GET /api/csrf/`. A resposta configura/renova o cookie `csrftoken`.
2. Faça o login em `POST /api/token/` com as credenciais e envie o cabeçalho
   `X-CSRFToken`, usando o valor obtido no passo anterior.
3. Em caso de sucesso (`200`), os cookies `access_token` e `refresh_token` são
   recebidos por `Set-Cookie`. A resposta não contém os JWTs no JSON.
4. Busque o estado inicial do usuário em `GET /api/advogado/current-user/`.
   Se retornar `200`, considere a sessão autenticada.

Exemplo com `fetch`:

```ts
const API_URL = process.env.NEXT_PUBLIC_API_URL!; // ex.: http://localhost:8000/api

export async function initializeCsrf() {
  await fetch(`${API_URL}/csrf/`, { credentials: 'include' });
}

export async function login(email: string, password: string) {
  await initializeCsrf();
  const csrf = getCookie('csrftoken');

  const response = await fetch(`${API_URL}/token/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(csrf ? { 'X-CSRFToken': csrf } : {}),
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) throw new Error('Usuário ou senha inválidos.');
  return fetch(`${API_URL}/advogado/current-user/`, {
    credentials: 'include',
  }).then((r) => r.json());
}
```

O campo de identificação do login é `email`, pois o modelo usa o e-mail como
`USERNAME_FIELD`. Portanto, envie `{ email, password }`.

## Como enviar CSRF nas requisições autenticadas

Para `GET`, `HEAD` e `OPTIONS`, envie apenas as credenciais. Para qualquer
requisição de escrita (`POST`, `PUT`, `PATCH` ou `DELETE`) autenticada:

1. leia o cookie `csrftoken`;
2. envie seu valor em `X-CSRFToken`;
3. mantenha `credentials: 'include'` para enviar os cookies JWT e CSRF.

Não envie `Authorization: Bearer ...`: a API ignora esse fluxo e lê
`access_token` do cookie.

```ts
function getCookie(name: string) {
  const item = document.cookie
    .split('; ')
    .find((cookie) => cookie.startsWith(`${name}=`));
  return item ? decodeURIComponent(item.split('=').slice(1).join('=')) : null;
}

export async function apiFetch(path: string, init: RequestInit = {}) {
  const method = (init.method ?? 'GET').toUpperCase();
  const headers = new Headers(init.headers);

  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    let csrf = getCookie('csrftoken');
    if (!csrf) {
      await initializeCsrf();
      csrf = getCookie('csrftoken');
    }
    if (csrf) headers.set('X-CSRFToken', csrf);
  }

  return fetch(`${API_URL}${path}`, {
    ...init,
    method,
    headers,
    credentials: 'include',
  });
}

// Exemplo: criação de cliente
await apiFetch('/clientes/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(dadosDoCliente),
});
```

## Renovação da sessão

Quando uma chamada autenticada retornar `401`, tente uma única renovação:

`POST /api/token/refresh/` com `credentials: 'include'` e `X-CSRFToken`. Não
envie o refresh token no corpo: ele é lido pelo back-end do cookie
`refresh_token`. Em caso de sucesso, a API troca os cookies e a chamada
original pode ser repetida uma vez.
Se a renovação também retornar `401`, descarte o estado local do usuário e
direcione para o login.

```ts
async function refreshSession() {
  const csrf = getCookie('csrftoken');
  const response = await fetch(`${API_URL}/token/refresh/`, {
    method: 'POST',
    credentials: 'include',
    headers: csrf ? { 'X-CSRFToken': csrf } : {},
  });
  return response.ok;
}
```

Evite criar vários refreshes simultâneos: centralize a renovação em um único
interceptor/fila. Assim, quando várias chamadas receberem `401`, todas aguardam
a mesma renovação e só uma delas chama o endpoint.

## Logout

Para encerrar a sessão, chame `POST /api/advogado/logout/` com
`credentials: 'include'` e `X-CSRFToken`. A API invalida o refresh token quando possível,
marca o usuário offline e remove os dois cookies. Depois disso, limpe somente
o estado de interface/cache do front-end; não há JWT local para apagar.

```ts
await apiFetch('/advogado/logout/', { method: 'POST' });
// limpar store/cache e redirecionar para /login
```

## Diagnóstico rápido

| Sintoma | Verificar |
| --- | --- |
| Cookies não aparecem ou não seguem para a API | `credentials: 'include'`, origem CORS permitida e uso consistente de `localhost`/`127.0.0.1`. |
| `403 CSRF Failed` | Primeiro execute `GET /api/csrf/` e envie o cookie `csrftoken` como `X-CSRFToken` em operações de escrita. |
| `401` após algum tempo | Faça uma renovação em `/api/token/refresh/` e repita a chamada uma vez. |
| `401` na renovação | A sessão expirou ou foi revogada; solicite novo login. |

## Produção

Com front e API em sites diferentes, a API deve usar HTTPS e configurar
`JWT_COOKIE_SECURE=true`, `CSRF_COOKIE_SECURE=true` e, quando for realmente
cross-site, `JWT_COOKIE_SAMESITE=None` e `CSRF_COOKIE_SAMESITE=None`. Os
domínios públicos exatos devem constar em `CORS_ALLOWED_ORIGINS` e
`CSRF_TRUSTED_ORIGINS`; não use curingas com credenciais.
