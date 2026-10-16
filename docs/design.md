# Comes e Bebes: documento de design

Versão 5 (16/10/2026). Nome: **Comes e Bebes** (pode mudar). O que está marcado
**[decidir]** depende do Gabs; o resto é sugestão e pode mudar.

Decidido com o Gabs:

- tempo real, mas sem muita pressa; o desafio é dar conta da cozinha sem
  queimar nada (nem botar fogo em tudo);
- começa como lanchonete e cresce até café, restaurante e bar;
- jogo mão na massa, com gestão leve: compras, cardápio e preço em 5
  faixas;
- o dia termina com a limpeza, depois que a casa fecha;
- três velocidades no menu inicial: Tranquilo, Normal e Corrido;
- limpar até tarde não tem custo: a recompensa é a casa limpa;
- sem funcionários por enquanto: você faz tudo sozinho;
- jogo de conforto, não arcade: sem pontuação nem recorde; o jogador
  continua enquanto quiser, encontrando o seu ritmo;
- o único game over é a vigilância sanitária fechar a casa, e ele volta o
  jogo para o começo da estação;
- o tempo passa como no Stardew Valley: 4 estações de 28 dias, e o que os
  fregueses gostam muda com a estação;
- fregueses de sempre ficam para depois do primeiro protótipo.

## 1. Ideia

Você abre uma lanchonete pequena. Cada dia tem três fases:

1. **Abertura** (menus, sem relógio): compras, cardápio e preços.
2. **Expediente** (tempo real): atender as mesas, preparar cada receita,
   servir, cobrar.
3. **Limpeza** (tempo real, mais calma): deixar a casa pronta para amanhã.

Com lucro e reputação, a casa vira café, restaurante e bar, cada um com
receitas e clientes novos. Os dias passam pelas estações do ano e o jogo
não acaba: é sobre pegar o ritmo da casa, não sobre fazer pontos.

Feito em Python com o r36s-a11y-sdk, como Paciência e Stelar Flow. A
lógica fica separada do som e da fala, com simulador para o equilíbrio.

## 2. Ritmo: tempo real sem pressa

O relógio corre, mas as janelas são largas:

- um cliente espera alguns minutos reais antes de ir embora, e avisa antes
  (três estágios de impaciência);
- comida no fogo tem uma janela boa de vários segundos, com aviso sonoro
  antes de passar do ponto;
- poucos clientes por vez no começo (2 ou 3 mesas ocupadas), e o fluxo
  cresce com a reputação.

O desafio vem de **ter várias coisas no fogo ao mesmo tempo**: enquanto o
hambúrguer grelha você monta o pão e anota outra mesa, e precisa voltar à
chapa na hora certa.

A fala tem prioridade: avisos urgentes (queimando, fogo) cortam a fala
atual; o resto entra na fila e é curto.

Velocidade no menu inicial: Tranquilo, Normal, Corrido. Muda a paciência
dos clientes e o tempo de cozimento. Dá para trocar a qualquer momento
pela pausa.

### Do ponto ao fogo

Cada coisa no fogo passa por estágios, cada um com seu som:

| Estágio | Som | O que fazer |
|---|---|---|
| Cru / cozinhando | chiado baixo | esperar |
| No ponto | sininho da estação + chiado muda de tom | tirar (B) |
| Passando | chiado forte, cheiro "falado" uma vez | tirar logo; o prato vale menos |
| Queimado | fumaça, tosse | jogar fora e refazer |
| Fogo | alarme e crepitar na posição da estação | apagar com o extintor |

Fogo deixa a estação fora de uso até apagar, assusta os clientes (todos
perdem paciência) e, se ninguém apaga, se espalha para a estação vizinha.

## 3. A casa em áudio

O jogador fica no meio da casa e ouve tudo com som 3D:

| Camada | Onde soa | O quê |
|---|---|---|
| Salão | à frente, de esquerda a direita | 3 a 6 mesas, cada uma num ponto do arco |
| Cozinha | atrás, de esquerda a direita | bancada, chapa, fritadeira, liquidificador, pia e lixeira (depois: fogão e forno) |

No protótipo o balcão saiu: duas camadas bastam, e a pia e a lixeira ficaram
na cozinha.

Sons do salão: sininho da porta (chegou cliente), cadeira arrastando na
posição da mesa (sentou), "garçom!" (quer pedir ou pagar), tamborilar,
suspiro e resmungo (impaciência), caixa registradora (pagou), moedas
extras (gorjeta).

## 4. Controles

Seguem o padrão do SDK e dos outros jogos: B (o botão de baixo) confirma e A
volta; Start pausa, Y status, Select lê tudo.

| Botão | O quê |
|---|---|
| Esquerda / direita | Anda entre as mesas ou estações da camada; o som sai da posição dela |
| Cima / baixo | Salão / cozinha |
| B | Ação no foco: anotar, servir, cobrar, recolher louça, pôr no fogo, tirar, virar, sacudir, apagar fogo; no liquidificador, segurar |
| A | Detalha o foco; numa lista, cancela |
| X | O que estou carregando (até 2 itens, um em cada mão) |
| L1 / R1 | Pula para a mesa ou estação anterior / próxima que precisa de você |
| Select | Lê a situação: pedidos abertos, o que está no fogo, quem está impaciente |
| Y | Hora, dia e estação, dinheiro, reputação |
| Start | Pausa |

L1/R1 é o atalho principal: pula direto para quem chamou ou para o que
está no ponto.

## 5. Expediente

Ciclo de uma mesa:

1. **Chega e senta.** Sininho e cadeira na posição da mesa.
2. **Anotar.** B na mesa: o cliente fala o pedido ("um X-burger e um suco
   de laranja"). O pedido vira uma comanda; Select relê as comandas.
3. **Preparar.** Cada item do pedido é uma receita (seção 6).
4. **Servir.** Levar o prato na mão e apertar B na mesa certa. Prato errado
   não é aceito e o cliente repete o pedido.
5. **Comer.** Barulho de talheres; dá tempo de cuidar de outras coisas.
6. **Cobrar.** "Garçom!", B na mesa. O pagamento soma preço e gorjeta; a
   gorjeta depende da espera e da qualidade.
7. **Mesa suja.** Recolher a louça (vai para a pia) antes de outro cliente
   sentar.

## 6. Receitas

Cada receita tem uma peculiaridade, para não virar tudo a mesma coisa:

| Receita | Casa | Como se faz |
|---|---|---|
| Misto quente | Lanchonete | Montar na bancada (pão, presunto, queijo), levar à chapa, virar no meio (B quando a fala pede), tirar no ponto |
| X-burger | Lanchonete | Hambúrguer na chapa; enquanto grelha, montar o pão na bancada; juntar |
| Batata frita | Lanchonete | Cesto na fritadeira; sacudir uma vez no meio; tirar e salgar |
| Suco | Lanchonete | Escolher a fruta, segurar B no liquidificador até o som ficar liso; soltar cedo deixa pedaço, demais esquenta |
| Café coado | Café | Ferver a água no fogão; passar devagar (apertar B no ritmo do gotejar) |
| Pão de queijo | Café | Forno com fornada de 6; um pedido de 2 deixa 4 prontos para os próximos |
| Prato feito | Restaurante | Arroz e feijão em panelas que ficam no fogão o expediente todo (mexer de vez em quando ou grudam); bife na chapa; montar o prato |
| Drink | Bar | Receita com 2 a 4 passos na ordem (gelo, dose, completar, bater); errar a ordem muda o drink |

Na bancada, montar é escolher ingredientes numa lista (cima e baixo, B põe)
e depois Montar, no topo da lista. A mistura certa vira o prato; uma
mistura que não vira nada não gasta ingrediente.

## 7. Limpeza

Depois de fechar a porta, a casa fica em silêncio e a sujeira aparece no
mapa sonoro, cada tipo com seu som:

| Sujeira | Onde | Som | Como limpar |
|---|---|---|---|
| Louça | pia da cozinha | pilha tilintando | lavar uma a uma (B); a pilha diminui de tom |
| Mesas | salão | migalhas, mosca zumbindo | B e passar pano (esquerda e direita alternados, como esfregar) |
| Chão | salão e cozinha | passos grudando quando passa | varrer ou passar o rodo |
| Chapa e fogão | cozinha | gordura estalando | raspar (segurar B) |
| Lixo | cozinha | saco cheio, cheiro "falado" | levar para fora |

Quanto mais sujeira no fim do dia, mais tempo leva; o que você deixar fica
para amanhã. Casa limpa dá bônus de reputação de manhã. Sujeira acumulada
traz problemas: moscas no salão (clientes reclamam), barata (alguém vai
embora sem pagar) e, se piorar, a **vigilância sanitária** aparece.

### Vigilância sanitária: o único game over

A sujeira deixada para trás vira um nível de higiene da casa, que só cai
quando você deixa de limpar dia após dia. Os avisos vêm antes, sempre
falados no fechamento ou na abertura:

1. clientes comentam ("vi uma mosca na mesa");
2. carta de advertência da vigilância: "vamos voltar nesta semana";
3. visita surpresa durante o expediente. Se a casa estiver limpa, tudo
   volta ao normal. Se estiver suja, a casa é interditada: o jogo volta para o dia 1 da
   estação, com o dinheiro, o estoque e as melhorias daquele dia.

Quem limpa um pouco todo dia nunca chega perto disso.

A limpeza não tem cronômetro apertado: você limpa o quanto quiser e
aperta Start → "Ir para casa". Limpar até tarde não tem custo no dia
seguinte; a recompensa é a casa limpa.

## 8. Abertura (gestão leve)

Tudo em menus, sem relógio.

- **Compras.** Ingredientes por pacote (10 pães, 5 kg de batata). A
  geladeira tem espaço limitado e alguns itens estragam em poucos dias.
  Faltar ingrediente no meio do expediente tira o prato do cardápio.
- **Cardápio.** Liga e desliga receitas já aprendidas. Cardápio menor é
  mais fácil de dar conta.
- **Preço em 5 faixas**, por receita: Muito barato, Barato, Justo, Caro,
  Muito caro. Mais barato traz mais clientes e menos lucro por prato; mais
  caro traz menos clientes, mais exigentes, que esperam menos e dão menos
  gorjeta se algo der errado.
- **Melhorias** (com o lucro): mais mesas, segunda chapa, geladeira maior,
  extintor melhor, música ambiente (clientes mais pacientes).
- **Fechamento do dia anterior** é falado antes da abertura: clientes
  atendidos, quem foi embora, gorjetas, lucro, reputação e um comentário
  de cliente. Não há nota nem pontuação.

## 9. Progressão

| Casa | Novidade |
|---|---|
| Lanchonete | 3 mesas, chapa, fritadeira, liquidificador. Tutorial natural |
| Café | Fogão e forno, bebidas com preparo, fornadas, clientes que ficam muito tempo |
| Restaurante | Panelas que ficam no fogo o expediente todo, mais mesas, reservas |
| Bar | Noite, drinks, rodadas, conta aberta, cliente bêbado e barulho |

A casa muda quando junta dinheiro e estrelas suficientes; as receitas de
casas anteriores continuam no cardápio.

Sem funcionários por enquanto: você faz tudo sozinho. Um ajudante pode
voltar a ser discutido depois.

## 10. Calendário e estações

Como no Stardew Valley: **Primavera, Verão, Outono e Inverno, 28 dias
cada**, e depois Ano 2, Ano 3, sem fim. A abertura começa sempre falando
o dia ("Dia 12 do Verão, ano 1, sol forte"). O jogo salva sozinho ao fim
de cada dia.

O que muda com a estação:

| Estação | Fregueses querem | Ambiente |
|---|---|---|
| Primavera | Sanduíche natural, sucos de frutas, bolo de fubá | Passarinhos, janelas abertas |
| Verão | Sucos gelados, açaí, saladas, sorvete; pratos quentes vendem pouco | Cigarras, ventilador, calor que deixa clientes menos pacientes |
| Outono | Pão de queijo, bolo, café com leite | Vento, folhas na porta |
| Inverno | Café, chocolate quente, caldo, sopa; pamonha e quentão na festa junina | Chuva, vento frio, panela no fogo |

- **Pedidos:** o que está na moda na estação é pedido mais vezes e dá
  mais gorjeta. Deixar no cardápio só o que ninguém quer esvazia a casa.
- **Ingredientes da estação** ficam mais baratos e frescos nas compras;
  fora de época, caros ou em falta.
- **Clima do dia** muda o movimento: chuva traz menos gente, mas quem vem
  quer comida quente e fica mais tempo.
- **Datas especiais**, uma ou duas por estação (por exemplo, festa junina
  no inverno), com receitas que só aparecem nesses dias.
- **Fregueses de sempre:** alguns clientes voltam todo dia, com nome, voz
  e pedido preferido, que também muda com a estação. Lembrar o pedido
  deles (e acertar) é parte do conforto do jogo.

### Outono (feito)

- **Receitas novas**, aprendidas no dia 1 do outono e que ficam na casa
  depois: pão na chapa (pão e manteiga na bancada, chapa, virar no meio) e
  suco de mexerica (fruta da estação, descascada na bancada e batida no
  liquidificador). O fornecedor dá um pacote de cada ingrediente novo.
- **Mexerica só nas compras no outono.** Fora de época some da lista; o que
  sobrou estraga em 5 dias.
- **Gostos:** pão na chapa e suco de mexerica são os mais pedidos, misto
  quente sobe e suco de laranja cai.
- **Clima:** dias de vento frio, com folhas na porta quando entra cliente.
- **Som de fundo** do expediente: vento e folhas.
- **Dia das Mães** (dia 12): 50% mais movimento, famílias que quase sempre
  pedem dois itens e gorjeta 50% maior.
- Jogo novo escolhe a estação do primeiro dia.

## 11. Primeiro protótipo

Só a lanchonete, para testar se o ritmo é gostoso:

- 3 mesas;
- chapa, fritadeira, liquidificador e bancada;
- 4 receitas: misto quente, X-burger, batata frita, suco;
- abertura com compras, cardápio e preço em 5 faixas;
- expediente com fogo, extintor e as três velocidades;
- limpeza e vigilância sanitária;
- uma estação (Verão) para começar, com o calendário já funcionando.

O protótipo está em [github.com/gogabs/comes-e-bebes](https://github.com/gogabs/comes-e-bebes).

Fica para depois: café, restaurante, bar, as outras estações, datas
especiais, fregueses de sempre e melhorias.
