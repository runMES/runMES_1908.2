from django.urls import path
from modeling import views

urlpatterns = [
  path('',views.modeling_home,name='modeling_home'),
  path('home/',views.modeling_home,name='modeling_home'),
  path('dc_category/',views.dc_category,name='dc_category'),
  path('dc_item/',views.dc_item,name='dc_item'),
  path('dc_spec/',views.dc_spec,name='dc_spec'),
  path('dc_plan/',views.dc_plan,name='dc_plan'),
  path('area/',views.model_area,name='model_area'),
  path('eq_group/',views.model_eq_group,name='model_eq_group'),
  path('eq/',views.model_eq,name='model_eq'),
  path('lot_record/',views.lot_record,name='lot_record'),
  path('eq_record/',views.eq_record,name='eq_record'),
  path('bin_grade/',views.bin_grade,name='bin_grade'),
  path('binning/',views.binning,name='binning'),
  path('breaking/',views.breaking,name='breaking'),
  path('step_category/',views.step_category,name='step_category'),
  path('process_step/',views.process_step,name='process_step'),
  path('process/',views.process,name='process'),
  path('product/',views.product,name='product'),
  path('bonus_scrap/',views.bonus_scrap,name='bonus_scrap'),
  path('lot_hold_release/',views.lot_hold_release,name='lot_hold_release'),
  path('eq_hold_release/',views.eq_hold_release,name='eq_hold_release'),
  path('user_account/',views.user_account,name='user_account'),
]
