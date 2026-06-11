# Descrição do Pull Request #1995

## Títulos Sugeridos

1. **Fix race condition in user guide closure and update return type**
2. **Implement user guide auto-closure after program access**
3. **Add _close_user_guide method with duplicate prevention**

**Título Escolhido**: Fix race condition in user guide closure and update return type

---

## Contexto

O POUI (Protheus User Interface) exibe um modal de guia de usuário ("user guide popover") na primeira vez que uma rotina é acessada via método `Program()`. Esta funcionalidade é importante para orientar novos usuários, mas precisa ser fechada automaticamente para não bloquear a continuação dos testes.

O objetivo deste PR é implementar um mecanismo robusto de fechamento automático deste modal, evitando race conditions e garantindo que o modal não seja processado múltiplas vezes para a mesma rotina.

---

## O que foi alterado

### 1. Novo atributo de instância: `closed_user_guide_routines`
- **Localização**: Linha 115 em `__init__`
- **Propósito**: Lista que armazena o nome das rotinas para as quais o guia de usuário já foi fechado
- **Tipo**: `list`
- **Justificativa**: Evita tentativas de fechamento repetidas da mesma rotina, já que o modal aparece apenas uma vez

### 2. Novo método interno: `_close_user_guide()`
- **Localização**: Linhas 6095-6138
- **Assinatura**: `def _close_user_guide(self) -> bool:`
- **Propósito**: Gerencia o fechamento do modal de guia de usuário com tratamento de race conditions
- **Retorno**: `bool` → `True` se o modal foi fechado com sucesso ou não estava presente; `False` caso contrário

#### Lógica do método:

1. **Wait inicial (não-bloqueante)**
   - Aguarda até `config.time_out / 3` segundos pela presença do modal (`.po-user-guide-popover`)
   - Se o modal NÃO aparecer: retorna `True` imediatamente (sucesso)
   - Se o modal APARECE: prossegue ao loop de fechamento

2. **Loop de fechamento com retry**
   - Duração: até `config.time_out / 3` segundos
   - A cada iteração:
     - Faz web scrape para localizar o botão de fechar (`.po-user-guide-button-close`)
     - **Guard 1**: Se o botão não foi encontrado → aguarda 5s pela desaparição do modal e tenta novamente
     - **Guard 2**: Se o botão foi encontrado mas não está sendo exibido → aguarda 5s e tenta novamente (solução para race condition)
     - Se o botão existe e está sendo exibido → clica no botão
     - Aguarda 5s pela desaparição do modal
     - Retorna `True` se desapareceu, continua no loop caso contrário

3. **Tratamento de race condition**
   - Verifica explicitamente `element_is_displayed(button_close)` antes de qualquer interação
   - Previne crashes causados por tentativa de click em elementos inválidos

### 3. Integração em `set_program()`
- **Localização**: Linhas 5760-5763
- **Quando é executado**: Após a rotina ser confirmada e o tab abrir com sucesso
- **Lógica**:
  ```python
  if not program_name in self.closed_user_guide_routines:
      closed_user_guide = self._close_user_guide()
      if closed_user_guide:
          self.closed_user_guide_routines.append(program_name)
  ```
- **Comportamento**:
  - Verifica se a rotina já teve seu guia fechado
  - Se não: chama `_close_user_guide()`
  - Se fechado com sucesso: adiciona à lista para evitar chamadas futuras

---

## Impacto no fluxo anterior

✅ **Nenhuma quebra de fluxo anterior**

- O novo comportamento é **transparente** para quem chama `Program()`
- Se o modal não aparecer (cenário comum), a execução continua normalmente sem delay (timeout apenas de `time_out / 3`)
- A chamada é exclusivamente **interna**, não exposta na API pública
- Scripts QA existentes **não são afetados** — não há mudanças na assinatura de métodos públicos

---

## Riscos e Mitigação

### ✅ Race Condition (Crítico) — MITIGADO
**Risco**: Elemento desaparecer entre `web_scrap` e `poui_click`, causando crash.

**Mitigação Implementada**:
- Adicionado guard: `elif not self.element_is_displayed(button_close)`
- Antes de qualquer click, verifica se o elemento ainda está sendo exibido
- Se não está: aguarda 5s e tenta novamente (dentro do loop de retry)

### ✅ Assinatura e Contrato — CORRIGIDO
**Risco**: Docstring incorreta (declarava `-> None` mas retornava `bool`).

**Mitigação Implementada**:
- Assinatura corrigida: `-> bool`
- Docstring atualizada com tipo de retorno correto
- Documentação clara do retorno: "True if the modal was successfully closed or was not present, False otherwise"

### ✅ Duplicação de Chamadas — PREVENIDA
**Risco**: Chamar `_close_user_guide()` múltiplas vezes para a mesma rotina.

**Mitigação Implementada**:
- Lista `self.closed_user_guide_routines` armazena rotinas já processadas
- Check de presença antes de cada chamada
- Uma vez fechado: pula o método nas próximas execuções

---

## Como validar

### Cenário 1: Modal aparece na primeira chamada de `Program()`
```python
# Primeira execução
self.Program("MATA020")  # Modal fecha automaticamente, rotina adicionada à lista

# Segunda execução
self.Program("MATA020")  # Pula `_close_user_guide()`, executa rápido
```

### Cenário 2: Modal não aparece
```python
self.Program("MATA020")  # Aguarda `time_out / 3` s, não encontra modal, retorna sucesso imediatamente
```

### Cenário 3: Modal aparece mas demora para fechar
```python
self.Program("MATA020")  # Loop de retry tenta fechar a cada 5s até `time_out / 3` segundos
```

---

## Checklist de Testes

- [x] Modal não presente: execução não bloqueada (timeout curto de `time_out / 3`)
- [x] Modal presente e fecha na primeira tentativa
- [x] Modal presente mas requer múltiplas tentativas (retry loop)
- [x] Elemento desaparece entre scrape e click (race condition mitigada)
- [x] Mesma rotina chamada 2x: segunda chamada pula `_close_user_guide()`
- [x] Rotinas diferentes: cada uma tenta fechar o modal na primeira chamada
- [x] Integração com `set_program()` transparente e sem efeitos colaterais

---

## Pendências Conhecidas

Nenhuma.

---

## Sumário Técnico

| Aspecto | Status |
|---------|--------|
| **Especificação atendida?** | ✅ Sim |
| **Fluxos anteriores preservados?** | ✅ Sim |
| **Race condition mitigada?** | ✅ Sim |
| **Assinatura/docstring corretas?** | ✅ Sim |
| **Duplicação prevenida?** | ✅ Sim |
| **Testes cobertos?** | ✅ Sim |
| **Regressão esperada?** | ❌ Não |

