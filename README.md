# LamoEditor Pro - Editor de Vídeo Profissional

Um aplicativo completo de edição de vídeo profissional construído com PyQt6 e MoviePy.

## 🎬 Recursos

### Edição Principal
- **Timeline Multi-Segmentos**: Adicione múltiplos clipes de vídeo e organize-os em qualquer ordem
- **Pontos In/Out Precisos**: Defina pontos de início e fim exatos para cada clipe
- **Timeline Arrastar e Soltar**: Reordene clipes facilmente na timeline
- **Visualização em Tempo Real**: Assista suas edições em tempo real com controles completos de reprodução

### Efeitos de Vídeo
- **Ajustes de Cor**:
  - Controle de brilho (0-200%)
  - Ajuste de contraste (0-200%)
- **Ferramentas de Transformação**:
  - Rotação (-360° a +360°)
  - Controle de velocidade (0.1x a 10x) - câmera lenta e avanço rápido
- **Filtros**:
  - Conversão para Preto e Branco
  - Espelho horizontal
  - Espelho vertical

### Sobreposições de Texto
- Adicione texto personalizado em qualquer ponto da timeline
- Personalize fonte, tamanho e cor
- Posicione o texto em qualquer lugar (centro, topo, base, esquerda, direita)
- Defina a duração para cada sobreposição de texto
- Suporte para múltiplas sobreposições de texto

### Controle de Áudio
- Ajuste de volume por segmento (0-200%)
- Mixagem de áudio entre múltiplos clipes
- Preserve ou modifique faixas de áudio

### Opções de Exportação
- **Múltiplos Formatos**: MP4 (H.264/H.265), AVI, MOV, WebM
- **Configurações de Qualidade**: Opções de bitrate Baixo, Médio, Alto, Muito Alto
- **Controle de Taxa de Quadros**: Original, 24fps, 30fps, 60fps
- **Rastreamento de Progresso**: Barra de progresso de exportação em tempo real
- **Exportação em Segundo Plano**: Continue trabalhando enquanto exporta

### Gerenciamento de Projetos
- **Salvar Projetos**: Salve sua timeline e configurações como JSON
- **Carregar Projetos**: Retome a edição de projetos salvos
- **Desfazer/Refazer**: Suporte completo para desfazer/refazer (até 50 ações)
- **Auto-salvamento de Estado**: Nunca perca seu trabalho

### Interface do Usuário
- **Design Moderno**: Interface limpa e profissional com estilo Fusion
- **Atalhos de Teclado**:
  - `Espaço`: Reproduzir/Pausar
  - `I`: Definir ponto In
  - `O`: Definir ponto Out
  - `Ctrl+S`: Salvar projeto
  - `Ctrl+O`: Abrir vídeo
  - `Ctrl+Z`: Desfazer
  - `Ctrl+Y`: Refazer
- **Painéis Redimensionáveis**: Personalize seu espaço de trabalho
- **Barra de Status**: Feedback em tempo real sobre todas as operações

## 📋 Requisitos

- Python 3.8 ou superior
- FFmpeg (necessário para o MoviePy)

## 🚀 Instalação

### 1. Instalar FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Baixe de [ffmpeg.org](https://ffmpeg.org/download.html) e adicione ao PATH

### 2. Instalar Dependências Python

```bash
pip install -r requirements.txt
```

Ou instale manualmente:
```bash
pip install PyQt6 PyQt6-Multimedia moviepy numpy Pillow imageio imageio-ffmpeg
```

## 🎯 Uso

### Iniciando o Editor

```bash
python video_editor_pro.py
```

### Fluxo de Trabalho Básico

1. **Abrir um Vídeo**:
   - Clique em "Abrir Vídeo" ou pressione `Ctrl+O`
   - Selecione seu arquivo de vídeo (MP4, MOV, MKV, AVI, WebM, FLV)

2. **Definir Pontos In/Out**:
   - Reproduza o vídeo para encontrar o ponto de início desejado
   - Pressione `I` ou clique em "Set In" para marcar o início
   - Continue reproduzindo para encontrar o ponto final
   - Pressione `O` ou clique em "Set Out" para marcar o fim

3. **Adicionar à Timeline**:
   - Clique em "Add to Timeline" para adicionar o segmento
   - Repita os passos 1-3 para adicionar mais segmentos

4. **Aplicar Efeitos** (Opcional):
   - Selecione um segmento da timeline
   - Vá para a aba "Effects"
   - Ajuste brilho, contraste, rotação, velocidade
   - Ative filtros (P&B, efeitos de espelho)
   - Clique em "Apply Effects to Selected Segment"

5. **Adicionar Texto** (Opcional):
   - Vá para a aba "Text"
   - Digite seu texto
   - Personalize fonte, tamanho, cor, posição
   - Defina a duração
   - Clique em "Add Text Overlay"

6. **Ajustar Áudio** (Opcional):
   - Selecione um segmento da timeline
   - Vá para a aba "Audio"
   - Ajuste o controle deslizante de volume
   - Clique em "Apply Volume to Selected Segment"

7. **Exportar**:
   - Vá para a aba "Export"
   - Escolha formato, bitrate e FPS
   - Clique em "Export Video"
   - Escolha o local para salvar
   - Aguarde a conclusão da exportação

### Gerenciamento da Timeline

- **Reordenar Clipes**: Selecione um clipe e use "Move Up" ou "Move Down"
- **Remover Clipes**: Selecione um clipe e clique em "Remove"
- **Limpar Timeline**: Clique em "Clear Timeline" para começar do zero

### Gerenciamento de Projetos

- **Salvar Projeto**: `Arquivo > Salvar Projeto` ou `Ctrl+S`
- **Carregar Projeto**: `Arquivo > Carregar Projeto`
- Projetos são salvos como arquivos JSON com todas as informações de timeline e efeitos

## 🎨 Recursos Avançados

### Controle de Velocidade
- Crie efeitos de câmera lenta (0.1x - 0.9x)
- Crie efeitos de avanço rápido (1.1x - 10x)
- Aplicado por segmento para máxima flexibilidade

### Múltiplas Sobreposições de Texto
- Adicione sobreposições de texto ilimitadas
- Cada uma com temporização e estilo independentes
- Perfeito para títulos, legendas e créditos

### Empilhamento de Efeitos
- Aplique múltiplos efeitos a um único segmento
- Efeitos são processados em ordem
- Combine ajustes de cor com transformações e filtros

### Sistema de Desfazer/Refazer
- Suporte completo para desfazer/refazer todas as operações
- Armazena até 50 estados anteriores
- Nunca perca seu trabalho devido a erros

## 🔧 Solução de Problemas

### Vídeo Não Abre
- Certifique-se de que o FFmpeg está instalado e no seu PATH
- Verifique se o formato do vídeo é suportado
- Tente converter o vídeo para MP4 primeiro

### Exportação Falha
- Verifique o espaço disponível em disco
- Certifique-se de que o caminho de saída tem permissão de escrita
- Tente um codec diferente ou bitrate menor
- Verifique a instalação do FFmpeg

### Desempenho Lento
- Feche outros aplicativos
- Use vídeos de origem com resolução menor
- Reduza o número de efeitos
- Exporte com bitrate/resolução menor

### Texto Não Aparece
- Certifique-se de que a duração do texto está dentro do comprimento do vídeo
- Verifique se a cor do texto contrasta com o vídeo
- Verifique se a fonte está disponível no seu sistema

## 📝 Dicas e Melhores Práticas

1. **Trabalhe com Cópias**: Sempre trabalhe com cópias dos seus vídeos originais
2. **Salve Frequentemente**: Use `Ctrl+S` frequentemente para salvar seu projeto
3. **Teste Efeitos**: Visualize os efeitos antes de exportar o vídeo completo
4. **Organize Segmentos**: Mantenha sua timeline organizada para facilitar a edição
5. **Use Atalhos de Teclado**: Acelere seu fluxo de trabalho com atalhos
6. **Configurações de Exportação**: Comece com qualidade média, ajuste conforme necessário
7. **Legibilidade do Texto**: Use cores de alto contraste para sobreposições de texto
8. **Níveis de Áudio**: Mantenha o volume entre 80-120% para melhores resultados

## 🎓 Referência de Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| `Espaço` | Reproduzir/Pausar |
| `I` | Definir Ponto In |
| `O` | Definir Ponto Out |
| `Ctrl+O` | Abrir Vídeo |
| `Ctrl+S` | Salvar Projeto |
| `Ctrl+Z` | Desfazer |
| `Ctrl+Y` | Refazer |
| `Ctrl+Q` | Sair |

## 🐛 Limitações Conhecidas

- Arquivos de vídeo muito grandes (>4GB) podem ser lentos para processar
- Alguns efeitos avançados requerem implementação personalizada
- A visualização em tempo real não mostra todos os efeitos (efeitos são aplicados durante a exportação)
- Visualização de sobreposição de texto não disponível (texto aparece na exportação final)

## 🔮 Melhorias Futuras

Recursos potenciais para versões futuras:
- Transições de vídeo (fade, dissolve, wipe)
- Exibição de forma de onda de áudio
- Visualização de miniaturas na timeline
- Chroma key (tela verde)
- Gradação de cor avançada
- Mixagem de áudio multi-faixa
- Processamento em lote
- Aceleração por GPU

## 📄 Licença

Este projeto é fornecido como está para uso educacional e pessoal.

## 🤝 Contribuindo

Sinta-se à vontade para fazer fork, modificar e melhorar este editor!

## 💡 Suporte

Para problemas ou dúvidas:
1. Verifique a seção de Solução de Problemas
2. Verifique a instalação do FFmpeg
3. Verifique as versões do Python e dos pacotes
4. Revise as mensagens de erro no console

---

**Aproveite a edição com o LamoEditor Pro!** 🎬✨
