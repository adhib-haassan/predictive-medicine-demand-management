
# Zenodo Example Pipeline — Oncology Inventory (s, SS, Q)

This repository contains a compact, executable example to reproduce the
*before–after* table of inventory parameters described in the manuscript.

## How to run
```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python zenodo_example_pipeline.py   --abcxyz "Anexo 2. Clasificación XYZ.xlsx"   --consumos "Consumos 2023-2024.xlsx"   --arsenal "Arsenal.xlsx"   --overstock "Costos de sobrestock.xlsx"   --params_new "Parámetros de stock.xlsx"   --out_csv table_before_after.csv   --out_tex table_before_after.tex
```

If you already computed optimized parameters, include them in
`Parámetros de stock.xlsx` with columns `[code, s_new, ss_new, q_new]`.
Otherwise, the script computes *illustrative* values consistent with the study.

## Outputs
- `table_before_after.csv`: CSV table ready for inspection
- `table_before_after.tex`: LaTeX table ready to paste into the manuscript

## Reproducibility
- No patient-level data are required.
- The script is robust to minor column-name variants and missing optional files.
