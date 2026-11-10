# Manual de Uso por Persona — HDTO

Este guia resume **quem faz o quê e onde** na plataforma dos Homens Batistas do Tocantins. As permissões são definidas por grupo de usuário e pelo vínculo (associação/igreja) do cadastro.

## Acessos gerais

| Recurso | URL |
|---|---|
| Portal público | `/` |
| Login | `/contas/login/` |
| Painel analítico | `/contas/painel/` |
| Administração | `/admin/` |
| Autocadastro de membro | `/cadastro/membro/` |
| Perfil do titular | `/conta/perfil/` |
| Mapa das congregações | `/mapa/` |

Papéis (grupos) existentes:

| Grupo | Persona | Escopo |
|---|---|---|
| `admin_estadual` | Administrador Estadual | Todo o estado do Tocantins |
| `coord_regional` | Coordenador Regional | Sua associação regional |
| `diretor_local` | Diretor/Conselheiro Local | Sua igreja |
| `membro` | Membro / Responsável legal | Apenas seu próprio cadastro |

As contas de acesso **não são criadas pelo público**: o Administrador cria o usuário em `/admin/` (Contas > Usuários), define o grupo e informa a associação e/ou igreja do vínculo.

---

## 1. Visitante (não autenticado)

**Onde:** `/`, `/institucional/<slug>/`, `/noticias/`, `/galerias/`, `/eventos/`, `/mapa/`.

**O que pode fazer**
- Consultar páginas institucionais, notícias e galerias publicadas.
- Ver a agenda de eventos e os detalhes de cada evento.
- Usar o mapa com filtros por tipo de organização, associação e município.
- Realizar o autocadastro censitário em `/cadastro/membro/`.

**O que não pode**
- Acessar painel, cadastros institucionais ou check-in.
- Inscrever-se em eventos (exige login).

---

## 2. Membro / Responsável legal

**Onde:** `/contas/login/`, `/cadastro/membro/`, `/conta/perfil/`, `/eventos/<id>/inscrever/`, `/conta/revogar-consentimento/`.

**O que pode fazer**
1. Fazer o autocadastro censitário, aceitando o termo de consentimento vigente.
2. Vincular-se a uma ou mais organizações **ativas** de igrejas homologadas.
3. Menores de 18 anos: informar os dados do responsável legal (nome, CPF e parentesco).
4. Acompanhar o perfil, consentimentos registrados e inscrições em `/conta/perfil/`.
5. Inscrever-se em eventos abertos e obter a credencial com QR Code.
6. Revogar o consentimento: os dados pessoais são anonimizados e a conta é inativada.

**Atenção**
- O CPF é único: não é possível manter dois cadastros com o mesmo CPF.
- Sem termo de consentimento vigente ou sem organização ativa, o cadastro não é ativado.
- A revogação é definitiva para os dados pessoais (LGPD); o histórico legal é preservado.

---

## 3. Diretor / Conselheiro Local

**Onde:** `/contas/painel/`, `/cadastros/igrejas/nova/`, `/cadastros/organizacoes/nova/`, `/cadastro/membro/`, QR de check-in dos eventos.

**O que pode fazer**
- Ativar as organizações locais **HD**, **ERV** e **Embaixadores do Rei** para a sua igreja, uma de cada tipo.
- Cadastrar igrejas/congregações (o registro entra como **pendente** de homologação).
- Acompanhar o painel analítico restrito à sua igreja.
- Orientar e realizar o cadastro censitário de membros vinculados às organizações da sua igreja.
- Realizar o check-in de inscrições de eventos pelo QR Code.

**Restrições**
- Só enxerga a própria igreja e seus vínculos.
- Organizações só podem ser ativadas em **igreja homologada**.
- Não homologa igrejas, não publica conteúdo e não acessa dados de outras igrejas.

---

## 4. Coordenador Regional

**Onde:** mesmos recursos do Diretor Local, porém com escopo na associação.

**O que pode fazer**
- Acompanhar igrejas, organizações e indicadores agregados da sua associação no painel analítico.
- Cadastrar igrejas e ativar organizações nas igrejas homologadas da associação.
- Acompanhar o engajamento censitário da região.
- Realizar check-in de inscrições de eventos.

**Restrições**
- Vê apenas a associação à qual está vinculado.
- Não homologa igrejas nem publica conteúdo.
- Indicadores respeitam o k-anonimato: grupos pequenos não são exibidos.

---

## 5. Administrador Estadual

**Onde:** `/admin/` (requer acesso de equipe) e `/contas/painel/`.

**O que pode fazer**
1. **Homologar igrejas:** Admin > Igrejas > selecionar > ação "Homologar igrejas selecionadas". Só igrejas homologadas recebem organizações e aparecem no mapa.
2. Gerir associações regionais, igrejas, organizações e municípios.
3. Criar usuários, definir grupos e vincular associação/igreja.
4. Manter o **termo de consentimento vigente** (Members > Versões do termo).
5. Publicar notícias, galerias, páginas institucionais e documentos.
6. Criar e moderar eventos e acompanhar inscrições/check-ins.
7. Consultar o painel analítico de todo o estado e auditar consentimentos e revogações.
8. Importar a malha municipal do IBGE com `importar_municipios_to`.

**Atenção**
- O grupo `admin_estadual` libera painel e cadastros institucionais; para homologar e publicar é necessário também ter acesso ao `/admin/` (`is_staff`/superusuário).
- Consentimentos e revogações são imutáveis (append-only), inclusive no banco.

---

## Matriz rápida de permissões

| Ação | Visitante | Membro | Diretor | Coordenador | Admin |
|---|---|---|---|---|---|
| Ver portal, notícias e mapa | Sim | Sim | Sim | Sim | Sim |
| Autocadastro censitário | Sim | Sim | Sim | Sim | Sim |
| Perfil, inscrições e QR Code | — | Sim | — | — | — |
| Revogar consentimento | — | Sim | — | — | — |
| Painel analítico | — | — | Sim | Sim | Sim |
| Cadastrar igreja | — | — | Sim | Sim | Sim |
| Ativar organização (HD/ERV/ER) | — | — | Sim | Sim | Sim |
| Check-in por QR Code | — | — | Sim | Sim | Sim |
| Homologar igreja | — | — | — | — | Sim |
| Publicar conteúdo e eventos | — | — | — | — | Sim |
| Gerir usuários e grupos | — | — | — | — | Sim |

---

## Boas práticas

- Confirme sempre o **vínculo** (associação/igreja) do usuário antes de liberar um grupo.
- O cadastro de menor de idade exige responsável legal; o consentimento deve ser do responsável.
- O painel exibe apenas agregados com supressão de grupos menores que `CENSO_K_ANONIMATO`.
- Nunca compartilhe credenciais; a revogação de consentimento inativa a conta do titular.
- Dúvidas operacionais de deploy e backup: consulte `docs/RUNBOOK.md`.
