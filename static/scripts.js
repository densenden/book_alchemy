document.addEventListener('DOMContentLoaded', function() {
    function loadContent(url, direction) {
        fetch(url)
            .then(response => response.text())
            .then(html => {
                const container = document.getElementById('menu-container');
                container.innerHTML = html;
                container.classList.add(`slide-in-${direction}`);
                const backButton = document.createElement('button');
                backButton.textContent = 'Back';
                backButton.classList.add('back-button');
                backButton.onclick = () => {
                    container.classList.remove(`slide-in-${direction}`);
                    container.classList.add(`slide-out-${direction}`);
                    setTimeout(() => location.reload(), 300);
                };
                container.appendChild(backButton);
            })
            .catch(error => console.warn('Error loading content:', error));
    }

    const covers = document.querySelectorAll('.cover');
    covers.forEach(cover => {
        cover.onload = () => {
            cover.classList.add('cover-loaded');
        };
        // If the image is already cached
        if (cover.complete) {
            cover.classList.add('cover-loaded');
        }
    });

    const lazyImages = document.querySelectorAll('.lazy');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.getAttribute('data-src');
                img.classList.remove('lazy');
                img.classList.add('cover-loaded');
                observer.unobserve(img);
            }
        });
    }, {
        rootMargin: '400px'
    });

    lazyImages.forEach(image => {
        imageObserver.observe(image);
    });
});