import numpy as np, wave
import story
SR=44100; D=float(story.DURATION); FIN=D-2.7; N=int(SR*D)
out=np.zeros(N)
def f(n): return 440*2**((n-69)/12)
def note(t0,freq,dur,vol,kind="box"):
    i0=int(t0*SR); n=int(dur*SR); 
    if i0>=N: return
    n=min(n,N-i0); tt=np.arange(n)/SR
    ph=(freq*tt)%1.0
    if kind=="box":
        s=np.where(ph<0.25,1.0,-1.0)*0.6
        env=np.where(tt<0.3,1.0,np.exp(-(tt-0.3)*8))*np.exp(-tt*1.2)*np.minimum(1,tt/0.003)
    else:
        s=(4*np.abs(ph-0.5)-1)
        env=np.where(tt<1.2,1.0,np.exp(-(tt-1.2)*10))*np.minimum(1,tt/0.003)
    out[i0:i0+n]+=vol*s*env
mel=story.MELODY
bass=story.BASS
beat=story.BEAT
quiet=[(e[1],e[2]) for e in story.SFX if e[0]=="noise"]
t=0.4; i=0
while t<FIN:
    m=mel[i%len(mel)]
    vol=0.11 if any(a<t<b for a,b in quiet) else 0.18
    if m: note(t,f(m),1.2,vol)
    if i%4==0: note(t,f(bass[(i//4)%len(bass)]),1.6,0.16,"bass")
    t+=beat; i+=1
rng=np.random.default_rng(1)
for ev in story.SFX:
    kind,t0=ev[0],ev[1]
    if kind=="sad":        # deux notes qui descendent
        note(t0,f(67),0.6,0.15); note(t0+0.3,f(63),0.9,0.15)
    elif kind=="noise":    # bruit doux (pluie, vent, vagues) + petites notes "plic"
        t1=ev[2]; a,b=int(t0*SR),int(t1*SR)
        nz=rng.standard_normal(b-a); y=np.zeros_like(nz); acc=0
        for k in range(len(nz)): acc=acc*0.85+nz[k]*0.15; y[k]=acc
        tt=np.arange(b-a)/SR; env=np.minimum(1,tt/0.6)*np.minimum(1,(tt[-1]-tt)/0.6)
        out[a:b]+=0.10*y*env
        tp=t0+0.2
        while tp<t1-0.3:
            note(tp,f(rng.integers(84,96)),0.15,0.07); tp+=rng.uniform(0.12,0.3)
    elif kind=="joy":      # arpège joyeux qui monte
        for j,m in enumerate([72,76,79,84,88,91]): note(t0+j*0.09,f(m),1.0,0.14)
    elif kind=="shimmer":  # scintillement magique
        for j,m in enumerate([79,84,88,91,96]): note(t0+j*0.25,f(m),1.2,0.08)
    elif kind=="boing":    # petit rebond / chute rigolote
        for j in range(8): note(t0+j*0.03,f(60+j*3 if j<4 else 72-(j-4)*4),0.08,0.12)
    elif kind=="click":    # petit cliquetis de clé
        note(t0,f(96),0.05,0.10); note(t0+0.05,f(91),0.05,0.08)
    elif kind=="oops":     # essai raté
        note(t0,f(64),0.25,0.14); note(t0+0.2,f(58),0.6,0.14)
for m in [60,64,67,72,76]: note(FIN,f(m),2.6,0.12)
note(FIN,f(48),2.6,0.15,"bass")

from speech import SYLL
from story import VOICES, HERO
voice=np.zeros(N)
VOW=[(800,1200),(400,2000),(300,2300),(450,800),(320,700)]  # a e i o u
rv=np.random.default_rng(5)
for who,t0,dur,pf,v in SYLL:
    base=VOICES.get(who,300)
    fs=1.0+max(0,(base-230))/1100
    i0=int(t0*SR); n=int(dur*SR); tt=np.arange(n)/SR
    f0=base*pf*(1+0.10*np.sin(np.pi*tt/dur))*(1+0.015*np.sin(2*np.pi*6*tt))
    ph=2*np.pi*np.cumsum(f0)/SR
    F1,F2=VOW[v]; F1*=fs; F2*=fs
    sig=np.zeros(n)
    for k in range(1,25):
        fk=k*base*pf
        if fk>5000: break
        a=(np.exp(-((fk-F1)/180)**2)+0.6*np.exp(-((fk-F2)/260)**2)+0.08)/k**0.6
        sig+=a*np.sin(k*ph)
    att=min(n,int(0.012*SR)); env=np.ones(n); env[:att]=np.linspace(0,1,att)
    rel=int(0.05*SR); env[-rel:]*=np.linspace(1,0,rel)
    # little consonant click at start
    cl=min(n,int(0.015*SR)); sig[:cl]+=rv.standard_normal(cl)*0.6*np.linspace(1,0,cl)
    voice[i0:i0+n]+=sig*env*0.5
# duck music under voice
act=(np.abs(voice)>0).astype(float)
k=int(0.15*SR); ker=np.ones(k)/k
act=np.clip(np.convolve(act,ker,'same')*3,0,1)
out=out/np.abs(out).max()*0.6*(1-0.55*act)+voice/np.abs(voice).max()*0.8
out*=np.minimum(1,(D-np.arange(N)/SR)/0.8)
out/=max(1e-9,np.abs(out).max())/0.85
pcm=(out*32767).astype(np.int16)
st=np.repeat(pcm[:,None],2,axis=1)
w=wave.open("music_mix.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()
