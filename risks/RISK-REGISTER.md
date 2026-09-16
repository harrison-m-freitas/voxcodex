# Risk Register

| ID | Risco | Severidade | Mitigação inicial |
|---|---|---|---|
| RISK-01 | adaptação de narração alterar significado | crítica | provenance + comparação + revisão |
| RISK-02 | reading order incorreto | crítica | layout + validação estrutural |
| RISK-03 | conteúdo gerado parecer texto do autor | crítica | content_origin explícito |
| RISK-04 | speaker attribution incorreto | alta | confidence + human review |
| RISK-05 | provenance ser adiada | crítica | tornar requisito do PoC |
| RISK-06 | CBM rígido demais | alta | núcleo genérico + extensões |
| RISK-07 | LLM usado em excesso | alta | preferir parsers/modelos especializados |
| RISK-08 | suporte universal a visual/matemática cedo demais | alta | limitar PoC |
| RISK-09 | caracteres técnicos alterados | crítica no corpus técnico | literal_exact + validação |
| RISK-10 | cobertura incompleta fonte→áudio | crítica | coverage reconciliation |
| RISK-11 | CBM sofrer overfitting ao gênero/formato do corpus-base | alta | núcleo universal mínimo + extensões/roles + validação cross-genre antes do freeze |
| RISK-12 | extração perder tipografia/layout com valor semântico | alta | preservar Source Evidence rica e derivar semântica sem descartar spans/estilos |
| RISK-13 | tabelas e outros dados estruturados serem achatados e perderem relações | crítica em conteúdo técnico | preservar topologia canônica + validação estrutural |
| RISK-14 | callouts/anotações editoriais serem confundidos com conteúdo literal de terminal/código | alta | segmentar origem/função por span e manter provenance |
| RISK-15 | normalização tipada destruir representação superficial significativa (`011`, zeros à esquerda etc.) | alta | preservar lexema superficial e armazenar interpretação apenas como derivação |
| RISK-16 | inferências contaminarem ou sobrescreverem conteúdo canônico | crítica | restringir inferência a Annotation/Relation com status epistemológico + evidence + provenance |
| RISK-17 | revisão congelada ser alterada e quebrar reprodutibilidade | crítica | CanonicalRevision frozen imutável; correções geram nova revision |
| RISK-18 | Annotation/Relation virar estrutura genérica sem contrato e perder semântica | alta | tipos/predicates namespaced + payloads tipados + Role Profiles |
| RISK-19 | regras de especialização ficarem rígidas demais para outros gêneros | alta | Role Profiles permissivos + cross-genre validation antes do freeze |
| RISK-20 | membership/reuso entre revisions ficar ambíguo | alta | registries/manifests explícitos; objeto imutável pode pertencer a múltiplas revisions |
| RISK-21 | ownership de fragments em structured payloads gerar ambiguidade | média/alta | contrato congelado: `ContentFragment` tem um `DocumentNode` owner; refs de payload components são não-owning; reavaliar somente com evidência contrária |
| RISK-22 | text layer/extrator de PDF matemático produzir saída plausível porém semanticamente corrompida | crítica em conteúdo matemático | detectar fórmulas, preservar região/glyph/layout, reconstrução estruturada com provenance/confidence e revisão quando necessário |
| RISK-23 | falha do pipeline ser confundida com incapacidade do CBM e provocar alteração desnecessária do schema | alta | Compatibility Corpus com `PROCESSING_FAILURE` separado de `MODEL_GAP`/`MODEL_FAILURE` + Schema Evolution Log |
| RISK-24 | pipeline M2 achatar a fonte cedo demais e tornar erro de reconstrução impossível de auditar | crítica | preservar Source Evidence rica + EvidenceSnapshot/ReconstructionSnapshot inspecionáveis antes da materialização canônica |
| RISK-25 | M2 expandir para Semantic Enrichment/OCR universal/muitos formatos e perder capacidade de diagnóstico | alta | fronteira SourceArtifact→CanonicalRevision; Tier 1 PDF textual+Markdown; demais formatos/downstream explicitamente adiados |
| RISK-26 | Source Evidence receber semântica documental prematuramente e contaminar reconstrução | crítica | EvidenceUnit registra observação; roles canônicos somente na Reconstruction/CBM |
| RISK-27 | nova extração sobrescrever evidence anterior e destruir capacidade de comparação/auditoria | alta | EvidenceSnapshot imutável e snapshots concorrentes coexistem |
| RISK-28 | native/geometric order ser tratado como logical reading order | crítica | reading order derivado em M2.3 com provenance/confidence |
| RISK-29 | chunk/page/worker boundaries vazarem para a estrutura documental | crítica | OpenStructuralState + cross-boundary reconciliation; processing boundary não implica document boundary |
| RISK-30 | pipeline forçar resolução para regiões ambíguas e criar estrutura inventada | alta | ReconstructionIssue + partial reconstruction + human review orientado a risco |
| RISK-31 | roteamento primário por gênero causar overfitting e falhar em documentos híbridos | alta | reconstruction genre-agnostic baseada em estruturas/sinais observados |
| RISK-32 | materialization reinterpretar Reconstruction e esconder a origem real de uma decisão | crítica | M2.4 só mapeia resultado resolvido; divergência vira MaterializationIssue |
| RISK-33 | evidência significativa ficar fora do CBM sem ser contabilizada | crítica | evidence accountability + unmapped evidence categories + suspected-loss blocker |
| RISK-34 | cache reutilizar output com input/configuração semanticamente incompatível | crítica | ActivityFingerprint + input digests + config semântica versionada |
| RISK-35 | mudança pequena invalidar/reprocessar o livro inteiro e explodir custo | alta | dependency-driven invalidation + region/stage-level reuse + ExecutionPlan |
| RISK-36 | confidence de fontes/modelos diferentes ser comparada como se tivesse mesma escala | alta | confidence localizada + producer/basis/calibration + ReviewRisk separado |
| RISK-37 | provenance ser substituída por logs de observability e perder lineage causal | alta | modelos separados de provenance e telemetry |
| RISK-38 | human review sobrescrever resultados e apagar histórico | alta | ReviewDecision como activity/derivation imutável |
| RISK-39 | golden tests acoplarem-se a IDs/JSON e bloquearem mudanças legítimas | média/alta | assertions semânticas/estruturais por camada |
| RISK-40 | holdouts do M2 serem contaminados por inspeção/tuning durante implementação | crítica | seleção congelada pré-implementação + reveal somente após candidate freeze |
| RISK-41 | Discovery Corpus virar gate ilimitado e impedir fechamento do M2 | média/alta | support tiers + exit criteria explícitos; discovery bloqueia só quando contradiz claims/falha fundamental |
| RISK-42 | ProcessingActivity e Derivation virarem autoridades concorrentes de lineage | crítica | Derivation é autoridade exclusiva de input/output edges; activity só descreve execução |
| RISK-43 | hierarquia Reconstruction divergir entre parent_ref e child_refs | alta | parent_ref + order_key normativos; child_refs derivável e validado |
| RISK-44 | bootstrap bibliográfico gerar CanonicalDocument/Revision inconsistente ou inventado | alta | CanonicalTargetContext + intake/human assertion auditável + provisionamento lógico consistente |
| RISK-45 | revalidation ou stale state mutar artefatos/revisions históricas | crítica | reports suplementares externos + stale contextual + snapshots/revisions imutáveis |
| RISK-46 | blind holdout sofrer claim drift após reveal | crítica | freeze prévio de assertions, holdout selection, candidate config e capability/support-tier claims |
| RISK-47 | provenance frozen apontar para evidence expirada ou irresolvível | alta | retention/addressability policy para artifacts referenciados por frozen revisions |

| RISK-48 | arquivo adquirido perder URL/licença/origem exata e comprometer provenance jurídica/operacional | alta | metadata por CorpusCase + URL/licença explicitamente pendentes quando não capturadas; não inferir origem por filename |
| RISK-49 | bundle de aquisição (HTML salvo/repo ZIP) ser confundido com um único SourceArtifact já normalizado | média/alta | preservar bundle bruto + entrypoint + hashes individuais; unpack/normalização somente como derivação determinística futura |

| RISK-50 | source contendo holdout ser processada integralmente e revelar o escopo reservado por logs/output/adjacência | crítica | quarentena do SourceArtifact inteiro + HOLDOUT-QUARANTINE.json + reveal somente após candidate freeze |
| RISK-51 | assertions de regressão mudarem durante implementação para acomodar o pipeline | crítica | M2-REGRESSION-ASSERTIONS-V1.json frozen/versionado antes do tuning; mudança exige nova versão explícita |

| RISK-52 | substituição de CorpusCase indisponível alterar silenciosamente a cobertura ou a capability claim | alta | decisão explícita + registro do candidato anterior/novo + reclassificação de support tier + provenance do bundle adquirido |

| RISK-53 | corpus de compatibilidade sofrer drift durante implementação e tornar resultados/regressões não reproduzíveis | alta | freeze 30/30 com manifest/digests; qualquer troca posterior exige nova versão explícita do corpus |
