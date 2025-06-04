// Espera a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.hero-btn');

    // Agrega una animación al hacer hover en los botones
    buttons.forEach(button => {
        button.addEventListener('mouseenter', () => {
            button.classList.add('animate');
        });

        button.addEventListener('mouseleave', () => {
            button.classList.remove('animate');
        });
    });

    // Efecto de entrada para el título
    const title = document.querySelector('.hero-title');
    if (title) {
        title.classList.add('fade-in');
    }
});


document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.btn');

    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            btn.style.transform = 'scale(1.05)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'scale(1)';
        });
    });
});
