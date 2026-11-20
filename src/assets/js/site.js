(function(){
  var root=document.documentElement;
  var btn=document.querySelector('.theme-toggle');
  if(btn){btn.addEventListener('click',function(){
    var dark=root.dataset.theme==='dark'||(root.dataset.theme!=='light'&&matchMedia('(prefers-color-scheme: dark)').matches);
    root.dataset.theme=dark?'light':'dark';
    try{localStorage.setItem('theme',root.dataset.theme)}catch(e){}
  });}
  document.querySelectorAll('.copy').forEach(function(b){
    b.addEventListener('click',function(){
      var txt=b.getAttribute('data-copy'),label=b.textContent;
      if(navigator.clipboard){navigator.clipboard.writeText(txt).then(function(){b.textContent=b.getAttribute('data-done');setTimeout(function(){b.textContent=label},1600)})}
    });
  });
  var box=document.querySelector('.lang-suggest');
  if(box){
    var pageLang=box.dataset.lang,nav=(navigator.language||'en').slice(0,2),dismissed=false;
    try{dismissed=localStorage.getItem('lang-dismissed')==='1'}catch(e){}
    if(!dismissed&&nav!==pageLang&&(nav==='it'||nav==='en')){
      var msg=nav==='it'?'Questa pagina è disponibile in italiano.':'This page is available in English.';
      var link=nav==='it'?'Apri':'Open';
      box.innerHTML='<span>'+msg+'</span> <a href="'+box.dataset.other+'" hreflang="'+nav+'">'+link+'</a><button type="button" aria-label="Close">×</button>';
      box.hidden=false;
      box.querySelector('button').addEventListener('click',function(){box.hidden=true;try{localStorage.setItem('lang-dismissed','1')}catch(e){}});
    }
  }
})();
