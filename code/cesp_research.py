from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import json
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path('./'); OUT=ROOT/'artifacts'; OUT.mkdir(parents=True,exist_ok=True)
RISK=['SPY','QQQ','IWM','EFA','VNQ','XLE','DBC','BTC-USD','ETH-USD']
DEF=['TLT','IEF','GLD','UUP']
ALL=RISK+DEF
@dataclass
class Config:
    start: str = '2015-01-02'
    end: str | None = None
    vol_span: int = 63
    pressure_span: int = 21
    percentile_window: int = 252
    threshold: float = .70
    cost_bps: float = 10.0
CFG=Config()

def download():
    end=CFG.end or (pd.Timestamp.now(tz='UTC').tz_localize(None)+pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    raw=yf.download(ALL,start=CFG.start,end=end,auto_adjust=True,progress=False,group_by='column',threads=False)
    close=raw['Close'] if isinstance(raw.columns,pd.MultiIndex) else raw[['Close']]
    close=close.reindex(columns=ALL).dropna(how='all').ffill().dropna(how='all')
    close.to_csv(OUT/'prices.csv')
    return close

def ces_state(close,cfg=CFG):
    r=np.log(close).diff(); vol=r.ewm(span=cfg.vol_span,min_periods=cfg.vol_span).std().shift(1)
    z=(r/(vol+1e-8)).replace([np.inf,-np.inf],np.nan)
    x=z[RISK].dropna(how='all')
    absz=x.abs(); p=(absz+1e-8).div(absz.sum(axis=1)+1e-8,axis=0)
    H=-(p*np.log(p+1e-8)).sum(axis=1)/np.log(len(RISK))
    signs=np.sign(x).fillna(0); S=((signs.sum(axis=1)**2-signs.pow(2).sum(axis=1))/(len(RISK)*(len(RISK)-1))).clip(-1,1)
    amp=np.sqrt((x.pow(2).mean(axis=1)).clip(lower=0))
    psi=(1-H)*S.clip(lower=0)*amp
    pressure=psi.ewm(span=cfg.pressure_span,min_periods=cfg.pressure_span).mean()
    hist=pressure.rolling(cfg.percentile_window,min_periods=60).rank(pct=True).shift(1)
    wd=((hist-cfg.threshold)/(1-cfg.threshold)).clip(0,1).fillna(0)
    out=pd.DataFrame({'entropy':H,'synchronization':S,'amplitude':amp,'psi':psi,'pressure':pressure,'percentile':hist,'defensive_weight':wd})
    return out

def metrics(ret,name):
    r=ret.dropna(); eq=(1+r).cumprod(); years=len(r)/252; cagr=eq.iloc[-1]**(1/years)-1 if years and eq.iloc[-1]>0 else np.nan; vol=r.std()*np.sqrt(252); sharpe=r.mean()*252/vol if vol>0 else np.nan; dd=eq/eq.cummax()-1
    return {'strategy':name,'cagr':cagr,'volatility':vol,'sharpe':sharpe,'max_drawdown':dd.min(),'calmar':cagr/abs(dd.min()) if dd.min()<0 else np.nan,'observations':len(r)}

def run(close,cfg=CFG):
    r=close.pct_change().fillna(0); st=ces_state(close,cfg).reindex(r.index).ffill().fillna(0); w=st.defensive_weight.shift(1).fillna(0); trade=w.diff().abs().fillna(0)
    risk=r[RISK].mean(axis=1); defensive=r[DEF].mean(axis=1)
    ces=(1-w)*risk+w*defensive-trade*cfg.cost_bps/10000
    vol= risk.rolling(63).std().shift(1); vt=(.10/(vol*np.sqrt(252)).clip(.05,.40)).clip(0,1).fillna(.5); vtret=vt*risk+(1-vt)*defensive
    sma=(close['SPY']<close['SPY'].rolling(200).mean()).astype(float).shift(1).fillna(0); smaret=(1-sma)*risk+sma*defensive-sma.diff().abs().fillna(0)*cfg.cost_bps/10000
    static=.6*risk+.4*defensive
    rng=np.random.default_rng(42); target=w.mean(); state=pd.Series((rng.random(len(w))<target).astype(float),index=w.index); placebo=(1-state)*risk+state*defensive
    strategies={'CESP':ces,'Risk equal-weight':risk,'Defensive equal-weight':defensive,'60_40':static,'SMA200 mix':smaret,'Vol-targeted mix':vtret,'Random exposure placebo':placebo}
    stats=pd.DataFrame([metrics(x,n) for n,x in strategies.items()]); stats['defensive_exposure']=np.nan; stats.loc[stats.strategy=='CESP','defensive_exposure']=w.mean(); stats.loc[stats.strategy=='CESP','turnover']=trade.mean()*252
    out=st.copy(); out['risk_return']=risk; out['defensive_return']=defensive; out['cesp_return']=ces; out['cesp_equity']=(1+ces).cumprod(); out['risk_equity']=(1+risk).cumprod(); out['defensive_equity']=(1+defensive).cumprod(); out['weight']=w; out['date']=out.index.astype(str)
    out.to_csv(OUT/'cesp_diagnostics.csv'); stats.to_csv(OUT/'cesp_summary.csv',index=False); pd.DataFrame(strategies).to_csv(OUT/'cesp_returns.csv')
    return out,stats

def sensitivity(close):
    rows=[]
    for th in [.60,.70,.80]:
        for span in [10,21,42]:
            c=Config(threshold=th,pressure_span=span); _,s=run(close,c); a=s[s.strategy=='CESP'].iloc[0].to_dict(); a.update({'threshold':th,'pressure_span':span}); rows.append(a)
    pd.DataFrame(rows).to_csv(OUT/'cesp_sensitivity.csv',index=False)

def main():
    close=download(); diag,summary=run(close); sensitivity(close); json.dump({'risk_assets':RISK,'defensive_assets':DEF,'config':CFG.__dict__,'retrieved_utc':pd.Timestamp.now(tz='UTC').isoformat()},open(OUT/'metadata.json','w'),indent=2); print(summary.to_string(index=False))
if __name__=='__main__': main()
