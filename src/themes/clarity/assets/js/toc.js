document.addEventListener('DOMContentLoaded', function () {
    const toc = document.getElementById('toc');
    const tocSection = toc && (toc.closest('.col-md-4') || document.getElementById('toc-section'));

    if (!toc || !tocSection) {
        return;
    }

    const headings = document.querySelectorAll('#main_article h2');

    if (headings.length === 0) {
        tocSection.remove();
        return;
    }

    headings.forEach(function (heading, index) {
        if (!heading.id) {
            heading.id = 'heading' + index;
        }

        const title = heading.cloneNode(true);
        title.querySelectorAll('sup, a:not([href])').forEach(function (el) { el.remove(); });

        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = '#' + heading.id;
        a.setAttribute('aria-describedby', 'toc-title');
        a.textContent = title.textContent.trim();
        a.addEventListener('click', function (e) {
            e.preventDefault();
            heading.scrollIntoView({ behavior: 'smooth', block: 'start' });
            history.pushState(null, '', '#' + heading.id);
        });

        li.appendChild(a);
        toc.appendChild(li);
    });
});
