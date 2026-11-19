from pathlib import Path
import json,math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ezdxf
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
from shapely.geometry import Point,Polygon,LineString
from shapely.affinity import scale,rotate,translate
from shapely.ops import unary_union,nearest_points
OUT=Path(__file__).resolve().parents[1]; OUT.mkdir(parents=True,exist_ok=True)
def ell(cx,cy,rx,ry): return translate(scale(Point(0,0).buffer(1,resolution=128),rx,ry),cx,cy)
def leaf(cx,cy,rx,ry,a): return rotate(ell(cx,cy,rx,ry),a,origin=(cx,cy))
def line(points,w): return LineString(points).buffer(w/2,cap_style=1,join_style=1)
panel=Point(0,0).buffer(290,resolution=256); ring=panel.difference(panel.buffer(-17))
# Accurate top-view turtle anatomy.
shell=ell(0,0,124,158)
head=ell(0,180,42,49)
neck=ell(0,145,35,50)
tail=Polygon([(-18,-145),(18,-145),(0,-202)])
flippers=unary_union([
 leaf(-170,72,55,130,-58),leaf(170,72,55,130,58),
 leaf(-153,-92,42,90,-123),leaf(153,-92,42,90,123)
])
material=unary_union([ring,shell,head,neck,tail,flippers])
# Shell scute apertures: central rosette, rings, and side plates.
cuts=[]
# Top-view face: two eyes and paired nostrils, without a cartoon mouth.
cuts += [ell(-16,188,4,7),ell(16,188,4,7),ell(-7,211,2.5,4),ell(7,211,2.5,4)]
# Central shell column.
for y,rx,ry in [(102,26,20),(55,31,23),(5,34,25),(-47,31,23),(-96,25,20)]:
 cuts.append(leaf(0,y,rx,ry,0))
# Side shell plates.
for s in (-1,1):
 for y,rx,ry,a in [(92,22,29,28),(42,24,32,35),(-12,24,33,42),(-65,22,29,48),(-108,18,24,55)]:
  cuts.append(leaf(s*64,y,rx,ry,s*a))
 # flipper streamlines
 cuts += [leaf(s*171,78,13,42,s*58),leaf(s*185,48,10,30,s*61),
          leaf(s*153,-94,11,34,s*123)]
# Small shell crown and tail accents.
cuts += [leaf(-29,131,12,22,-25),leaf(29,131,12,22,25),leaf(0,-133,16,17,0)]
ap=unary_union(cuts).intersection(material.buffer(-5))
ap_parts=list(ap.geoms) if hasattr(ap,'geoms') else [ap]
for _ in range(150):
 best=None
 for i,a in enumerate(ap_parts):
  for j in range(i+1,len(ap_parts)):
   d=a.distance(ap_parts[j])
   if d<4.1 and (best is None or d<best[0]): best=(d,i,j)
 if best is None: break
 _,i,j=best; a,b=ap_parts[i],ap_parts[j]; pa,pb=nearest_points(a,b)
 bridge=LineString([(pa.x,pa.y),(pb.x,pb.y)]).buffer(2.05,cap_style=1)
 merged=unary_union([a,b,bridge]).buffer(0)
 ap_parts=[g for k,g in enumerate(ap_parts) if k not in (i,j)]+[merged]
ap=unary_union(ap_parts)
# Select a symmetric mounting pair with maximum clearance in the widened rim.
best_mount=None
for deg in range(18,163):
 rad=math.radians(deg); x=281.5*math.cos(rad); y=281.5*math.sin(rad)
 if abs(x)<90 or y<70: continue
 hs=[Point(x,y).buffer(4,resolution=48),Point(-x,y).buffer(4,resolution=48)]
 if not all(h.within(material) for h in hs): continue
 score=min(min(h.distance(material.boundary),h.distance(ap)) for h in hs)
 if best_mount is None or score>best_mount[0]: best_mount=(score,x,y,hs)
if best_mount is None or best_mount[0]<4.1: raise RuntimeError('No valid symmetric mounting pair found')
mount_score,mount_x,mount_y,mount_geoms=best_mount
mounts=unary_union(mount_geoms)
material=material.difference(unary_union([ap,mounts]))
parts=list(material.geoms) if hasattr(material,'geoms') else [material]
if len(parts)!=1: raise RuntimeError(f'{len(parts)} disconnected components')
material=parts[0]
# Production outputs.
doc=ezdxf.new('R2010'); doc.units=ezdxf.units.MM; doc.layers.add('CUT',color=7); msp=doc.modelspace()
def coords(poly): return [(round(x,4),round(y,4)) for x,y in list(poly.exterior.coords)[:-1]]
msp.add_lwpolyline(coords(material),close=True,dxfattribs={'layer':'CUT'})
for r in material.interiors: msp.add_lwpolyline(coords(Polygon(r)),close=True,dxfattribs={'layer':'CUT'})
doc.saveas(OUT/'original-ornamental-sea-turtle-panel.dxf')
def pd(r):
 pts=[(x+300,300-y) for x,y in list(r.coords)[:-1]]
 return 'M '+' L '.join(f'{x:.3f},{y:.3f}' for x,y in pts)+' Z'
d=' '.join([pd(material.exterior)]+[pd(r) for r in material.interiors])
(OUT/'original-ornamental-sea-turtle-panel.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="600mm" height="600mm" viewBox="0 0 600 600"><path d="{d}" fill="#111" fill-rule="evenodd"/></svg>\n')
def mp(poly):
 v=[]; c=[]
 for r in [poly.exterior,*poly.interiors]:
  pts=list(r.coords); v.extend(pts); c.extend([MplPath.MOVETO]+[MplPath.LINETO]*(len(pts)-2)+[MplPath.CLOSEPOLY])
 return MplPath(v,c)
fig,ax=plt.subplots(figsize=(8,8.7),dpi=190); fig.patch.set_facecolor('#eee8df'); ax.set_facecolor('#eee8df')
ax.add_patch(PathPatch(mp(material),facecolor='#171819',edgecolor='#090909',lw=.55))
ax.set_xlim(-305,305); ax.set_ylim(-325,315); ax.set_aspect('equal'); ax.axis('off')
ax.text(0,-316,'ORIGINAL ORNAMENTAL SEA TURTLE  •  Ø580 mm  •  2 mm STEEL',ha='center',va='bottom',fontsize=8,color='#4e4a45',weight='bold')
fig.savefig(OUT/'original-ornamental-sea-turtle-preview.jpg',bbox_inches='tight',facecolor=fig.get_facecolor()); plt.close(fig)
holes=[Polygon(r) for r in material.interiors]; mg=999.0; pair=None
for i,a in enumerate(holes):
 for j in range(i+1,len(holes)):
  dd=a.distance(holes[j])
  if dd<mg: mg=dd; pair=[i,j]
mass=material.area*2*7.85e-6
centers=[[round(h.centroid.x,2),round(h.centroid.y,2)] for h in holes]
metrics={'diameter_mm':580.0,'thickness_mm':2.0,'material':'mild steel','connected_components':1,'geometry_valid':material.is_valid,'closed_profiles':1+len(material.interiors),'decorative_apertures':len(material.interiors)-2,'mounting_holes':2,'mounting_hole_diameter_mm':8.0,'mounting_centers_mm':[[round(-abs(mount_x),2),round(mount_y,2)],[round(abs(mount_x),2),round(mount_y,2)]],'minimum_profile_separation_mm':round(mg,3),'minimum_gap_pair':pair,'minimum_gap_centers':[centers[i] for i in pair] if pair else None,'area_mm2':round(material.area,2),'cut_length_mm':round(material.length,2),'mass_kg':round(mass,4),'cut_price_at_2_usd_per_kg':round(mass*2,2)}
(OUT/'geometry-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics))
