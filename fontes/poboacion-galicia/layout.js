const B=__dirname+'/node_modules/';
const {hierarchy}=require(B+'d3-hierarchy');
const {polygonCentroid,polygonArea}=require(B+'d3-polygon');
const {voronoiTreemap}=require(B+'d3-voronoi-treemap');
const seedrandom=require(B+'seedrandom');
const fs=require('fs');
const D=JSON.parse(fs.readFileSync(__dirname+'/data/datos.json'));
const order=['A Coruña','Pontevedra','Ourense','Lugo','Exterior'];
const all=[...D.concellos,...D.exterior];
const root=hierarchy({children:order.map(p=>({n:p,children:all.filter(c=>c.p===p)}))}).sum(d=>d.v||0);
const R=500,N=180,clip=[];
for(let i=0;i<N;i++){const a=-Math.PI/2+i*2*Math.PI/N;clip.push([R*Math.cos(a),R*Math.sin(a)]);}
const seed=process.argv[2]||'galicia';
voronoiTreemap().clip(clip).prng(seedrandom(seed)).convergenceRatio(0.002).maxIterationCount(400).minWeightRatio(0.005)(root);
const r2=v=>Math.round(v*10)/10;
const pts=p=>p.map(q=>r2(q[0])+','+r2(q[1])).join(' ');
// pole of inaccessibility (coarse grid search) for label placement
function inside(p,x,y){let c=false;for(let i=0,j=p.length-1;i<p.length;j=i++){const[a,b]=p[i],[e,f]=p[j];if((b>y)!=(f>y)&&x<(e-a)*(y-b)/(f-b)+a)c=!c;}return c;}
function segd(px,py,a,b){const dx=b[0]-a[0],dy=b[1]-a[1];let t=((px-a[0])*dx+(py-a[1])*dy)/(dx*dx+dy*dy||1);t=Math.max(0,Math.min(1,t));return Math.hypot(px-a[0]-t*dx,py-a[1]-t*dy);}
function pole(p){let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const[x,y]of p){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
 let best=[...polygonCentroid(p),0];const s=Math.max(x1-x0,y1-y0)/24;
 const ev=(x,y)=>{if(!inside(p,x,y))return -1;let d=1e9;for(let i=0;i<p.length;i++)d=Math.min(d,segd(x,y,p[i],p[(i+1)%p.length]));return d;};
 best[2]=ev(best[0],best[1]);
 for(let x=x0;x<=x1;x+=s)for(let y=y0;y<=y1;y+=s){const d=ev(x,y);if(d>best[2])best=[x,y,d];}
 for(let k=0;k<3;k++){const[bx,by]=best,st=s/(2**(k+1));for(let dx=-2;dx<=2;dx++)for(let dy=-2;dy<=2;dy++){const d=ev(bx+dx*st,by+dy*st);if(d>best[2])best=[bx+dx*st,by+dy*st,d];}}
 return best.map(r2);}
let err=0;const tot=root.value,A=polygonArea(clip);
const groups=root.children.map(g=>({n:g.data.n,v:g.value,poly:pts(g.polygon),pole:pole(g.polygon)}));
const cells=root.leaves().map(l=>{const a=Math.abs(polygonArea(l.polygon));err+=Math.abs(a/A-l.value/tot);return {id:l.data.id,n:l.data.n,p:l.data.p,v:l.data.v,poly:pts(l.polygon),pole:pole(l.polygon)};});
console.error('seed',seed,'total abs area error',err.toFixed(4));
fs.writeFileSync(__dirname+'/data/layout.json',JSON.stringify({R,anoPadron:D.anoPadron,anoPERE:D.anoPERE,groups,cells}));
