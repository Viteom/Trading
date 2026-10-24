"""Technical indicators. Squeeze implementation inspired by LazyBear, not TV-verified."""
import math
import statistics


def ema_series(values, period):
    out=[values[0]]
    for value in values[1:]: out.append(out[-1]+2/(period+1)*(value-out[-1]))
    return out


def rma(values, period):
    out=[None]*len(values)
    if len(values)<period: return out
    out[period-1]=sum(values[:period])/period
    for i in range(period,len(values)):
        out[i]=(out[i-1]*(period-1)+values[i])/period
    return out


def linreg_last(values):
    n=len(values)
    mean=sum(values)/n
    center=(n-1)/2
    slope=sum((i-center)*(v-mean) for i,v in enumerate(values))/sum((i-center)**2 for i in range(n))
    return mean+slope*center


def snapshots(rows):
    if len(rows)<100: raise ValueError('Se requieren 100 velas cerradas como mínimo')
    close=[float(r[4]) for r in rows]
    high=[float(r[2]) for r in rows]
    low=[float(r[3]) for r in rows]
    if any(not math.isfinite(v) or v<=0 for series in (close,high,low) for v in series):
        raise ValueError('OHLC inválido')
    fast,mid,slow=[ema_series(close,n) for n in (10,55,100)]
    tr=[high[0]-low[0]]
    plus=[0.];minus=[0.]
    for i in range(1,len(close)):
        tr.append(max(high[i]-low[i],abs(high[i]-close[i-1]),abs(low[i]-close[i-1])))
        up,down=high[i]-high[i-1],low[i-1]-low[i]
        plus.append(up if up>down and up>0 else 0.)
        minus.append(down if down>up and down>0 else 0.)
    atr,up_rma,down_rma=[rma(v,14) for v in (tr,plus,minus)]
    gains=rma([max(b-a,0) for a,b in zip(close,close[1:])],14)
    losses=rma([max(a-b,0) for a,b in zip(close,close[1:])],14)
    pdi=[100*u/a if a else 0. for u,a in zip(up_rma[13:],atr[13:])]
    mdi=[100*d/a if a else 0. for d,a in zip(down_rma[13:],atr[13:])]
    dx=[100*abs(p-m)/(p+m) if p+m else 0. for p,m in zip(pdi,mdi)]
    adx=[None]*13+rma(dx,14)
    detrended=[];states=[]
    for i in range(len(close)):
        if i<19:
            detrended.append(None);states.append(None);continue
        window=close[i-19:i+1]
        mean=sum(window)/20
        # Conventional BB(20,2) and KC(20,1.5, true range); legacy variants differ.
        deviation=statistics.pstdev(window)*2
        kc_range=sum(tr[i-19:i+1])/20*1.5
        states.append('ON' if deviation<kc_range else 'OFF' if deviation>kc_range else 'NEUTRAL')
        detrended.append(close[i]-((max(high[i-19:i+1])+min(low[i-19:i+1]))/2+mean)/2)
    out=[]
    for i in (len(close)-2,len(close)-1):
        gain,loss=gains[i-1],losses[i-1]
        rsi=100-100/(1+gain/loss) if loss else (100. if gain else 50.)
        momentum=linreg_last(detrended[i-19:i+1])
        previous_momentum=linreg_last(detrended[i-20:i])
        out.append(dict(price=close[i],ema10=fast[i],ema55=mid[i],ema100=slow[i],
                        atr=atr[i],rsi=rsi,adx=adx[i],plus_di=pdi[i-13],minus_di=mdi[i-13],
                        squeeze=states[i],momentum=momentum,previous_momentum=previous_momentum))
    return out


def eligible(s, side):
    if s['squeeze']!='OFF' or s['adx']<20: return False
    if side=='LONG':
        return (s['price']>s['ema10']>s['ema55']>s['ema100'] and 50<s['rsi']<70
                and s['plus_di']>s['minus_di'] and s['momentum']>0 and s['momentum']>s['previous_momentum'])
    return (s['price']<s['ema10']<s['ema55']<s['ema100'] and 30<s['rsi']<50
            and s['minus_di']>s['plus_di'] and s['momentum']<0 and s['momentum']<s['previous_momentum'])


def decide(previous,current):
    for side in ('LONG','SHORT'):
        if eligible(current,side) and not eligible(previous,side): return side
    return 'WAIT'
