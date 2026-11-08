document.addEventListener('DOMContentLoaded', () => {
  const cards = [...document.querySelectorAll('.reservation-card')];
  const buttons = [...document.querySelectorAll('[data-history-filter]')];
  buttons.forEach(button => button.addEventListener('click', () => {
    const mode = button.dataset.historyFilter;
    const now = new Date();
    buttons.forEach(b => { const active = b === button; b.classList.toggle('is-active', active); b.setAttribute('aria-pressed', String(active)); });
    cards.forEach(card => {
      const when = new Date(`${card.dataset.bookingDate}T${card.dataset.bookingTime || '00:00'}:00`);
      const status = card.dataset.bookingStatus;
      const upcoming = when >= now && ['confirmed','arrived'].includes(status);
      card.hidden = mode === 'upcoming' ? !upcoming : mode === 'history' ? upcoming : false;
    });
  }));
});
