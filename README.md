# Comes e Bebes

Jogo de áudio de lanchonete para o R36S acessível, jogável só com som e fala.
Você toca uma lanchonete pequena no seu ritmo: de manhã faz as compras e
ajusta o cardápio e os preços, no expediente atende as mesas e cozinha em
tempo real sem deixar nada queimar, e de noite limpa a casa. Não tem
pontuação nem fim: os dias passam pelas quatro estações, com 28 dias cada.

Este é o **primeiro protótipo**: só a lanchonete, com 3 mesas, chapa,
fritadeira, liquidificador e 4 receitas (misto quente, X-burger, batata frita
e suco de laranja) no verão. A **Primavera**, o **Outono** e o **Inverno** têm
receitas, ingredientes, som de fundo e data especial próprios. Ao começar um jogo novo, você escolhe a estação do primeiro dia. Ideia completa, decisões e o que fica
para depois: [docs/design.md](docs/design.md).

Feito em Python com a biblioteca do
[r36s-a11y-sdk](https://github.com/gogabs/r36s-a11y-sdk).

## A casa em sons

O salão fica à sua frente, com as mesas 1, 2 e 3 da esquerda para a direita.
A cozinha fica atrás: bancada, chapa, fritadeira, liquidificador, pia e
lixeira. Cada som sai do lugar dele: a cadeira arrastando na mesa onde o
cliente sentou, o chiado da chapa atrás de você à esquerda.

## Controles

No expediente:

| Botão | O quê |
|---|---|
| Cima / baixo | Salão / cozinha |
| Esquerda / direita | Anda entre as mesas ou estações |
| B | Ação da vez no foco: anotar, servir, cobrar, recolher louça, pôr no fogo, tirar, virar, sacudir, apagar fogo. No liquidificador, segure. Na bancada, abre a lista de ingredientes |
| A | Detalha o foco (com a paciência do cliente) |
| X | O que está nas mãos (são duas) |
| Y | Hora, dia, dinheiro e reputação |
| L1 / R1 | Pula para a mesa ou estação anterior / seguinte que precisa de você |
| Select | Lê a situação da casa inteira |
| Start | Pausa, com a velocidade (Tranquilo, Normal, Corrido) |

Na bancada: cima e baixo escolhem, B põe o ingrediente, **Montar** fica no
topo da lista e A cancela.

Na limpeza: B nas mesas e no chão começa a esfregar (esquerda e direita
alternadas), na chapa e na fritadeira segure B para raspar, na pia B lava um
prato e no lixo B leva para fora. Y diz o que falta. Start e **Ir para casa**
encerram o dia.

## Receitas

| Receita | Como se faz |
|---|---|
| Misto quente | Pão, presunto e queijo na bancada; chapa; virar no meio; tirar no ponto |
| X-burger | Carne na bancada; chapa; com o hambúrguer na mão, pão e queijo na bancada |
| Batata frita | Batata na bancada; fritadeira; sacudir no meio; tirar; sal na bancada |
| Suco de laranja | Laranja na bancada; liquidificador; segurar B até o som ficar liso |

## Outono

No primeiro dia do outono a casa aprende duas receitas e ganha um pacote de
cada ingrediente novo. Os fregueses passam a pedir mais coisa quentinha e
menos suco de laranja, e o expediente tem vento e folhas ao fundo.

| Receita | Como se faz |
|---|---|
| Pão na chapa | Pão e manteiga na bancada; chapa; virar no meio; tirar no ponto |
| Suco de mexerica | Mexerica na bancada; liquidificador; segurar B. A mexerica só aparece nas compras no outono |

No dia 12 é **Dia das Mães**: a casa enche de famílias, que pedem mais e
deixam gorjetas maiores.

## Inverno

No primeiro dia do inverno a casa aprende mais duas receitas. Os fregueses
querem coisa bem quente, quase ninguém pede suco, e o expediente tem garoa no
toldo e vento baixo ao fundo.

| Receita | Como se faz |
|---|---|
| Queijo quente | Pão e queijo na bancada; chapa; virar no meio; tirar no ponto |
| Chocolate quente | Leite e chocolate na bancada; liquidificador; segurar B. Batido demais, espuma |

No dia 3 é **Dia de São João**: tem quadrilha na praça e o povo passa na
casa para se esquentar.

## Primavera

Na primavera a casa aprende as últimas duas receitas. Os fregueses querem
coisa fresca, e o expediente tem passarinhos ao fundo.

| Receita | Como se faz |
|---|---|
| Sanduíche natural | Pão, frango desfiado e alface na bancada; já sai pronto |
| Vitamina de morango | Morango e leite na bancada; liquidificador; segurar B. O morango só aparece nas compras na primavera |

No dia 21 é **Dia das Crianças**: famílias com a criançada, que pedem mais e
deixam gorjetas maiores.

Depois do ponto a comida passa, queima e pega fogo. O extintor (B na estação
pegando fogo) apaga, mas deixa sujeira.

## Rodar

No PC (Windows, com o SDK clonado ao lado ou a cópia em `r36s_a11y/`):

```bat
python main.py
```

No console, com o SDK clonado ao lado deste repositório:

```bash
./instalar.sh
```

O jogo salva sozinho no começo e no fim de cada dia. Sair no meio do
expediente recomeça o dia da abertura.

## Desenvolvimento

```bash
python3 -m unittest discover -s tests       # testes
python3 tools/simular.py --dias 7           # equilíbrio com um jogador automático
python3 tools/simular.py --estacao Inverno  # o mesmo, começando no inverno
python3 tools/gerar_sons.py                 # sons provisórios
```

Os números do equilíbrio ficam em `comes/config.py` e as receitas e estações
em `comes/data.py`. A lógica em `comes/` não toca som nem fala: `casa.py` é o
que vai para o save (dinheiro, estoque, calendário, sujeira, vigilância),
`expediente.py` é o salão e a cozinha em tempo real e `limpeza.py` é o fim do
dia. `main.py` liga tudo ao SDK.

Os sons em `sounds/` são provisórios, gerados por código. Para trocar um, ponha
um WAV ou OGG com o mesmo nome e apague o provisório.
