# Padrão de Nomes de Arquivos PDF

Os arquivos PDF localizados na pasta `/data/raw/pdf` seguem um padrão de nomenclatura específico, que facilita a identificação e organização dos dados.

## Padrão Identificado

O formato geral dos nomes dos arquivos é:

`aviario_XXXX_ptY.pdf`

Onde:

*   `aviario_`: Prefixo fixo que indica que o arquivo se refere a um aviário.
*   `XXXX`: Um identificador numérico de 4 dígitos para o aviário (por exemplo, `1203`, `1204`, `1262`, `1263`).
*   `_ptY`: Indica a parte do documento PDF, onde `Y` é um número sequencial (por exemplo, `pt1`, `pt2`, `pt3`). Isso sugere que documentos maiores foram divididos em várias partes.
*   `.pdf`: A extensão do arquivo, indicando que é um documento PDF.

## Exemplos:

*   `aviario_1203_pt1.pdf`: Primeira parte do documento do aviário 1203.
*   `aviario_1204_pt2.pdf`: Segunda parte do documento do aviário 1204.
*   `aviario_1262_pt1.pdf`: Primeira parte do documento do aviário 1262.

Este padrão permite que os arquivos sejam facilmente agrupados por aviário e ordenados por parte, o que é útil para processamento e análise.