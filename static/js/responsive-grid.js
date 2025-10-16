function setupResponsiveShowcase(showcase) {
    const cards = showcase.querySelectorAll('.news-post-item');
    const buttonContainer = showcase.nextElementSibling;

    // Exit if there are no cards or a button container to manage
    if (cards.length === 0 || !buttonContainer) return;

    const showMoreBtn = buttonContainer.querySelector('.show-more-btn');
    const showLessBtn = buttonContainer.querySelector('.show-less-btn'); // This might be null

    // --- Core function to hide/show cards ---
    const updateVisibleCards = () => {
        cards.forEach(card => card.style.display = 'block');
        if (cards.length === 0) return;

        const firstCardTop = cards[0].offsetTop;
        let hiddenCount = 0;

        cards.forEach(card => {
            if (card.offsetTop > firstCardTop) {
                card.style.display = 'none';
                hiddenCount++;
            }
        });

        // Show the button container only if cards are actually hidden
        if (hiddenCount > 0) {
            buttonContainer.classList.remove('initially-hidden');
            if (showMoreBtn) showMoreBtn.style.display = 'inline-block';
            // FIX: Only try to hide the "Show Less" button if it exists
            if (showLessBtn) showLessBtn.style.display = 'none';
        } else {
            buttonContainer.classList.add('initially-hidden');
        }
    };

    // --- Event Listeners for Buttons ---
    if (showMoreBtn) {
        // Only add a click listener if it's a true "show more" button (i.e., has a "show less" counterpart)
        // Otherwise, it's just a link to another page, and we let the browser handle it.
        if (showLessBtn) {
            showMoreBtn.addEventListener('click', () => {
                cards.forEach(card => card.style.display = 'block');
                showMoreBtn.style.display = 'none';
                showLessBtn.style.display = 'inline-block';
            });
        }
    }

    // FIX: Only add a listener for the "Show Less" button if it exists
    if (showLessBtn) {
        showLessBtn.addEventListener('click', () => {
            updateVisibleCards();
            showcase.parentElement.querySelector('h2').scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Initial run and setup resize listener
    updateVisibleCards();
    window.addEventListener('resize', updateVisibleCards);
}

// Run the setup for each showcase on the page
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.post-showcase').forEach(setupResponsiveShowcase);
});