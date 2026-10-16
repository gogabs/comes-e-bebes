# Origem e atualização da SDK

A cópia de reserva em `r36s_a11y/` corresponde à main de
[gogabs/r36s-a11y-sdk](https://github.com/gogabs/r36s-a11y-sdk) no commit
`3f12376e3548f1880dda5f6f9937ea630c8e8e6c`, a mesma do Stelar Flow. Não há
patches exclusivos do jogo. `sdk-origin.json` registra os hashes dos arquivos.

O instalador prefere um clone da SDK ao lado deste repositório e usa a cópia
incluída como reserva. Para atualizar a cópia de reserva:

```sh
python3 tools/sync_sdk.py --sdk ../r36s-a11y-sdk
python3 -m unittest discover -s tests
git diff -- r36s_a11y sdk-origin.json
```
