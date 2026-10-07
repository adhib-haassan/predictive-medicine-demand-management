#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zenodo example pipeline — Hospital oncology inventory (s, SS, Q)
-----------------------------------------------------------------
This script reproduces, in an executable way, the *data processing steps* used in
the manuscript to build the illustrative before–after table (Module 7).
It reads raw Excel files, harmonizes keys, selects a small set of high-priority
items (A/B × X/Y), and outputs a compact table with base vs. new parameters.

Inputs (Excel, same folder by default):
  • Anexo 2. Clasificación XYZ.xlsx   → base (s, SS), ABC/XYZ, CV, lead time
  • Consumos 2023-2024.xlsx           → monthly consumption (2023–2024)
  • Arsenal.xlsx                      → price (PPP) and current stock
  • Costos de sobrestock.xlsx         → (optional) inventory value, hold cost
  • Parámetros de stock.xlsx          → (optional) s_new, SS_new, Q_new (provided)

Outputs:
  • table_before_after.csv            → CSV with the before–after table
  • table_before_after.tex            → LaTeX table ready to paste into the paper

Usage (defaults expect the files above in the working directory):
  python zenodo_example_pipeline.py \
      --abcxyz "Anexo 2. Clasificación XYZ.xlsx" \
      --consumos "Consumos 2023-2024.xlsx" \
      --arsenal "Arsenal.xlsx" \
      --overstock "Costos de sobrestock.xlsx" \
      --params_new "Parámetros de stock.xlsx" \
      --out_csv table_before_after.csv \
      --out_tex table_before_after.tex

Notes
-----
• If you already computed optimized parameters (s_new, SS_new, Q_new), place
  them in "Parámetros de stock.xlsx"; the script will merge and prefer those.
• Otherwise, the script computes *illustrative* s_new and SS_new using a simple
  continuous-review logic with CV and lead time, purely for transparency.
• Dependencies: pandas (openpyxl), numpy.
"""

import argparse
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

# ---------- Pandas display (reproducibility) ----------
pd.set_option('display.max_columns', 200)
pd.set_option('display.width', 180)

# ---------- Helpers ----------

def load_excel_any(path: Path, sheet_name=None) -> pd.DataFrame:
    """Load Excel with openpyxl; return empty DataFrame if missing or unreadable."""
    p = Path(path) if path is not None else None
    if p is None or not p.exists():
        warnings.warn(f"File not found: {path}")
        return pd.DataFrame()
    try:
        return pd.read_excel(p, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        warnings.warn(f"Could not read {p}: {e}")
        return pd.DataFrame()


def std_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names: lowercase, ascii-ish, underscores."""
    def clean(c):
        c = str(c).strip().lower()
        for a,b in {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ñ':'n','ü':'u','%':'pct','/':'_','\n':' '}.items():
            c = c.replace(a,b)
        c = c.replace('(', '').replace(')', '').replace('-', ' ')
        return '_'.join(c.split())
    out = df.copy()
    out.columns = [clean(c) for c in out.columns]
    return out


def first_col(df: pd.DataFrame, candidates) -> str | None:
    for cand in candidates:
        if cand in df.columns:
            return cand
    # fallback: contains substring
    for col in df.columns:
        for cand in candidates:
            if cand in col:
                return col
    return None

# ---------- Load layers ----------

def load_abcxyz(path: Path) -> pd.DataFrame:
    df = load_excel_any(path)
    if df.empty:
        return df
    df = std_cols(df)
    code   = first_col(df, ['codigo', 'codigo_inc', 'cod'])
    name   = first_col(df, ['producto', 'medicamento'])
    abc    = first_col(df, ['clasificacion_abc', 'abc'])
    xyz    = first_col(df, ['clasificacion_xyz', 'xyz'])
    s_base = first_col(df, ['punto_de_repo', 'punto_de_reorden', 'reorder'])
    ss_b   = first_col(df, ['stock_de_seguridad', 'ss', 'seguridad'])
    lt     = first_col(df, ['tiempo_prom_entrega', 'lead', 'lt'])
    cv     = first_col(df, ['coeficiente_de_variacion', 'cv'])

    out = pd.DataFrame()
    out['code']    = df[code] if code else np.nan
    out['name']    = df[name] if name else np.nan
    out['abc']     = df[abc]  if abc  else np.nan
    out['xyz']     = df[xyz]  if xyz  else np.nan
    out['s_base']  = pd.to_numeric(df[s_base], errors='coerce') if s_base else np.nan
    out['ss_base'] = pd.to_numeric(df[ss_b],   errors='coerce') if ss_b   else np.nan
    out['lt_days'] = pd.to_numeric(df[lt],     errors='coerce') if lt     else np.nan
    out['cv']      = pd.to_numeric(df[cv],     errors='coerce') if cv     else np.nan

    out['abc'] = out['abc'].astype(str).str.upper().str.strip().str[0]
    out['xyz'] = out['xyz'].astype(str).str.upper().str.strip().str[0]
    return out.dropna(subset=['code'], how='all')


def load_consumos(path: Path) -> pd.DataFrame:
    df = load_excel_any(path)
    if df.empty:
        return df
    df = std_cols(df)
    code = first_col(df, ['codigo', 'codigo_inc', 'cod'])
    name = first_col(df, ['medicamento', 'producto'])
    months = [c for c in df.columns if c.startswith(('ene','feb','mar','abr','may','jun','jul','ago','sept','oct','nov','dic'))]
    if not months:
        months = [c for c in df.columns if c in list(map(str, range(1,13)))]
    out = pd.DataFrame()
    out['code'] = df[code] if code else np.nan
    out['name'] = df[name] if name else np.nan
    if months:
        out['annual_total_cons'] = df[months].apply(pd.to_numeric, errors='coerce').sum(axis=1)
        out['mean_monthly_cons'] = df[months].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    return out.dropna(subset=['code'], how='all')


def load_arsenal(path: Path) -> pd.DataFrame:
    df = load_excel_any(path)
    if df.empty:
        return df
    df = std_cols(df)
    code  = first_col(df, ['codigo_inc','codigo','cod'])
    name  = first_col(df, ['producto','medicamento'])
    price = first_col(df, ['precio_prom_pond','precio','ppp'])
    stock = first_col(df, ['stock_bodega','stock', 'stock_junio'])
    out = pd.DataFrame()
    out['code'] = df[code] if code else np.nan
    out['name'] = df[name] if name else np.nan
    out['price'] = pd.to_numeric(df[price], errors='coerce') if price else np.nan
    out['stock_now'] = pd.to_numeric(df[stock], errors='coerce') if stock else np.nan
    return out.dropna(subset=['code'], how='all')


def load_overstock(path: Path) -> pd.DataFrame:
    df = load_excel_any(path)
    if df.empty:
        return df
    df = std_cols(df)
    code = first_col(df, ['codigo','codigo_inc'])
    inv  = first_col(df, ['valor_inventario', 'valor_inventario_junio_2025'])
    mx   = first_col(df, ['valor_del_stock_maximo', 'valor_stock_maximo'])
    hold = first_col(df, ['costo_de_almacenar','costo_de_almacenaje','costo_almacenar'])
    out = pd.DataFrame()
    out['code'] = df[code] if code else np.nan
    out['inventory_value'] = pd.to_numeric(df[inv], errors='coerce') if inv else np.nan
    out['max_value'] = pd.to_numeric(df[mx], errors='coerce') if mx else np.nan
    out['hold_cost'] = pd.to_numeric(df[hold], errors='coerce') if hold else np.nan
    return out.dropna(subset=['code'], how='all')


def load_params_new(path: Path) -> pd.DataFrame:
    df = load_excel_any(path)
    if df.empty:
        return df
    df = std_cols(df)
    code = first_col(df, ['code','codigo','codigo_inc'])
    snew = first_col(df, ['s_new','s_nuevo','s_opt'])
    ssnw = first_col(df, ['ss_new','ss_nuevo','ss_opt'])
    qnew = first_col(df, ['q_new','q_nuevo','q_opt'])
    out = pd.DataFrame()
    out['code'] = df[code] if code else np.nan
    out['s_new_provided']  = pd.to_numeric(df[snew], errors='coerce') if snew else np.nan
    out['ss_new_provided'] = pd.to_numeric(df[ssnw], errors='coerce') if ssnw else np.nan
    out['q_new_provided']  = pd.to_numeric(df[qnew], errors='coerce') if qnew else np.nan
    return out.dropna(subset=['code'], how='all')

# ---------- Illustrative (s,SS) calculation ----------

def illustrative_policy(df: pd.DataFrame, z: float = 1.65) -> pd.DataFrame:
    d = df.copy()
    mu_m = d['mean_monthly_cons'].fillna(d['annual_total_cons'] / 12.0)
    mu_d = mu_m / 30.0
    lt   = d['lt_days'].fillna(30.0).clip(lower=1.0)
    cv   = d['cv'].fillna(0.25).clip(lower=0.0)
    sigma_d = cv * mu_d
    ss_new = z * sigma_d * np.sqrt(lt)
    s_new  = mu_d * lt + ss_new
    d['s_new_calc']  = s_new.round(3)
    d['ss_new_calc'] = ss_new.round(3)
    return d

# ---------- Build before–after ----------

def build_before_after(abcxyz, consumos, arsenal, overstock, params_new, top_n=6):
    base = abcxyz.copy()
    for df in (base, consumos, arsenal, overstock, params_new):
        if not df.empty and 'code' in df.columns:
            df['code'] = df['code'].astype(str).str.strip()
    out = base.merge(consumos, on='code', how='left', suffixes=('','_cons'))
    out = out.merge(arsenal[['code','price','stock_now']], on='code', how='left')
    out = out.merge(overstock, on='code', how='left')

    # Priority: A/B & X/Y
    mask = out['abc'].isin(['A','B']) & out['xyz'].isin(['X','Y'])
    prio = out[mask].copy()
    prio['rank_key'] = prio['inventory_value'].fillna(0)*10 \
                     + prio['price'].fillna(0) * prio['mean_monthly_cons'].fillna(0) \
                     + prio['cv'].fillna(0)
    prio = prio.sort_values('rank_key', ascending=False).head(top_n)

    prio = illustrative_policy(prio)
    if not params_new.empty:
        prio = prio.merge(params_new, on='code', how='left')
        prio['s_new']  = prio['s_new_provided'].fillna(prio['s_new_calc'])
        prio['ss_new'] = prio['ss_new_provided'].fillna(prio['ss_new_calc'])
    else:
        prio['s_new']  = prio['s_new_calc']
        prio['ss_new'] = prio['ss_new_calc']

    prio['q_new'] = prio.get('q_new_provided', np.nan)

    table = prio[['code','name','abc','xyz','s_base','ss_base','s_new','ss_new','q_new']].copy()
    for c in ['s_base','ss_base','s_new','ss_new','q_new']:
        table[c] = pd.to_numeric(table[c], errors='coerce').round(3)
    table = table.rename(columns={
        'code':'Item','name':'Description',
        's_base':'$s_{base}$','ss_base':'$SS_{base}$',
        's_new':'$s_{new}$','ss_new':'$SS_{new}$','q_new':'$Q_{new}$'
    })
    return table

# ---------- Export ----------

def to_latex_table(df: pd.DataFrame, out_path: Path):
    order = ['Item','Description','abc','xyz','$s_{base}$','$SS_{base}$','$s_{new}$','$SS_{new}$','$Q_{new}$']
    cols = [c for c in order if c in df.columns]
    latex = df[cols].to_latex(index=False, escape=True)
    Path(out_path).write_text(latex, encoding='utf-8')

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description='Build before–after (s,SS,Q) table from raw Excel layers.')
    ap.add_argument('--abcxyz', type=Path, default=Path('Anexo 2. Clasificación XYZ.xlsx'))
    ap.add_argument('--consumos', type=Path, default=Path('Consumos 2023-2024.xlsx'))
    ap.add_argument('--arsenal', type=Path, default=Path('Arsenal.xlsx'))
    ap.add_argument('--overstock', type=Path, default=Path('Costos de sobrestock.xlsx'))
    ap.add_argument('--params_new', type=Path, default=Path('Parámetros de stock.xlsx'))
    ap.add_argument('--out_csv', type=Path, default=Path('table_before_after.csv'))
    ap.add_argument('--out_tex', type=Path, default=Path('table_before_after.tex'))
    ap.add_argument('--top_n', type=int, default=6)
    args = ap.parse_args()

    abcxyz = load_abcxyz(args.abcxyz)
    consum = load_consumos(args.consumos)
    ars    = load_arsenal(args.arsenal)
    over   = load_overstock(args.overstock)
    pnew   = load_params_new(args.params_new)

    if abcxyz.empty:
        raise SystemExit('ERROR: ABC/XYZ (with base s and SS) is required.')

    table = build_before_after(abcxyz, consum, ars, over, pnew, top_n=args.top_n)
    table.to_csv(args.out_csv, index=False)
    to_latex_table(table, args.out_tex)
    print('Saved:', args.out_csv, 'and', args.out_tex)

if __name__ == '__main__':
    main()
