"""リングA CAD（腕石レール付き）→ リングB（腕石なし・甲丸肩）アレンジモデル生成"""
import json,base64,struct,math,sys
src,dst=sys.argv[1],sys.argv[2]
D=json.load(open(src))
XH=4.85      # これより外側（|x|）が肩レール領域
PHI_END=62.0 # 置き換える範囲の下端角度（度）

def dec(c):
    pos=base64.b64decode(c['pos']);v=struct.unpack('<%dH'%(len(pos)//2),pos);q=c['q']
    P=[(q['min'][0]+v[3*i]*q['sc'],q['min'][1]+v[3*i+1]*q['sc'],q['min'][2]+v[3*i+2]*q['sc']) for i in range(len(v)//3)]
    idx=base64.b64decode(c['idx']);I=struct.unpack('<%dH'%(len(idx)//2),idx)
    return P,[I[i:i+3] for i in range(0,len(I),3)]
def phi(p):return math.degrees(math.atan2(abs(p[0]),p[2]))
def rr(p):return math.hypot(p[0],p[2])
def interp(tbl,x):
    tbl=sorted(tbl)
    if x<=tbl[0][0]:return tbl[0][1]
    if x>=tbl[-1][0]:return tbl[-1][1]
    for (a,u),(b,w) in zip(tbl,tbl[1:]):
        if a<=x<=b:return u+(w-u)*(x-a)/(b-a)
def smooth(tbl,k=2):
    o=[]
    for i in range(len(tbl)):
        s=tbl[max(0,i-k):i+k+1];o.append((tbl[i][0],sum(v for _,v in s)/len(s)))
    return o

def build(c):
    P,T=dec(c)
    # 角度ごとの形状を計測
    gap=[];rin=[];rmax=[]
    for a in range(14,90):
        s=sorted(rr(p) for p in P if p[2]>0 and abs(p[0])>XH-1.5 and a-1<=phi(p)<a+1)
        if not s:continue
        rin.append((a,s[0]));rmax.append((a,s[-1]))
        g=[(s[i],s[i+1]) for i in range(len(s)-1) if s[i+1]-s[i]>0.25 and s[i]<11]
        if g and a>=16:gap.append((a,g[0][0],g[0][1]))
    gap=[g for g in gap if g[0]<=60]
    # 連続している隙間の範囲
    phi_gap_end=max(g[0] for g in gap)
    band_top=[(a,lo) for a,lo,hi in gap]; rail_in=smooth([(a,hi) for a,lo,hi in gap])
    sh=[s for s in c['stones'] if abs(s['y'])<0.05 and abs(s['x'])>4.5]
    rail_top=sorted({(round(math.degrees(math.atan2(abs(s['x']),s['z'])),2),math.hypot(s['x'],s['z'])) for s in sh})
    last_st=rail_top[-1][0]
    plain_out=interp(rmax,PHI_END+1)
    # 石座の無い通常腕（62〜72°）の外径を直線近似して外挿
    pl=[(a,r) for a,r in rmax if PHI_END<=a<=PHI_END+10];n_=len(pl);ma=sum(a for a,_ in pl)/n_;mr=sum(r for _,r in pl)/n_
    sl=sum((a-ma)*(r-mr) for a,r in pl)/sum((a-ma)**2 for a,_ in pl)
    plain_fit=lambda a:mr+sl*(a-ma)
    top_tbl=[(rail_top[0][0]-6,rail_top[0][1]+0.02)]+rail_top+[(PHI_END+1,plain_out)]
    # 腕の内径・外径（石座の無い位置で計測）：上部は隙間の下端、下部は通常腕
    full=[]
    for a in range(0,181,2):
        t=[rr(p) for p in P if (a-1.5)<=phi(p)<(a+1.5) and (p[2]<0 or abs(p[0])>XH-1.5)]
        if t:full.append((a,min(t),max(t)))
    bt=[(a,lo) for a,lo,hi in gap if a<=44]
    plain=[(a,mx) for a,mn,mx in full if a>=PHI_END]
    a_bt=bt[-1][0]
    a_m=rail_top[-1][0]
    rt=[(a,r-0.12) for a,r in rail_top]+[(PHI_END,interp(plain,PHI_END))]
    def R_top(a):
        if a<=rt[0][0]:return rt[0][1]+0.02*(rt[0][0]-a)/6
        return interp(rt,a)
    def band_out(a):
        if a<=a_bt:return interp(bt,a)
        if a>=PHI_END:return interp(plain,a)
        if a>=a_m:return R_top(a)
        t=(a-a_bt)/(a_m-a_bt);t=t*t*(3-2*t);return interp(bt,a_bt)*(1-t)+(R_top(a_m)-0.15)*t+0.15*t*t
    band_in=[(a,mn) for a,mn,mx in full if a>=PHI_END]+[(a,interp(rin,a)) for a in range(14,int(PHI_END))]
    # 1) 頭部（取巻き・中石・頭部下の腕）だけを残し、腕・肩レール・腕石座を削除
    rm=[(abs(p[0])>XH or p[2]<5) for p in P]
    T2=[t for t in T if not(rm[t[0]] or rm[t[1]] or rm[t[2]])]
    V=[];F=[]
    def sweep(a0,a1,fin,fout,wf_,drop,n=60,m=14,caps=True):
        wfun=wf_ if callable(wf_) else (lambda a,_w=wf_:_w);w=wfun(a0)
        base=len(V);prof=[('o',w/2-w*j/m) for j in range(m+1)]+[('i',-w/2+w*j/m) for j in range(m+1)];L=len(prof)
        for k in range(n+1):
            ad=a0+(a1-a0)*k/n;a=math.radians(ad);fa=abs(((ad+180)%360)-180);ri=fin(fa);ro=fout(fa);ww=wfun(fa)
            for t,y0 in prof:
                y=y0*ww/w;u=abs(y)/(ww/2);r=ro-drop*u**2.4 if t=='o' else ri+0.12*u**6
                V.append((r*math.sin(a),y,r*math.cos(a)))
        for k in range(n):
            for j in range(L):
                a_=base+k*L+j;b_=base+k*L+(j+1)%L;F.append((a_,a_+L,b_));F.append((b_,a_+L,b_+L))
        if caps:
            for k,flip in ((0,False),(n,True)):
                ctr=len(V);ring=[base+k*L+j for j in range(L)];V.append(tuple(sum(V[i][q] for i in ring)/L for q in range(3)))
                for j in range(L):
                    f=(ctr,ring[j],ring[(j+1)%L]);F.append(f if not flip else (f[0],f[2],f[1]))
    # 2) 腕：頭部の下から一周（下側で継ぎ目なし）
    a_b=math.degrees(math.asin((XH-0.6)/interp(bt,20)))
    sweep(a_b,360-a_b,lambda a:interp(band_in,a)-0.02,lambda a:band_out(a)+0.02,1.66,0.32,n=240)
    # 3) 甲丸の肩（腕石なし）：頭部側面から腕へ合流
    a_start=rail_top[0][0]-4.5;a_end=a_m+2.0
    def r_in(a):
        if a<=a_bt:return interp(rail_in,a)-0.05
        return band_out(a)-0.45
    def r_out(a):
        return R_top(a)-(0.0 if a<=a_m else 0.06*(a-a_m)/(a_end-a_m))
    for sg in (1,-1):
        f0=len(F);v0=len(V)
        sweep(a_start,a_end,r_in,r_out,lambda a:1.68-0.08*max(0,min(1,(a-a_start)/(a_end-a_start))),0.34,n=90)
        if sg<0:
            for k in range(v0,len(V)):x,y,z=V[k];V[k]=(-x,y,z)
            for k in range(f0,len(F)):a_,b_,c_=F[k];F[k]=(a_,c_,b_)
    # 左右に複製
    # 統合
    off=len(P);allP=P+V;allT=T2+[(a+off,b+off,c+off) for a,b,c in F]
    used=sorted({i for t in allT for i in t});remap={o:i for i,o in enumerate(used)}
    allP=[allP[i] for i in used];allT=[tuple(remap[i] for i in t) for t in allT]
    assert len(allP)<65536
    mn=[min(p[k] for p in allP) for k in range(3)];span=max(max(p[k] for p in allP)-mn[k] for k in range(3));sc=span/65535
    pb=struct.pack('<%dH'%(3*len(allP)),*[max(0,min(65535,round((p[k]-mn[k])/sc))) for p in allP for k in range(3)])
    ib=struct.pack('<%dH'%(3*len(allT)),*[i for t in allT for i in t])
    n=dict(c);n.update(id=c['id']+'B',sku='RB',base=c['id'],arr=True,pos=base64.b64encode(pb).decode(),idx=base64.b64encode(ib).decode(),
        q={'min':mn,'sc':sc},i32=False,tris=len(allT),stones=[s for s in c['stones'] if s not in sh])
    print(c['id'],'removed tris',len(T)-len(T2),'new tris',len(F),'verts',len(allP),'gap_end',phi_gap_end,'stones',len(n['stones']),'rail_top',rail_top)
    return n
out=D+[build(c) for c in D if c['kind']=='RING']
open(dst,'w').write(json.dumps(out,ensure_ascii=False))
