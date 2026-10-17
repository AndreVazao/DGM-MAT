# Avaliação de referência externa — Moli

- Data da avaliação: 2026-10-17
- Repositório: https://github.com/lexmount/moli
- Estado: **REFERÊNCIA A INVESTIGAR; não integrar diretamente**
- Categoria: navegador headless / automação web para agentes de IA

## Resumo

Moli é um navegador headless open source escrito em Rust, orientado a agentes de IA. Expõe uma CLI e interfaces de automação compatíveis com CDP, WebDriver Classic e WebDriver BiDi. Pode obter páginas, extrair conteúdo em Markdown/HTML/JSON/árvore semântica, executar JavaScript e automatizar tarefas web. Suporta Windows, Linux e macOS.

O projeto declara licenciamento Apache-2.0 ou MIT por opção, salvo componentes e ficheiros com licenças próprias. Antes de reutilizar código, confirmar os avisos/licenças de cada componente.

## Valor potencial para DGM-MAT

1. **Navegação e pesquisa web para agentes:** alternativa a fluxos baseados exclusivamente em scraping ou a um browser completo.
2. **Extração estruturada para contexto de LLM:** Markdown e árvores semânticas podem reduzir ruído antes de enviar conteúdo ao modelo.
3. **Automação compatível com ferramentas existentes:** CDP e WebDriver podem facilitar integração com clientes e bibliotecas de automação já usados.
4. **Operações visuais sob pedido:** o layout, a geometria e as capturas podem ser ativados quando necessários, em vez de manter rendering contínuo.
5. **Opção local/open source:** potencialmente alinhada com a preferência do DGM-MAT por ferramentas locais e sem dependência obrigatória de APIs pagas.

## Limites e riscos a validar

- Moli não é um browser gráfico normal: não oferece janela persistente nem pretende reproduzir fielmente todos os comportamentos visuais de Chrome.
- Canvas/WebGL, reprodução multimédia e certos modos de screenshot/print têm limitações documentadas.
- A opção de layout sob pedido tem semântica própria; validar a atualidade da geometria antes de usar coordenadas após alterações na página.
- Confirmar compatibilidade real com o hardware modesto e a versão de Windows do PC de desenvolvimento.
- Inspecionar instalação, binários/releases, dependências, licenças, permissões de rede, cookies, perfis, proxies e armazenamento antes de o executar.
- Páginas web são entrada não confiável. Restringir acesso a localhost, redes privadas, ficheiros locais, credenciais e sessões autenticadas; impor allowlists, timeouts e limites de recursos.
- Não presumir que suporta CAPTCHA, autenticação, todos os sites ou todas as operações Playwright.
- A alegação do upstream de prontidão para produção deve ser confirmada por testes próprios; o projeto continua em desenvolvimento ativo.

## Decisão recomendada

**Guardar como candidato de referência e fazer uma prova de conceito isolada; não adicionar já como dependência obrigatória nem importar código para o DGM-MAT.**

### Prova de conceito proposta

1. Ler README, documentação, skills, release notes e licenças atuais.
2. Testar instalação e remoção reversível num diretório isolado, sem privilégios administrativos desnecessários.
3. Comparar com a solução de browser já existente no DGM-MAT: fiabilidade, consumo de RAM/CPU, latência, compatibilidade com JavaScript e páginas dinâmicas, extração Markdown/semântica, screenshots e recuperação de erros.
4. Testar limites de rede e isolamento, sem cookies pessoais nem credenciais reais.
5. Medir o consumo no PC atual antes de considerar execução contínua.
6. Integrar apenas através de um adaptador opcional, com timeouts, logs, health check e fallback para o mecanismo existente.
7. Documentar resultados reproduzíveis e só então decidir se vale a pena adotar.

## Critérios de aprovação

- Os testes são reproduzíveis e não alteram repositórios nem perfis de utilizador.
- O consumo de recursos é aceitável no hardware-alvo.
- O browser não acede a destinos locais/privados fora da política definida.
- As falhas são explícitas e não são reportadas como ações concluídas.
- O DGM-MAT continua funcional se Moli não estiver instalado ou falhar.
- Licenças e cadeia de distribuição são verificadas.

## Fontes

- Repositório: https://github.com/lexmount/moli
- README: https://github.com/lexmount/moli/blob/main/README.md

## Regra de manutenção

Este documento regista uma hipótese técnica, não uma decisão de adoção. Atualizar após uma auditoria real da versão/release que for testada. Não executar merges, instalações ou alterações de arquitetura apenas com base nesta nota.
