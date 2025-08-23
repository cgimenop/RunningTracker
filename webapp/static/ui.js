function toggleSection(header) {
    const content = header.nextElementSibling;
    const icon = header.querySelector('.toggle-icon');

    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.textContent = '▼';
        header.classList.remove('collapsed');
    } else {
        content.style.display = 'none';
        icon.textContent = '▶';
        header.classList.add('collapsed');
    }
}

function openDetailSection(date) {
    // Open main Detailed Data section
    const detailedDataSection = Array.from(document.querySelectorAll('.section-header')).find(h =>
        h.querySelector('span').textContent.trim() === 'Detailed Data'
    );

    if (detailedDataSection) {
        const mainContent = detailedDataSection.nextElementSibling;
        mainContent.style.display = 'block';
        detailedDataSection.querySelector('.toggle-icon').textContent = '▼';
        detailedDataSection.classList.remove('collapsed');
    }

    // Open specific date section
    const targetSection = document.getElementById('detail-' + date.replace(/-/g, ''));
    if (targetSection) {
        const header = targetSection.querySelector('.section-header');
        const content = header.nextElementSibling;
        content.style.display = 'block';
        header.querySelector('.toggle-icon').textContent = '▼';
        header.classList.remove('collapsed');
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Initialize collapsed state
document.addEventListener('DOMContentLoaded', function() {
    const sections = document.querySelectorAll('.section-content');
    sections.forEach(function(section) {
        const header = section.previousElementSibling;
        if (!header.hasAttribute('data-open')) {
            section.style.display = 'none';
            const icon = header.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = '▶';
            }
            header.classList.add('collapsed');
        } else {
            section.style.display = 'block';
        }
    });
});