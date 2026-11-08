(() => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const root = document.createElement('div');
  root.innerHTML = `<button id="table-help-toggle" type="button" aria-controls="table-help-panel" aria-expanded="false">Помощник</button>
    <section id="table-help-panel" role="dialog" aria-label="Помощник TABLE" aria-modal="false">
      <header><strong>Помощник TABLE</strong><button id="table-help-close" type="button" aria-label="Закрыть">×</button></header>
      <div id="table-help-messages" role="log" aria-live="polite"></div>
      <form id="table-help-form"><input id="table-help-input" maxlength="500" autocomplete="off" aria-label="Ваш вопрос" placeholder="Вопрос или «забронировать»…" required><button id="table-help-send" type="submit">➤</button></form>
    </section>`;
  document.body.appendChild(root);
  const toggle = root.querySelector('#table-help-toggle'), panel = root.querySelector('#table-help-panel');
  const form = root.querySelector('#table-help-form'), input = root.querySelector('#table-help-input');
  const send = root.querySelector('#table-help-send'), messages = root.querySelector('#table-help-messages');
  const add = (value, mine=false) => { const el=document.createElement('div');el.className='table-help-msg'+(mine?' me':'');el.textContent=value;messages.appendChild(el);messages.scrollTop=messages.scrollHeight; };
  const link = (href, label) => {const a=document.createElement('a');a.href=href;a.textContent=label;a.className='assistant-payment-link';a.style.cssText='display:inline-block;padding:9px 14px;margin:8px 0;background:#2e6552;color:white;border-radius:10px;text-decoration:none';messages.appendChild(a);messages.scrollTop=messages.scrollHeight;};
  const setOpen = value => {panel.classList.toggle('open',value);toggle.setAttribute('aria-expanded',String(value));if(value)input.focus();else toggle.focus();};
  toggle.addEventListener('click',()=>setOpen(!panel.classList.contains('open')));
  root.querySelector('#table-help-close').addEventListener('click',()=>setOpen(false));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&panel.classList.contains('open'))setOpen(false)});
  add('Здравствуйте! Помогу забронировать столик. Напишите «забронировать» — я уточню дату, время, имя, телефон и число гостей. Также отвечаю на вопросы о меню.');
  const fields = ['reservation_date','reservation_time','customer_name','phone','guests'];
  const prompts = ['На какую дату? Введите ГГГГ-ММ-ДД (например, 2026-12-05).','На какое время? Введите ЧЧ:ММ (например, 19:00).','Как вас зовут?','Ваш номер телефона (например, +77071234567)?','Сколько гостей (1–6)?'];
  let booking=null, step=0;
  function validate(field, value) {
    if(field==='reservation_date') {if(!/^\d{4}-\d{2}-\d{2}$/.test(value)||Number.isNaN(new Date(value+'T12:00').getTime()))return false;return true;}
    if(field==='reservation_time')return /^([01]\d|2[0-3]):[0-5]\d$/.test(value);
    if(field==='customer_name')return value.length>=2&&value.length<=50;
    if(field==='phone')return /^\+?[\d\s()\-]{10,20}$/.test(value);
    if(field==='guests')return /^[1-6]$/.test(value);
    return false;
  }
  async function api(url, body){const res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify(body)});return {ok:res.ok,data:await res.json()};}
  form.addEventListener('submit',async e=>{
    e.preventDefault();const question=input.value.trim();if(!question)return;
    add(question,true);input.value='';send.disabled=true;
    try {
      if(booking){
        if(/^(отмена|отменить|cancel)$/i.test(question)){booking=null;add('Оформление отменено.');return;}
        const field=fields[step];
        if(!validate(field,question)){add('Проверьте формат. '+prompts[step]);return;}
        booking[field]=field==='guests'?Number(question):question;
        step++;
        if(step<fields.length){add(prompts[step]);return;}
        const {ok,data}=await api('/api/assistant/book',booking);booking=null;
        if(!ok||!data.success){add(data.message||'Не удалось создать бронирование. Попробуйте снова.');return;}
        if(data.payment_required){add(`Столик найден. Заявка №${data.reservation_id} ожидает демонстрационную предоплату 5 000 ₸. Бронь подтвердится только после оплаты. На оплату даётся 15 минут.`);link(data.payment_url,'Перейти к оплате брони');}
        else add(`Готово! Бронирование №${data.reservation_id} подтверждено. Столик выбран автоматически. Сохраните номер брони.`);
        return;
      }
      if(/(заброн|бронь|запис|reserve|book a table|үстел.*брон)/i.test(question)){
        booking={};step=0;add('Оформим бронь. Для отмены напишите «отмена». '+prompts[0]);return;
      }
      const {data}=await api('/api/assistant',{message:question});add(data.answer||data.message||'Не удалось получить ответ.');
    } catch {add('Нет соединения с сервером. Попробуйте ещё раз.');}
    finally{send.disabled=false;input.focus();}
  });
})();
