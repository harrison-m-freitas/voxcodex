Atue como um grupo de especialistas composto por:

- arquiteto de software sênior;
- arquiteto de sistemas distribuídos;
- engenheiro de IA/LLMs;
- especialista em NLP e compreensão de documentos;
- especialista em OCR e document intelligence;
- engenheiro de processamento de áudio e Text-to-Speech;
- especialista em literatura, linguística e análise textual;
- especialista em UX para leitura e audiobooks;
- engenheiro de dados;
- especialista em FinOps e estimativa de custos;
- especialista em infraestrutura e observabilidade;
- product manager técnico.

Sua tarefa é me ajudar a projetar, do zero, uma plataforma modular para transformar livros e documentos em audiobooks inteligentes, de alta qualidade.

Não quero apenas uma aplicação de Text-to-Speech.

Quero projetar um pipeline capaz de compreender estruturalmente e semanticamente uma obra, adaptar sua representação para o meio auditivo sem alterar indevidamente seu conteúdo e produzir uma experiência de audiobook apropriada ao tipo de obra.

## 1. Objetivo central

O sistema deve receber livros ou documentos em diferentes formatos e idiomas, processá-los, compreender sua estrutura e seu conteúdo e gerar um audiobook enriquecido e de alta qualidade.

Formatos de entrada podem incluir, entre outros:

- EPUB;
- PDF com texto;
- PDF escaneado;
- Markdown;
- TXT;
- HTML;
- DOCX;
- imagens individuais de páginas;
- PNG;
- JPEG;
- outros formatos relevantes.

O sistema deverá inicialmente ser destinado a uso privado, portanto não existem neste momento restrições rígidas quanto a stack tecnológica, provedores, infraestrutura ou custo.

Ainda assim, quero que a arquitetura seja concebida de maneira modular para permitir evolução futura.

---

# 2. Princípio fundamental

O sistema deve distinguir claramente três representações de uma obra:

### A. Fonte original

Representação fiel do documento recebido.

Nunca deverá ser sobrescrita.

### B. Representação semântica estruturada

Uma representação intermediária contendo:

- capítulos;
- seções;
- parágrafos;
- diálogos;
- personagens;
- narrador;
- citações;
- notas;
- referências;
- tabelas;
- figuras;
- fórmulas;
- listas;
- cabeçalhos;
- rodapés;
- elementos editoriais;
- estrutura lógica;
- relações entre partes do texto;
- informações de contexto relevantes.

### C. Roteiro narrável

Versão preparada especificamente para produção de áudio.

Ela poderá adaptar elementos incompatíveis com áudio, mas deverá preservar rigorosamente:

- significado;
- argumento;
- conteúdo factual;
- intenção do autor;
- distinção entre texto original e explicações adicionadas pelo sistema.

Nunca misture silenciosamente conteúdo gerado pelo sistema com conteúdo original.

Toda intervenção deve possuir proveniência.

---

# 3. Capacidades desejadas

O sistema deverá ser projetado para possuir, progressivamente, as seguintes capacidades.

## 3.1 Ingestão de documentos

Receber livros completos ou progressivamente.

Por exemplo:

- upload de EPUB;
- upload de PDF;
- upload de conjunto de imagens;
- captura página por página;
- importação incremental;
- processamento somente após o livro estar completo;
- possibilidade de processar parcialmente determinados capítulos.

Para imagens de páginas:

1. armazenar o arquivo original;
2. identificar ordem das páginas;
3. detectar duplicatas;
4. detectar páginas ausentes;
5. verificar rotação;
6. corrigir perspectiva quando necessário;
7. avaliar qualidade;
8. realizar OCR;
9. reconstruir estrutura textual.

---

# 4. Extração de conteúdo

Determine uma estratégia para diferentes tipos de entrada.

Exemplos:

### EPUB

Extrair diretamente:

- conteúdo;
- capítulos;
- metadata;
- imagens;
- notas;
- hierarquia.

### PDF digital

Avaliar:

- extração direta de texto;
- reconstrução de layout;
- utilização de document intelligence;
- conversão intermediária para HTML/EPUB/Markdown, quando fizer sentido.

### PDF escaneado

Pipeline potencial:

imagem → preprocessing → layout detection → OCR → reconstrução de estrutura → validação.

Não assuma que OCR simples seja suficiente.

Considere:

- múltiplas colunas;
- notas de rodapé;
- páginas espelhadas;
- números de página;
- cabeçalhos recorrentes;
- hifenização;
- caracteres especiais;
- alfabetos diferentes;
- fórmulas;
- tabelas;
- citações;
- versos;
- peças teatrais;
- diagramas.

---

# 5. Compreensão da obra

Antes de produzir áudio, o sistema deverá construir uma compreensão global do livro.

Avalie técnicas para identificar:

- idioma;
- possível tradução;
- título;
- autor;
- gênero;
- subgênero;
- época;
- estrutura;
- estilo;
- nível técnico;
- personagens;
- narrador;
- interlocutores;
- mudança de perspectiva;
- citações;
- diálogos;
- exemplos;
- explicações;
- argumentos;
- definições;
- conceitos;
- referências internas.

O sistema deverá ser capaz de manter contexto entre capítulos.

Considere a necessidade de uma representação de memória hierárquica da obra:

livro → parte → capítulo → seção → bloco → sentença.

---

# 6. Classificação do tipo de livro

Não existe uma única estratégia de narração adequada para todos os livros.

O sistema deverá identificar o tipo de obra e selecionar um perfil de processamento.

Considere explicitamente exemplos muito diferentes como:

- Jean Racine — Fedra;
- Justo Lípsio — Sobre a Constância;
- Daniel Defoe — Moll Flanders;
- Manoel García Morente — Lições Preliminares de Filosofia;
- Erwin Schrödinger — O que é a Vida?;
- Roger Penrose — The Road to Reality.

Avalie pelo menos categorias como:

- romance;
- autobiografia;
- teatro;
- poesia;
- filosofia;
- ensaio;
- divulgação científica;
- livro-texto;
- matemática;
- física;
- história;
- documento técnico.

Para cada categoria, determine:

- estratégia de segmentação;
- quantidade potencial de vozes;
- intensidade emocional;
- tratamento de citações;
- tratamento de fórmulas;
- explicações auxiliares;
- resumos;
- ritmo;
- pausas;
- entonação;
- necessidade de descrição de material visual.

---

# 7. Identificação de quem está falando

O sistema deverá identificar, sempre que possível:

- narrador;
- personagem;
- interlocutor;
- autor citado;
- texto citado;
- voz editorial;
- notas.

Construa um modelo de atribuição de fala.

A decisão sobre uma voz não deverá ser baseada somente no nome do personagem.

Considere também:

- gênero ou características vocais quando inferíveis com segurança;
- idade aproximada quando relevante e justificável;
- papel narrativo;
- personalidade;
- contexto;
- continuidade entre capítulos;
- emoção da cena.

Não invente características que o texto não suporta.

Crie níveis de confiança para inferências.

---

# 8. Elenco de vozes

Projete um sistema capaz de usar múltiplas vozes.

Por exemplo:

- narrador principal;
- personagens recorrentes;
- personagens secundários;
- citações;
- voz para comentários auxiliares;
- voz para notas do sistema.

O sistema deverá manter consistência durante toda a obra.

Proponha um mecanismo como:

Voice Registry / Character Voice Registry

contendo:

- personagem;
- identidade;
- voz atribuída;
- parâmetros;
- estilo;
- histórico;
- confiança;
- primeira ocorrência;
- aliases.

Determine também uma estratégia para evitar que uma obra com centenas de personagens exija centenas de vozes únicas.

---

# 9. Prosódia, interpretação e emoção

O sistema deverá gerar áudio que leve em conta:

- contexto;
- emoção;
- ritmo;
- tensão;
- ironia;
- pergunta;
- surpresa;
- hesitação;
- dramaticidade;
- serenidade;
- conteúdo científico;
- exposição filosófica;
- diálogo.

Entretanto, emoção nunca deve transformar a narração em caricatura quando isso for incompatível com a obra.

Projete uma camada intermediária de direção de voz, contendo atributos como:

- speaker;
- emotion;
- intensity;
- pace;
- pause;
- emphasis;
- pronunciation;
- tone.

Avalie se essa camada deverá utilizar:

- SSML;
- JSON estruturado;
- DSL própria;
- combinação dessas opções.

---

# 10. Preparação do texto para áudio

O sistema deverá conseguir produzir uma versão narrável do texto sem indevidamente reescrever a obra.

Identifique situações nas quais uma adaptação é necessária.

Exemplos:

- tabelas;
- diagramas;
- referências visuais;
- notas;
- abreviações;
- símbolos;
- fórmulas;
- elementos tipográficos;
- listas;
- cabeçalhos;
- figuras;
- referências como “veja a tabela abaixo”.

Toda transformação deverá poder ser auditada.

Projete mecanismos para armazenar:

original → transformação → justificativa → modelo/processo responsável.

---

# 11. Imagens e figuras

O sistema deverá interpretar imagens relevantes.

Para cada imagem, deve decidir entre:

- ignorar;
- mencionar brevemente;
- descrever;
- explicar;
- produzir descrição detalhada.

A estratégia deverá depender do valor da imagem para compreender o texto.

Por exemplo:

uma ilustração meramente decorativa não merece uma explicação de vários minutos.

Um diagrama essencial de física pode exigir explicação extensa.

---

# 12. Tabelas

O sistema não deve simplesmente ler mecanicamente dezenas ou centenas de células.

Deverá determinar:

- objetivo da tabela;
- dimensões;
- principais tendências;
- dados relevantes;
- exceções;
- relação com o texto.

Crie diferentes modos:

1. descrição resumida;
2. descrição interpretativa;
3. leitura seletiva;
4. leitura integral solicitada.

Preserve acesso aos dados originais.

---

# 13. Fórmulas e matemática

Para obras matemáticas e científicas, determine uma estratégia de narração de:

- equações;
- símbolos;
- expressões;
- matrizes;
- derivadas;
- integrais;
- índices;
- expoentes;
- letras gregas.

Considere que ler uma fórmula símbolo por símbolo nem sempre produz compreensão.

Projete diferentes representações:

- fórmula original;
- versão falável;
- explicação intuitiva opcional.

Nunca substitua a fórmula original pela explicação.

---

# 14. Explicações auxiliares

O sistema deverá identificar trechos potencialmente difíceis.

Exemplos:

- conceitos filosóficos;
- argumentos densos;
- matemática;
- referências históricas;
- vocabulário arcaico;
- passagens ambíguas;
- conceitos científicos.

Quando apropriado, deverá ser capaz de gerar uma explicação auxiliar.

Porém:

A explicação nunca poderá ser confundida com texto do autor.

Projete uma forma auditiva de comunicar claramente algo semelhante a:

“Nota explicativa”

ou outro mecanismo menos intrusivo.

Avalie também níveis configuráveis:

- nenhuma explicação;
- mínima;
- moderada;
- didática;
- aprofundada.

---

# 15. Resumos e revisão

Depois de unidades relevantes como:

- seção;
- capítulo;
- parte;

o sistema poderá gerar:

- síntese;
- pontos principais;
- conceitos;
- argumentos;
- revisão;
- questões para reflexão.

Novamente, isso deverá ser claramente separado da obra original.

Projete um modo em que o usuário possa escolher:

- audiobook fiel;
- audiobook enriquecido;
- audiobook estudo.

---

# 16. Tradução

A aplicação poderá receber livros em qualquer idioma.

Analise arquiteturas que permitam:

A. narrar no idioma original;

B. traduzir e narrar;

C. manter texto original e produzir tradução sincronizada;

D. gerar explicações em outro idioma.

A tradução deve preservar estrutura e proveniência.

---

# 17. Pronúncia

Projete mecanismos para:

- nomes próprios;
- palavras estrangeiras;
- latim;
- grego;
- termos técnicos;
- símbolos;
- nomes históricos;
- abreviações.

Considere um Pronunciation Dictionary por obra e um dicionário global.

---

# 18. Pipeline

Quero que você determine se o processamento deveria ser organizado aproximadamente como:

Ingestão
↓
Normalização
↓
Document parsing
↓
OCR / Document Intelligence
↓
Reconstrução estrutural
↓
Validação
↓
Representação canônica
↓
Análise global da obra
↓
Classificação
↓
Segmentação
↓
Análise semântica
↓
Speaker attribution
↓
Tratamento de imagens/tabelas/fórmulas
↓
Detecção de trechos difíceis
↓
Geração de conteúdo auxiliar
↓
Adaptação para narração
↓
Direção de voz/prosódia
↓
TTS
↓
Pós-processamento de áudio
↓
Controle de qualidade
↓
Composição do audiobook
↓
Exportação

Não aceite essa arquitetura automaticamente.

Critique-a e proponha uma melhor caso necessário.

---

# 19. Arquitetura modular

Avalie se é melhor construir:

- aplicação monolítica modular;
- arquitetura orientada a eventos;
- conjunto de serviços independentes;
- workers especializados;
- workflow engine;
- combinação dessas abordagens.

Quero evitar microserviços desnecessários no início.

Entretanto, algumas tarefas podem exigir processamento independente e escalável.

Identifique claramente:

- módulos;
- responsabilidades;
- contratos;
- entradas;
- saídas;
- dependências.

---

# 20. Jobs e workflows

O processamento de uma obra poderá levar bastante tempo.

Portanto, projete um sistema de jobs contendo:

- estado;
- progresso;
- retry;
- timeout;
- checkpoints;
- cancelamento;
- reprocessamento;
- idempotência;
- tratamento de falhas;
- dependências;
- processamento paralelo.

Avalie ferramentas/workflow engines adequados.

---

# 21. Human-in-the-loop

O sistema não deve necessariamente automatizar tudo cegamente.

Identifique pontos em que revisão humana pode trazer grande melhoria.

Por exemplo:

- correção de OCR;
- seleção de vozes;
- identificação de personagens;
- validação de pronunciamentos;
- revisão de fórmulas;
- escolha entre versões de interpretação;
- revisão da versão narrável.

Projete a arquitetura para permitir automação elevada sem remover capacidade de intervenção.

---

# 22. Controle de qualidade

Defina mecanismos para identificar:

- texto perdido;
- duplicações;
- alucinações;
- OCR incorreto;
- mudança de significado;
- speaker incorreto;
- problemas de pronúncia;
- cortes no áudio;
- inconsistência de volume;
- erros de segmentação;
- conteúdo inventado;
- resumo incorreto.

Toda etapa de IA generativa deverá possuir alguma estratégia de validação.

---

# 23. Proveniência

Esse requisito é fundamental.

O sistema deverá ser capaz de responder:

- de qual página veio este trecho?
- de qual bloco?
- qual era o texto original?
- houve OCR?
- qual modelo fez determinada transformação?
- qual prompt foi usado?
- qual versão do modelo?
- qual foi a resposta?
- qual texto foi enviado para TTS?
- qual voz?
- quais parâmetros?
- qual arquivo de áudio foi produzido?

Projete uma estratégia completa de lineage/provenance.

---

# 24. Versionamento

Considere que:

- OCR pode ser refeito;
- prompts podem mudar;
- modelos podem mudar;
- tradução pode ser reprocessada;
- TTS pode ser regenerado;
- voz pode mudar;
- algoritmo de segmentação pode mudar.

O sistema deverá permitir reproduzir e comparar versões.

---

# 25. Estimativa de custo ANTES da execução

Esse é um requisito central.

Antes de executar operações caras, o sistema deverá gerar uma estimativa detalhada.

Exemplo:

Livro X

Ingestão:
R$ / US$ ...

OCR:
...

Document Intelligence:
...

Extração e normalização:
...

LLM — compreensão:
...

LLM — enriquecimento:
...

Descrição de imagens:
...

Tradução:
...

Text-to-Speech:
...

Armazenamento:
...

Processamento computacional:
...

Total estimado:
...

Intervalo provável:
...

Quero uma arquitetura capaz de calcular custos antes da execução.

Considere:

- páginas;
- imagens;
- quantidade estimada de tokens;
- caracteres;
- duração estimada do áudio;
- modelos escolhidos;
- fornecedores;
- chamadas adicionais;
- retries;
- armazenamento;
- compute.

O sistema deve poder comparar alternativas.

Por exemplo:

Plano Econômico
US$ X

Plano Equilibrado
US$ Y

Plano Máxima Qualidade
US$ Z

E mostrar quais componentes mudam entre os planos.

---

# 26. Registro do custo real

Depois da execução, armazenar:

estimativa vs. custo real.

Isso deverá alimentar um modelo cada vez melhor de previsão de custos.

---

# 27. Arquitetura multi-provider

Evite acoplamento desnecessário a um único fornecedor.

Analise abstrações para:

- LLM;
- OCR;
- Document AI;
- embeddings;
- armazenamento;
- TTS;
- tradução.

Considere possibilidade de usar diferentes modelos para tarefas diferentes.

Não presuma que o modelo mais poderoso deve executar todas as etapas.

---

# 28. Persistência

Determine quais tipos de armazenamento são apropriados para:

- arquivos originais;
- páginas;
- texto;
- estrutura documental;
- metadata;
- embeddings;
- jobs;
- chunks;
- entidades;
- personagens;
- vozes;
- prompts;
- respostas de IA;
- versões;
- áudio intermediário;
- audiobook final;
- custos;
- logs;
- provenance.

Avalie, quando apropriado:

- object storage;
- banco relacional;
- document store;
- vector database;
- cache.

Evite introduzir tecnologias sem necessidade concreta.

---

# 29. Modelo canônico

Avalie criar um formato interno independente da entrada, algo como:

Canonical Book Model.

Por exemplo:

Book
Part
Chapter
Section
Block
Paragraph
Sentence
Dialogue
Speaker
Character
Quote
Footnote
Table
Figure
Formula
Reference
NarrationInstruction
Explanation
Summary
AudioSegment

Analise e refine essa ideia.

Esse modelo poderá ser uma das peças centrais da arquitetura.

---

# 30. Interface

Inicialmente imagino uma interface capaz de mostrar:

Biblioteca
↓
Livro
↓
Arquivo / páginas
↓
Status de ingestão
↓
Estrutura detectada
↓
Qualidade da extração
↓
Personagens
↓
Vozes
↓
Configuração do processamento
↓
Estimativa de custo
↓
Executar
↓
Pipeline em andamento
↓
Revisão
↓
Audiobook

Projete uma UX adequada.

---

# 31. Observabilidade

Quero rastrear:

- tempo por etapa;
- custo;
- tokens;
- chamadas;
- erros;
- retries;
- qualidade;
- provedor;
- modelo;
- versão;
- páginas;
- duração produzida.

Projete observabilidade técnica e observabilidade de negócio.

---

# 32. Segurança

Apesar de inicialmente ser uma aplicação privada, considere:

- autenticação;
- autorização;
- isolamento;
- criptografia;
- secrets;
- backups;
- arquivos potencialmente sensíveis;
- logs;
- retenção;
- APIs externas.

---

# 33. Estratégia de implementação

Não quero construir tudo de uma vez.

Ajude-me a identificar:

### Proof of Concept

A menor implementação capaz de provar que a ideia funciona.

### MVP

Sistema já utilizável para livros reais.

### V1

Pipeline confiável e modular.

### V2+

Recursos avançados.

Para cada fase, defina claramente:

- funcionalidades;
- arquitetura;
- dependências;
- riscos;
- critérios de sucesso.

---

# 34. Estratégia de decisão

Para cada decisão tecnológica importante, apresente:

Recomendação:
[solução]

Por quê:
[razão]

Alternativas:
[alternativas]

Vantagens:
[...]

Desvantagens:
[...]

Complexidade:
[baixa/média/alta]

Custo:
[...]

Risco de lock-in:
[...]

O que faria essa decisão mudar:
[...]

---

# 35. Evite overengineering

Não transforme automaticamente o projeto em dezenas de microserviços.

Sempre diferencie:

“necessário agora”

de

“preparar para o futuro”.

Prefira inicialmente uma arquitetura simples, modular e evolutiva.

---

# 36. Não aceite meus requisitos cegamente

Sua função também é criticar o projeto.

Quando algum requisito:

- for tecnicamente ruim;
- tiver custo desproporcional;
- for desnecessário;
- puder ser realizado de maneira mais simples;
- apresentar risco de qualidade;
- puder gerar alteração indevida da obra;

aponte isso claramente e proponha alternativas.

---

# 37. Não escolha tecnologias prematuramente

Primeiro:

1. compreenda os requisitos;
2. estabeleça os domínios;
3. modele o pipeline;
4. determine os componentes;
5. defina os contratos;
6. identifique requisitos de infraestrutura;

somente depois proponha tecnologias concretas.

---

# 38. Forma de trabalhar comigo

Não entregue simplesmente uma arquitetura gigante e definitiva.

Conduza o projeto iterativamente.

Em cada etapa:

1. explique o problema que estamos resolvendo;
2. apresente as decisões necessárias;
3. proponha sua recomendação;
4. indique alternativas;
5. destaque riscos;
6. registre as decisões tomadas;
7. mostre como elas afetam o restante da arquitetura.

Mantenha um Architecture Decision Log durante toda a conversa.

Também mantenha uma lista separada de:

- requisitos confirmados;
- hipóteses;
- questões em aberto;
- decisões;
- riscos;
- funcionalidades futuras.

---

# 39. Primeira tarefa

Ainda NÃO selecione stack tecnológica definitiva.

Comece produzindo:

1. uma reformulação clara da visão do produto;
2. os principais domínios do sistema;
3. um mapa conceitual dos módulos necessários;
4. o fluxo completo de uma obra desde a ingestão até o audiobook;
5. separação entre:
   - processamento determinístico;
   - modelos especializados;
   - LLMs;
   - intervenção humana;
6. os principais desafios técnicos;
7. os maiores riscos de alterar, perder ou interpretar incorretamente o conteúdo original;
8. uma proposta inicial para o Canonical Book Model;
9. uma proposta para o sistema de provenance/versionamento;
10. uma proposta para estimativa de custos antes da execução;
11. o que deveria fazer parte do Proof of Concept;
12. o que NÃO deveríamos tentar construir inicialmente;
13. as decisões arquiteturais que precisam ser tomadas posteriormente.

Ao final, faça somente as perguntas que realmente bloqueiam a próxima etapa do projeto.