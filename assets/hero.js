(() => {
  'use strict';
  const canvas = document.getElementById('terrain');
  const ctx = canvas.getContext('2d');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!ctx) return;
  let width=0, height=0, raf=0;
  function resize() {
    const rect=canvas.getBoundingClientRect();
    const ratio=Math.min(window.devicePixelRatio||1,2);
    width=rect.width; height=rect.height;
    canvas.width=Math.max(1,Math.floor(width*ratio));
    canvas.height=Math.max(1,Math.floor(height*ratio));
    ctx.setTransform(ratio,0,0,ratio,0,0);
  }
  const particles=Array.from({length:65},(_,i)=>({
    x:(Math.sin((i+1)*127.1)*43758.5453)%1,
    y:(Math.sin((i+1)*311.7)*43758.5453)%1,
    size: i%7===0?2.1:1.05,
    speed:.3+((i*17)%9)/23,
    phase:i*.72
  })).map(p=>({...p,x:Math.abs(p.x),y:Math.abs(p.y)}));
  function render(t) {
    ctx.clearRect(0,0,width,height);
    // La zone éclairée à droite évoque une topographie routière, sans simuler de données.
    const base=width*.61, span=width*.42;
    for(let i=0;i<8;i++) {
      ctx.beginPath();
      const shift=i*32;
      for(let x=base-70;x<width+20;x+=5){
        const nx=(x-base)/Math.max(1,span);
        const y=height*.15 + i*21 + Math.sin(nx*7.3+i*.64+(reduceMotion?0:t*.00012))*(17+i*2.8);
        x===base-70?ctx.moveTo(x,y):ctx.lineTo(x,y);
      }
      ctx.strokeStyle=`rgba(112,232,226,${.06+i*.013})`;
      ctx.lineWidth=1;ctx.stroke();
    }
    particles.forEach(p=>{
      const x=base+p.x*span, y=p.y*height;
      const phase=reduceMotion?1:0.65+.35*Math.sin(t*.0007*p.speed+p.phase);
      ctx.beginPath();ctx.arc(x,y,p.size,0,2*Math.PI);
      ctx.fillStyle=`rgba(134,232,233,${phase*.6})`;ctx.fill();
    });
    if (!reduceMotion) raf=requestAnimationFrame(render);
  }
  resize(); render(0);
  window.addEventListener('resize',resize);
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden){cancelAnimationFrame(raf);}
    else if(!reduceMotion){raf=requestAnimationFrame(render);}
  });
})();
