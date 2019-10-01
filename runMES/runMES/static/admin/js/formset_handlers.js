(function ($) {
  $(document).ready(function () {
    $("select").change(function () {
      s_name = this.name;
      //alert('select name:' + s_name);
      var parse_item_specs = s_name.split('-')[2];
      if (parse_item_specs == 'dcitems') {
        var parse_id = s_name.split('-')[1];
        //alert('item id:' + parse_id);
        i_id = this.value
        //alert('select id:' + i_id);
        var item_name = $(this).children("option:selected").text();
        //alert('selected item - ' + item_name);
        var data = {"i_id":i_id};
        $.get("/query_item_spec/",data, function(e) {
          //alert('return data:'+e);
          var spec_id = "select#id_dcplandcitem_set-" + parse_id + "-dcitem_spec";
          $(spec_id).html(e);
        });
        // var new_opt = "<option value selected>--------</option>" +
        //   "<option value=" + s_id + ">" + item_name + "-spec1</option>";
        // alert('new opt - ' + new_opt);
      }
    });

  });
})(django.jQuery);