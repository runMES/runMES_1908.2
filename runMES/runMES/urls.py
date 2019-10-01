"""runMES URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from runMES import views
from django.views.generic.base import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
  #path('', views.acc_login,name='acc_login'),
  #path('accounts/', django.contrib.auth.views.login_required(),{'template_name':'runMES/login.html'}),
  #path('logout/', views.acc_logout),
  path('i18n/', include('django.conf.urls.i18n')),
  path('', views.home, name='home'),
  path('admin/', admin.site.urls),
  path('accounts/',include('django.contrib.auth.urls')),
  path('change_password/',views.change_password,name='change_password'),
  path('query_item_spec/',views.query_item_spec,name='query_item_spec'),
  path('home/', views.home, name='home'),
  path('runMES/home/', views.home, name='home'),
  path('test/', views.test, name='test'),
  path('lang/ZH/', views.set_lang_TZ, name='set_lang_TZ'),
  path('lang/CN/', views.set_lang_CN, name='set_lang_CN'),
  path('lang/EN/', views.set_lang_EN, name='set_lang_EN'),
  path('lot/<int:pk>/list', views.lot_detail_dt, name='lot_detail_dt'),
  path('lot/', views.lot_list_query, name='lot_list_query'),
  path('lot/finished/', views.lot_finish_list_query, name='lot_finish_list_query'),
  path('lot/finished/<int:pk>/', views.lot_detail, name='lot_detail'),
  path('lot/shipped/', views.lot_ship_list_query, name='lot_ship_list_query'),
  path('lot/shipped/<int:pk>/', views.lot_detail, name='lot_detail'),
  path('lot/terminated/', views.lot_term_list_query, name='lot_term_list_query'),
  path('lot/terminated/<int:pk>/', views.lot_detail, name='lot_detail'),
  path('lot/lot_dc_hist_query/', views.lot_dc_hist_query, name='lot_dc_hist_query'),
  path('lot_list_link/', views.lot_list_link_query, name='lot_list_link_query'),
  path('lot_list_link/<int:pk>/', views.lot_detail_dt, name='lot_detail_dt'),
  path('lot/<int:pk>/', views.lot_detail, name='lot_detail'),
  path('lot/lot_info/', views.lot_info, name='lot_info'),
  path('lot/lot_hist/', views.lot_hist_query, name='lot_hist_query'),
  path('lot/lot_query_eq/', views.lot_query_eq, name='lot_query_eq'),
  path('lot/lot_query_dc/', views.lot_query_dc, name='lot_query_dc'),
  path('lot/lot_query_dc/lot_dc/', views.lot_dc, name='lot_dc'),
  path('lot/lot_query_bin/', views.lot_query_bin, name='lot_query_bin'),
  path('lot/lot_query_bin/lot_bin/', views.lot_bin, name='lot_bin'),
  path('lot/lot_breaking/',views.lot_breaking,name='lot_breaking'),
  path('lot/step_in/', views.lot_step_in, name='lot_step_in'),
  path('lot/eq_step_in_query/', views.eq_step_in_query, name='eq_step_in_query'),
  path('lot/eq_step_in/', views.eq_step_in, name='eq_step_in'),
  #path('lot/step_in_test/', views.lot_step_in_test, name='lot_step_in_test'),
  path('lot/step_out/', views.lot_step_out, name='lot_step_out'),
  path('lot/lot_record/', views.lot_record, name='lot_record'),
  path('lot/lot_record/record_dc/', views.record_dc, name='record_dc'),
  path('lot/lot_hold/', views.lot_hold, name='lot_hold'),
  path('lot/lot_release/', views.lot_release, name='lot_release'),
  path('lot/lot_hold_release_hist/', views.lot_hold_release_hist, name='lot_hold_release_hist'),
  path('lot/lot_bonus/', views.lot_bonus, name='lot_bonus'),
  path('lot/lot_scrap/', views.lot_scrap, name='lot_scrap'),
  path('lot/lot_bonus_scrap_hist/', views.lot_bonus_scrap_hist, name='lot_bonus_scrap_hist'),
  path('lot/ctrl_state/', views.lot_ctrl_state, name='lot_ctrl_state'),
  path('lot/lot_ship/', views.lot_ship, name='lot_ship'),
  path('lot/lot_split/', views.lot_split, name='lot_split'),
  path('lot/lot_merge/', views.lot_merge, name='lot_merge'),
  path('lot/lot_split_merge_hist/', views.lot_split_merge_hist, name='lot_split_merge_hist'),
  path('lot/change_product/',views.change_product,name='change_product'),
  path('lot/priority_change/',views.lot_priority_change,name='lot_priority_change'),
  path('eq/eq_hold/', views.eq_hold, name='eq_hold'),
  path('eq/eq_record/', views.eq_record, name='eq_record'),
  path('eq/eq_record_query/', views.eq_record_query, name='eq_record_query'),
  path('eq/eq_record/eq_dc/', views.record_eq, name='record_eq'),
  path('eq/eq_record/eq_record_history/', views.eq_record_hist, name='eq_record_hist'),
  path('eq/eq_release/', views.eq_release, name='eq_release'),
  path('eq/<int:pk>/status', views.EqStatusUpdate.as_view(), name='eq-detail'),
  path('eq/', views.eq_list_query, name='eq_list_query'),
  path('eq/<int:pk>/', views.eq_detail, name='eq_detail'),
  path('eq/eq_query_lot/', views.eq_query_lot, name='eq_query_lot'),
  path('eq/state/', views.eq_ctrl_state, name='eq_ctrl_state'),
  path('lot/lot_run_card/', views.lot_run_card, name='lot_run_card'),
  path('lot_start/',views.lot_start,name='lot_start'),
  path('lot_start/lot_add/',views.lot_start_add,name='lot_start_add'),
  path('lot_start_batch_query/',views.lot_start_batch_query,name='lot_start_batch_query'),
  path('lot_start_batch_query/lot_start_batch/',views.lot_start_batch,name='lot_start_batch'),
  path('work_order/',views.work_order,name='work_order'),
  path('work_order_query/',views.work_order_query,name='work_order_query'),
  path('work_order_query/<int:pk>/',views.work_order_detail,name='work_order_detail'),
  path('work_order/work_order_import',views.upload_csv,name='upload_csv'),
  path('CFM/',views.cfm,name='cmf'),
  path('CFM/cfm_ajax/',views.cfm_ajax,name='cmf_ajax'),
  path('modeling/',include('modeling.urls')),
  path('test/', views.test, name='test'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
