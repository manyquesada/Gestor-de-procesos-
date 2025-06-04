document.addEventListener('DOMContentLoaded', () => {
  // Confirmación de eliminación de documentos
  document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const confirmado = confirm("¿Estás seguro que deseas eliminar este documento?");
      if (!confirmado) e.preventDefault();
    });
  });

  // Inicializar tooltips de Bootstrap
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
