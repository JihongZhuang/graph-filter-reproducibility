"""Publication vector PDFs from the same native object inventory and frozen data."""
import argparse
import os
from pathlib import Path
from math import atan2,cos,sin,pi
from statistics import median
import json
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--font-dir',type=Path,default=Path(os.environ.get('WINDIR','/usr/share'))/'Fonts')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
OUT=args.output
OUT.mkdir(parents=True,exist_ok=False)
INV=json.loads((ROOT/'results/figure_inventory.json').read_text(encoding='utf-8'))
DATA=json.loads((ROOT/'results/figure_source_data.json').read_text(encoding='utf-8'))
C={'ink':'#1A1A1A','blue':'#0072B2','orange':'#D55E00','gray':'#666666','line':'#888888'}
SCALE=183/25.4*72/1800
def PT(v):return v/SCALE
for name,file,index in [('Arial','arial.ttf',0),('ArialBold','arialbd.ttf',0),('Math','cambria.ttc',1)]:
    pdfmetrics.registerFont(TTFont(name,str(args.font_dir/file),subfontIndex=index))

def font_for(ch,font):
    return font if ord(ch) in pdfmetrics.getFont(font).face.charToGlyph else 'Math'

def sw(t,size,font='Arial'):
    return sum(pdfmetrics.stringWidth(ch,font_for(ch,font),size) for ch in t)

class Figure:
    def __init__(self,n,height=1050):
        self.h=height
        self.c=Canvas(str(OUT/f'figure{n}.pdf'),pagesize=(1800*SCALE,height*SCALE),pageCompression=1,initialFontName='Arial',initialFontSize=6.5)
        self.c.setTitle(INV[n-1]['title']);self.c.setAuthor('');self.c.setCreator('Original vector research figures')
        self.c.scale(SCALE,SCALE)
    def line(self,x1,y1,x2,y2,color=C['ink'],width=2,dash=None):
        c=self.c;c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.setDash(dash or [])
        c.line(x1,self.h-y1,x2,self.h-y2);c.setDash([])
    def text(self,t,x,y,size=30,color=C['ink'],bold=False,align='left',font=None):
        f=font or ('ArialBold' if bold else 'Arial');w=sw(t,size,f)
        if align=='center':x-=w/2
        elif align=='right':x-=w
        self.c.setFillColor(HexColor(color))
        for ch in t:
            ff=font_for(ch,f);self.c.setFont(ff,size);self.c.drawString(x,self.h-y,ch);x+=pdfmetrics.stringWidth(ch,ff,size)
    def rect(self,x,y,w,h,fill=None,stroke=None,lw=2):
        c=self.c;c.setFillColor(HexColor(fill or '#FFFFFF'));c.setStrokeColor(HexColor(stroke or '#FFFFFF'));c.setLineWidth(lw)
        c.rect(x,self.h-y-h,w,h,fill=int(bool(fill and fill!='none')),stroke=int(bool(stroke and stroke!='none')))
    def point(self,x,y,symbol,color,r=7):
        c=self.c;c.setFillColor(HexColor(color));c.setStrokeColor(HexColor(color))
        if symbol=='circle':c.circle(x,self.h-y,r,fill=1,stroke=0)
        elif symbol=='square':c.rect(x-r,self.h-y-r,2*r,2*r,fill=1,stroke=0)
        else:
            p=c.beginPath();p.moveTo(x,self.h-y+r);p.lineTo(x+r,self.h-y);p.lineTo(x,self.h-y-r);p.lineTo(x-r,self.h-y);p.close();c.drawPath(p,fill=1,stroke=0)
    def finish(self):self.c.showPage();self.c.save()

def method():
    f=Figure(1,890)
    for o in INV[0]['objects']:
        kind=o['type']
        if kind=='connector':
            a,b=o['from'],o['to'];x1,y1=a['left']+a['width'],a['top']+a['height']/2;x2,y2=b['left'],b['top']+b['height']/2
            if o['kind']=='elbow':
                xx=(x1+x2)/2;f.line(x1,y1,xx,y1,o['color'],1.7);f.line(xx,y1,xx,y2,o['color'],1.7);f.line(xx,y2,x2,y2,o['color'],1.7)
            else:f.line(x1,y1,x2,y2,o['color'],1.7)
            f.c.setFillColor(HexColor(o['color']));q=f.c.beginPath();q.moveTo(x2,f.h-y2);q.lineTo(x2-13,f.h-y2+6);q.lineTo(x2-13,f.h-y2-6);q.close();f.c.drawPath(q,fill=1,stroke=0)
            continue
        if kind=='rect':f.rect(o['x'],o['y'],o['w'],o['h'],o['fill'],o['stroke'],o['lw'])
        if 'text' in o:
            lines=o['text'].split('\n');size=o['size'];leading=size*1.16
            for j,line in enumerate(lines):
                yy=o['y']+o['h']/2-(len(lines)-1)*leading/2+j*leading+size*.34
                xx=o['x']+({'left':0,'center':o['w']/2,'right':o['w']}[o['align']])
                f.text(line,xx,yy,size,o['color'],o['bold'],o['align'],'Math' if o['font']=='Cambria Math' else None)
    f.finish()

def panel(f,key,title,x,y):
    f.text(key,x,y+34,PT(8),bold=True);f.text(title,x+51,y+34,PT(7),bold=True)

def resources():
    f=Figure(2)
    specs=[('a','Yelp','yelp_f5','time',28,0,18,5),('b','Amazon-book','amazon_f2','time',945,0,40,10),
           ('c','Yelp','yelp_f5','peak',28,510,550,100),('d','Amazon-book','amazon_f2','peak',945,510,750,200)]
    for key,title,cfg,field,x,y,ymax,step in specs:
        panel(f,key,title,x,y)
        f.text('Time (min)' if field=='time' else 'Peak process memory (MiB)',x+85,y+79,PT(6.5))
        left,top,w,h=x+160,y+110,650,340;bottom=top+h
        xx=lambda v:left+(v-.5)/3*w
        yy=lambda v:bottom-v/ymax*h
        for value in range(0,ymax+1,step):
            gy=yy(value);f.line(left-7,gy,left,gy,C['ink'],1.7);f.text(f'{value:.2f}',left-15,gy+7,PT(6.2),C['ink'],align='right')
        f.line(left,top,left,bottom,C['ink'],1.7)
        groups=[('author_snapshot',64,C['blue'],'circle','Released'),('author_snapshot',32,C['gray'],'diamond','Released'),('streaming_direct',64,C['orange'],'square','Direct')]
        for g,(method,batch,col,marker,label) in enumerate(groups):
            record=next(z for z in DATA if z.get('panel')==key and z.get('method')==method and z.get('batch')==batch)
            vals=record['values_full_precision']
            for i,v in enumerate(vals):f.point(xx(g+1+(i-2)*.06),yy(v),marker,col,5)
            f.line(xx(g+.8),yy(median(vals)),xx(g+1.2),yy(median(vals)),C['ink'],1.8)
            f.text(f'{median(vals):.2f}',xx(g+1),yy(max(vals))-23,PT(6.2),align='center')
            f.text(label,xx(g+1),y+492,PT(6.2),align='center');f.text('b = '+str(batch),xx(g+1),y+522,PT(6.2),align='center')
    f.finish()

def quality():
    f=Figure(3,785)
    panel(f,'a','Recall@20 difference (percentage points)',245,15)
    panel(f,'b','Top20 set overlap (%)',1165,15)
    left,top,w,h=265,180,730,455;bottom=top+h
    xx=lambda v:left+(v+.2)/.25*w
    yy=lambda v:bottom-(v-.5)/2*h
    f.line(left,bottom,left+w,bottom,C['ink'],1.7)
    f.line(xx(0),top,xx(0),bottom,C['gray'],1.4,[6,6])
    for tick in [-.2,-.15,-.1,-.05,0,.05]:
        f.line(xx(tick),bottom,xx(tick),bottom+7,C['ink'],1.7);f.text(f'{tick:.2f}',xx(tick),bottom+35,PT(6.2),align='center')
    for i,cfg in enumerate(['yelp_f5','amazon_f2']):
        r=next(x for x in DATA if x.get('figure')==3 and x.get('config')==cfg);y=yy(2-i);lo,hi=r['CI_full_precision']
        f.text('Yelp' if i==0 else 'Amazon-book',220,y-4,PT(6.5),bold=True,align='right')
        f.text('n = '+f"{r['users']:,}",220,y+26,PT(6.1),align='right')
        f.line(xx(lo),y,xx(hi),y,C['ink'],1.8);f.line(xx(lo),y-10,xx(lo),y+10,C['ink'],1.5);f.line(xx(hi),y-10,xx(hi),y+10,C['ink'],1.5)
        f.point(xx(r['mean_full_precision']),y,'circle',C['ink'],5)
        f.text(f"{r['mean_full_precision']:.2f}",xx(r['mean_full_precision']),y-30,PT(6.2),align='center')
    f.text('Direct − released; conditional 95.00% iid-user intervals',left+w/2,742,PT(6.2),align='center')
    bleft,bw=1170,560
    bx=lambda v:bleft+v/100*bw
    f.line(bleft,bottom,bleft+bw,bottom,C['ink'],1.7)
    for tick in [0,25,50,75,100]:
        gx=bx(tick);f.line(gx,bottom,gx,bottom+7,C['ink'],1.7);f.text(f'{tick:.2f}',gx,bottom+35,PT(6.2),align='center')
    for i,cfg in enumerate(['yelp_f5','amazon_f2']):
        r=next(x for x in DATA if x.get('figure')==3 and x.get('config')==cfg);v=r['overlap_percent_full_precision'];y=yy(2-i)
        f.point(bx(v),y,'circle',C['ink'],5);f.text(f'{v:.2f}',bx(v),y-30,PT(6.2),align='center')
    f.text('100.00% = identical sets',bleft+bw/2,742,PT(6.2),align='center')
    f.finish()

if __name__=='__main__':
    method();resources();quality()
    print('Three vector PDFs written from frozen data and editable object inventory.')
