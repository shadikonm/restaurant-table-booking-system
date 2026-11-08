/* CSRF for existing forms and fetch requests without changing button handlers. */
(() => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    const token = meta ? meta.content : '';
    if (!token) return;
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('form').forEach(form => {
            if ((form.method || 'GET').toUpperCase() !== 'POST') return;
            if (form.querySelector('input[name="csrf_token"]')) return;
            const hidden = document.createElement('input');
            hidden.type = 'hidden'; hidden.name = 'csrf_token'; hidden.value = token;
            form.appendChild(hidden);
        });
    });
    const originalFetch = window.fetch.bind(window);
    window.fetch = (resource, options = {}) => {
        const method = (options.method || (resource instanceof Request ? resource.method : 'GET')).toUpperCase();
        const url = new URL(resource instanceof Request ? resource.url : String(resource), location.href);
        if (url.origin !== location.origin || !['POST','PUT','PATCH','DELETE'].includes(method)) {
            return originalFetch(resource, options);
        }
        const headers = new Headers(resource instanceof Request ? resource.headers : undefined);
        new Headers(options.headers || {}).forEach((v,k) => headers.set(k,v));
        headers.set('X-CSRF-Token', token);
        return originalFetch(resource, {...options, headers});
    };
})();
