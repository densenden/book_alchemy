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

document.addEventListener('DOMContentLoaded', function() {
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

    // Hide .message elements after 5 seconds
    setTimeout(function() {
        const messages = document.querySelectorAll('.message');
        messages.forEach(message => {
            message.style.display = 'none';
        });
    }, 5000); // 5000 milliseconds = 5 seconds

    document.addEventListener('keydown', function(event) {
    if (event.key === 'ArrowLeft') {
        const prevButton = document.querySelector('.arrow.book[onclick*="prev_book_id"]');
        if (prevButton && prevButton.style.visibility !== 'hidden') {
            prevButton.click();
        } else {
            const prevAuthorButton = document.querySelector('.arrow.author[onclick*="prev_author_id"]');
            if (prevAuthorButton && prevAuthorButton.style.visibility !== 'hidden') {
                prevAuthorButton.click();
            }
        }
    } else if (event.key === 'ArrowRight') {
        const nextButton = document.querySelector('.arrow.book[onclick*="next_book_id"]');
        if (nextButton && nextButton.style.visibility !== 'hidden') {
            nextButton.click();
        } else {
            const nextAuthorButton = document.querySelector('.arrow.author[onclick*="next_author_id"]');
            if (nextAuthorButton && nextAuthorButton.style.visibility !== 'hidden') {
                nextAuthorButton.click();
            }
        }
    }
});

});