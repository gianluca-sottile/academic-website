(function(){
  var form=document.querySelector('.filters');
  if(!form)return;
  form.hidden=false;
  var items=[].slice.call(document.querySelectorAll('.pubs-page .pub'));
  var groups=[].slice.call(document.querySelectorAll('.year-group'));
  var shown=form.querySelector('[data-shown]'),empty=document.querySelector('.pubs-page .empty');
  var q=form.elements.q,type=form.elements.type,theme='';
  items.forEach(function(li){li._text=li.textContent.toLowerCase()});
  function readHash(){var m=location.hash.match(/theme=([\w-]+)/);theme=m?m[1]:'';}
  function apply(){
    var term=q.value.trim().toLowerCase(),t=type.value,n=0;
    items.forEach(function(li){
      var ok=(!term||li._text.indexOf(term)>-1)&&(!t||li.dataset.type===t)&&(!theme||(' '+li.dataset.themes+' ').indexOf(' '+theme+' ')>-1);
      li.hidden=!ok;if(ok)n++;
    });
    groups.forEach(function(g){g.hidden=!g.querySelector('.pub:not([hidden])')});
    shown.textContent=n;empty.hidden=n>0;
    form.querySelectorAll('[data-theme-id]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.themeId===theme))});
  }
  form.addEventListener('input',apply);
  form.addEventListener('submit',function(e){e.preventDefault()});
  form.querySelectorAll('[data-theme-id]').forEach(function(b){b.addEventListener('click',function(){
    theme=b.dataset.themeId;history.replaceState(null,'',theme?'#theme='+theme:location.pathname);apply();
  })});
  window.addEventListener('hashchange',function(){readHash();apply()});
  readHash();apply();
})();
