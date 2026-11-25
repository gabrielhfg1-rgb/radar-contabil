# Radar Contábil

Painel que junta, num lugar só, notícias e projetos de lei importantes para um escritório de contabilidade, separados por área (Fiscal, Pessoal, Societário, Abertura de empresas, Normas contábeis e Câmbio).

- Um **robô** visita as fontes a cada 3 horas, pega título, resumo curto e link, e classifica por área.
- Tudo roda **de graça no GitHub**, sem você deixar o computador ligado.
- O **painel** abre no celular e no computador, e pode ser instalado na tela inicial como um aplicativo.

---

## 1. O que tem em cada pasta

| Arquivo ou pasta | Para que serve | Você mexe? |
|---|---|---|
| `categorias.json` | Áreas e palavras-chave | **Sim** |
| `fontes.json` | Lista de sites e feeds que o robô lê | **Sim** |
| `coletor/` | O robô (programa em Python) | Não precisa |
| `testes/` | Testes automáticos do robô | Não precisa |
| `docs/` | O painel (site/aplicativo) | Não precisa |
| `docs/dados/` | Notícias coletadas, um arquivo por mês | Não (o robô preenche) |
| `.github/workflows/coletar.yml` | O "despertador" que roda o robô a cada 3 horas | Não precisa |

---

## 2. Como colocar no ar (uma vez só, uns 15 minutos)

### 2.1 Criar a conta e o repositório
1. Entre em **https://github.com** e crie uma conta (botão *Sign up*). Se já tem, só faça login.
2. No canto superior direito, clique em **+** → **New repository**.
3. Em *Repository name*, escreva `radar-contabil`.
4. Marque **Public** (o GitHub Pages gratuito exige repositório público; só ficam públicos títulos e links de notícias, nada do seu escritório).
5. **Não** marque nenhuma opção de README, .gitignore ou licença. Clique em **Create repository**.

### 2.2 Enviar os arquivos
Escolha **um** dos caminhos:

**Caminho A — o Claude envia para você (mais fácil).** Conecte o GitHub ao Claude e adicione o repositório `radar-contabil` nas configurações do projeto. Depois é só avisar o Claude, que ele envia tudo.

**Caminho B — pelo site do GitHub.**
1. Na página do repositório recém-criado, clique no link **uploading an existing file**.
2. Arraste **o conteúdo** da pasta `radar-contabil` (não a pasta em si) para a página.
   - No Mac, a pasta `.github` fica escondida. No Finder, aperte `Cmd + Shift + .` para mostrá-la e arraste-a junto.
   - No Windows, ative *Exibir → Itens ocultos* no Explorador de Arquivos.
3. Em *Commit changes*, clique em **Commit changes**.
4. Confira se aparece a pasta `.github` na lista de arquivos. Se não aparecer, o robô não vai rodar sozinho.

### 2.3 Ligar o site (GitHub Pages)
1. No repositório, clique em **Settings** (engrenagem, no topo).
2. No menu da esquerda, clique em **Pages**.
3. Em *Build and deployment → Source*, escolha **GitHub Actions**.

### 2.4 Rodar o robô pela primeira vez
1. Clique na aba **Actions** do repositório. Se aparecer um botão verde pedindo para habilitar os workflows, clique nele.
2. Na esquerda, clique em **Coletar e publicar** → botão **Run workflow** → **Run workflow**.
3. Espere uns 2 a 4 minutos até aparecer o ✓ verde.
4. O endereço do seu painel aparece dentro da execução (etapa *publicar*) e também em **Settings → Pages**. Fica assim:
   `https://SEU-USUARIO.github.io/radar-contabil/`

A partir daí, o robô roda sozinho a cada 3 horas.

### 2.5 Instalar no celular
- **Android (Chrome):** abra o endereço do painel → menu ⋮ → **Instalar app** (ou *Adicionar à tela inicial*).
- **iPhone (Safari):** abra o endereço → botão de compartilhar □↑ → **Adicionar à Tela de Início**.

---

## 3. Como usar o painel

- **Notícias / Leis e projetos:** as duas abas no topo separam as notícias do dia a dia dos projetos de lei da Câmara. Na aba de leis, o período padrão é "Todo o histórico" e a ementa aparece inteira, agrupada pelo mês em que o projeto foi apresentado.
- **Esferas:** acima da lista, escolha de onde vem a informação: Câmara dos Deputados, Senado Federal, STF, Estadual, Municipal ou Portais e Receita. Na aba de leis, os projetos do Senado mostram também a situação atual (ex.: aguardando despacho, transformada em norma jurídica).
- **Setores:** abaixo das áreas, filtre por setor econômico (Agronegócio e Rural, Comércio e Varejo, Indústria, Serviços, Construção, Saúde, Tecnologia, Transporte, Financeiro, Educação, Energia, Terceiro Setor). As palavras de cada setor ficam em `categorias.json`, na lista `"setores"`, e se editam igual às áreas.
- **Áreas:** toque nas etiquetas coloridas no topo. Dá para escolher mais de uma. "Todas" limpa a escolha.
- **Busca:** digite uma palavra (acentos não importam).
- **Botão de filtros (☰):** escolha *Mostrar* (todos, só novos, não lidos, favoritos), *Período* e *Fonte*, e se quer esconder os itens "Outros".
- **NOVO:** marca o que chegou desde a sua última visita.
- **☆ Favorito** e **✓ Lido:** ficam salvos **só no aparelho** em que você marcou (celular e computador têm listas separadas). Abrir uma notícia já a marca como lida.
- **Situação das fontes** (no fim da página): mostra quais fontes funcionaram na última coleta e quais deram erro.

---

## 4. Como adicionar ou mudar palavras-chave (sem programar)

1. No GitHub, abra o arquivo `categorias.json` e clique no **lápis** (✏️ *Edit this file*).
2. Cada área tem uma lista `"palavras"`. Para incluir uma, acrescente uma linha **entre aspas e com vírgula no fim**, por exemplo:
   ```json
   "palavras": [
     "eSocial",
     "FGTS",
     "seguro-desemprego",
     "INSS"
   ]
   ```
   Atenção: a **última** palavra da lista não leva vírgula depois.
3. Clique em **Commit changes** (botão verde).

Regras da comparação:
- Acentos e maiúsculas/minúsculas não importam (`câmbio` = `CAMBIO`).
- Siglas só contam como palavra inteira: `ISS` não confunde com "comissão", `MEI` não confunde com "meio".
- Um item pode cair em várias áreas. O que não cair em nenhuma vai para **Outros**.
- Quando você muda as palavras, o robô **reclassifica também as notícias antigas** na próxima coleta.

Para criar uma área nova, copie um bloco inteiro de área (de `{` até `}`), cole depois do último, coloque vírgula entre eles e troque `id` (sem espaços nem acentos), `nome`, `cor` e `palavras`.

---

## 5. Como adicionar, desligar ou ligar uma fonte

Abra `fontes.json` e clique no lápis. Cada fonte é uma linha assim:

```json
{ "nome": "Jornal Contábil", "tipo": "feed", "url": "https://www.jornalcontabil.com.br/feed/", "ativo": true },
```

- **Adicionar:** copie uma linha, cole abaixo e troque `nome` e `url`. Serve qualquer endereço de **RSS** ou **Atom** (muitos sites têm em `/feed/` ou `/rss/`).
- **Desligar:** troque `"ativo": true` por `"ativo": false`.
- **Fontes muito gerais** (que falam de tudo, como Conjur): acrescente `"somente_com_area": true` e só entram as notícias que caírem em alguma área.
- **Buscas do STF:** o STF tem um feed por palavra pesquisada. Para acompanhar outro assunto, copie uma linha do STF e troque a palavra depois de `?s=` (use `+` no lugar de espaço), por exemplo `https://noticias.stf.jus.br/?s=ITCMD&feed=rss2`.
- **Esfera de cada fonte:** o campo `"esfera"` diz em qual botão a fonte aparece: `camara`, `senado`, `stf`, `estadual`, `municipal` ou `geral`. Ao adicionar uma fonte de uma Assembleia Legislativa ou Câmara de Vereadores, use `estadual` ou `municipal`.
- **Projetos de lei da Câmara e do Senado:** as fontes `"tipo": "camara"` e `"tipo": "senado"` usam as APIs oficiais. Edite a lista `"termos"` para mudar as buscas.
- **Projetos de lei da Câmara:** na fonte `"tipo": "camara"`, a lista `"termos"` diz quais buscas são feitas. Cada termo vira uma busca na API oficial. `"tipos"` escolhe os tipos de proposição (PL, PLP, PEC, MPV, PDL).

Depois de salvar, rode o robô na hora pela aba **Actions → Coletar e publicar → Run workflow** e confira em **Situação das fontes** se a nova fonte funcionou.

---

## 6. Perguntas comuns

**Uma fonte apareceu com erro. E agora?** O robô continua com as outras normalmente. Se o erro persistir por vários dias, o site pode ter mudado o endereço do feed. Desligue a fonte ou troque a URL.

**O robô parou de rodar.** O GitHub pausa agendamentos de repositórios sem nenhuma atividade por 60 dias. Se acontecer, vá em **Actions → Coletar e publicar** e clique em **Enable workflow**.

**O horário da coleta atrasou.** O GitHub às vezes atrasa execuções agendadas em alguns minutos. É normal.

**O histórico some?** Não. Cada mês fica num arquivo em `docs/dados/` e nada é apagado. Itens repetidos (mesmo link) entram uma vez só.

**Estou copiando conteúdo dos sites?** Não. O robô guarda só título, um resumo curto (até 280 caracteres) e o link para o original, se identifica como "RadarContabil" e faz uma pausa entre cada acesso.

---

## 7. Para quem programa (opcional)

```bash
python -m unittest discover -s testes -v   # testes
python coletor/coletar.py                  # coleta manual (grava em docs/dados/)
cd docs && python -m http.server 8000      # ver o painel em http://localhost:8000
```

Só usa a biblioteca padrão do Python (3.10 ou mais novo). Variáveis `RADAR_FONTES` e `RADAR_DADOS` permitem apontar para outro `fontes.json` ou outra pasta de dados.
