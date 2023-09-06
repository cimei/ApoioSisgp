

$(document).ready(function() {
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
  const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))


  var $table = $('#table')
  $table.bootstrapTable('destroy').bootstrapTable({
      icons: {
          paginationSwitchDown: 'fa-caret-square-down',
          paginationSwitchUp: 'fa-caret-square-up',
          refresh: 'fa-sync',
          toggleOff: 'fa-toggle-off',
          toggleOn: 'fa-toggle-on',
          columns: 'fa fa-th-list',
          fullscreen: 'fa-arrows-alt',
          detailOpen: 'fa-plus',
          detailClose: 'fa-minus',
          clearSearch: 'fa fa-trash'
        }
  })


});

function deleta_pg(url, id){
  Swal.fire({
    title: 'Deseja realmente deletar este Programa de Gestão??',
    showCancelButton: true,
    confirmButtonText: 'Sim',
  }).then((result) => {
    if (result.isConfirmed) {
      $.ajax({
        method: "POST",
        url: url
      })
        .done(function( msg ) {
          $("#tr_"+id).hide()
          Swal.fire('Excluido!', '', 'success')
        });
    }
  })
}