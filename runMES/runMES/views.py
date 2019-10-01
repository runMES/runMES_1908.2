from django.db import transaction
from django.shortcuts import render
from runMES import forms
from runMES import trans
from runMES.models import *
from django.views.generic.edit import UpdateView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.translation import activate
from django.utils.translation import gettext as _
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from datetime import datetime
import uuid
import logging
from MQTT import log_runMES
import csv
import time
import threading
import json
import redis

mylog=logging.getLogger('runMES')
# Create your views here.

version='19.08.2'
lastupdate='2019/09/13'
note='runMES (Manufacturing Execution System)'
cp_right='©2019 StepTech Systems'
default_lang='tz'

def red_font(msg):
  return format_html('<span style="color: #cc0033; font-weight: bold;">{0}</span>',msg)

def green_font(msg):
  return format_html('<span style="color: #00802b; font-weight: bold;">{0}</span>',msg)

def yellow_font(msg):
  return format_html('<span style="color: #cccc00f; font-weight: bold;">{0}</span>',msg)

def blue_font(msg):
  return format_html('<span style="color: #0059b3; font-weight: bold;">{0}</span>',msg)

def purple_font(msg):
  return format_html('<span style="color: #660033; font-weight: bold;">{0}</span>',msg)

def grey_font(msg):
  return format_html('<span style="color: #a6a6a6; font-weight: bold;">{0}</span>',msg)

def orange_font(msg):
  return format_html('<span style="color: #f99006; font-weight: bold;">{0}</span>',msg)

def lot_job():
  v_name='lot_job'
  lot_timer=settings.LOT_TIMER
  try:
    rs0=redis.Redis(db=0)
    rs1=redis.Redis(db=1)
    mylog.info({'views':v_name,'status':'started'})

    while True:
      lot_list=Lot.objects.exclude(ctrl_state='T').exclude(ctrl_state='S').exclude(ctrl_state='F')
      rs0.set('lot_wait',1)
      rs1.flushdb()
      for l in lot_list:
        field_set=['id','name','product','workorder','lot_type','curr_eq','lot_priority','process_step','step_recipe','step_check','step_dcplan','step_breaking','step_binning','is_hold','ctrl_state','next_operation','qty']
        f_set=[]
        for f in field_set:
          f_set.append(str(getattr(l,f)))
        rs1.set(str(l),str(f_set))

      rs0.set('lot_wait',0)
      time.sleep(lot_timer)

  except Exception as e:
    mylog.exception(e)

def cfm_job():
  v_name='cfm_job'
  cfm_timer=settings.CFM_TIMER
  try:
    rs=redis.Redis(db=2)
    mylog.info({'views':v_name,'cfm_job':'started'})
    while True:
      eq_set=Eq.objects.all()
      for e in eq_set:
        lot_set=Lot.objects.filter(curr_eq=e)
        lot_list=''
        eq_info=[]
        if lot_set:
          for l in lot_set:
            lot_list=lot_list+' '+l.name
        eq_info.append(e.name)
        eq_info.append(e.ctrl_state)
        eq_info.append(str(e.is_hold))
        if e.last_recipe:
          eq_info.append(e.last_recipe)
        else:
          eq_info.append('')
        if e.last_product:
          eq_info.append(e.last_product.name)
        else:
          eq_info.append('')

        eq_info.append(lot_list)

        rs.set(e.name,str(eq_info))
        #log_runMES.to_debug({'views':v_name,'EQ_info':str(eq_info)})

      time.sleep(cfm_timer)

  except Exception as e:
    mylog.exception(e)

def cfm(request):
  v_name='cfm'
  #global cfm_flag

  try:
    if request.method=='GET':
      #log_runMES.to_debug({'views':v_name,'request':request.method})
      if request.session['lang']:
        activate(request.session['lang'])
      else:
        activate(default_lang)

      load_title='EQ Realtime Monitoring'
      eq_states=[]
      eq_states.append({'name':red_font('DM'),'val':'Down'})
      eq_states.append({'name':blue_font('RA'),'val':'Run Available'})
      eq_states.append({'name':green_font('RN'),'val':'Run Not Available'})
      eq_states.append({'name':yellow_font('ID'),'val':'Idle'})
      eq_states.append({'name':purple_font('PM'),'val':'PM'})
      eq_states.append({'name':grey_font('LN'),'val':'Lend'})
      eq_states.append({'name':orange_font('SU'),'val':'Setup'})

      return render(request,'runMES/dt_auto_refresh.html',{'load_title':load_title,'eq_states':eq_states})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def cfm_ajax(request):
  v_name='cfm_ajax'
  rs=redis.Redis(db=2)
  #log_runMES.to_debug({'views':v_name,'request':'ajax'})
  try:
    # field_set=['name','ctrl_state','is_hold','last_recipe','last_product','lot_list']
    # load_title='EQ List Query'
    eq_set=Eq.objects.all().order_by('name')
    mylist=[]
    for e in eq_set:
      #log_runMES.to_debug({'views':v_name,'eq':e.name})
      if rs.get(e.name):
        rec=rs.get(e.name)
        #log_runMES.to_debug({'views':v_name,'rec':rec})
        record=eval(rec)
        cnt=0
        dic={}
        for item in record:
          #(('RA','Run Available'),('RN','Run Not Available'),('PM','Maintenance'),('ID','Idle'),('DM','Down'),('LN','Lend'),('SU','Setup'))
          if item=='True':
            item=red_font(item)
          if item=='RA':
            item=blue_font(item)
          if item=='RN':
            item=green_font(item)
          if item=='ID':
            item=yellow_font(item)
          if item=='LN':
            item=grey_font(item)
          if item=='PM':
            item=purple_font(item)
          if item=='DM':
            item=red_font(item)
          if item=='SU':
            item=orange_font(item)
          #log_runMES.to_debug({'views':v_name,'item':item})
          dic[str(cnt)]=item
          cnt=cnt+1

        mylist.append(dic)
        #log_runMES.to_debug({'views':v_name,'dic':dic})

      #log_runMES.to_debug({'views':v_name,'list':mylist})
    json_data=json.dumps(mylist,sort_keys='ID')
    #log_runMES.to_debug({'views':v_name,'json_data':json_data})

    return HttpResponse(json_data,content_type='application/json')

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def change_password(request):
  v_name='change_password'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.ChangePWDForm(request.POST)
      if form.is_valid():
        name=form.cleaned_data['name']
        old_pwd=form.cleaned_data['old_pwd']
        new_pwd=form.cleaned_data['new_pwd'].strip()
        log_runMES.to_debug({'views':v_name,'new_pwd':new_pwd})
        if new_pwd:
          au=authenticate(username=name,password=old_pwd)
          if au:
            u=User.objects.get(username=name)
            u.set_password(new_pwd)
            u.save()
            info={'User':request.user,'Change Password':_('Succeed')}
          else:
            info={'User':request.user,'ERR':red_font(_('Old Password Incorrect'))}
        else:
          info={'User':request.user,'ERR':red_font(_('New Password Incorrect'))}
      else:
        info=form.errors

      log_runMES.to_debug(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

    else:
      form=forms.ChangePWDForm(initial={'name':str(request.user)})
      form.fields['name'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Change Password','form':form,'username':str(request.user)})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

# for admin dcplan js
def query_item_spec(request):
  v_name='query_item_spec'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    print({'view':'query_item_spec','request':request})
    item_id=request.GET.get('i_id')
    print({'view':'query_item_spec','item_id':item_id})
    pre_opt="<option value selected>--------</option>"
    if item_id:
      item_obj=DcItem.objects.get(pk=int(item_id))
      result=DcItemSpec.objects.filter(dcitem=item_obj,freeze=True).order_by('name')
      print({'view':'query_item_spec','result':result})
      my_opt=''
      for r in result:
        my_opt=my_opt+"<option value="+str(r.pk)+">"+r.name+"</option> "

      my_opt=pre_opt+my_opt
      print({'view':'query_item_spec','my_opt':my_opt})
      # my_opt='<option value selected>--------</option><option value=2>item2-spec1</option>'
      return HttpResponse(my_opt)

      # myhttp=HttpResponse(serializers.serialize('json',result))
      # print({'view':'query_item_spec','myhttp':myhttp})
      # return HttpResponse(serializers.serialize('json',result))
    return HttpResponse(pre_opt)
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def home(request):
  v_name='home'
  mylog.debug({'views':v_name,'user':request.user,'request':request})
  try:
    request.session['lang']=default_lang
    activate(default_lang)
    return render(request,'runMES/home.html',{'version':version,'lastupdate':lastupdate,'note':note,'copyright':cp_right,'base':'base.html'})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def set_lang_TZ(request):
  v_name='set_lang_TZ'
  try:
    log_runMES.to_debug({'views':'set_lang_TZ'})
    request.session['lang']='tz'
    activate('tz')
    return render(request,'runMES/home.html',{'version':version,'lastupdate':lastupdate,'note':note,'copyright':cp_right,'base':'base.html'})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def set_lang_CN(request):
  v_name='set_lang_CN'
  try:
    log_runMES.to_debug({'views':'set_lang_CN'})
    request.session['lang']='cn'
    activate('cn')
    return render(request,'runMES/home.html',{'version':version,'lastupdate':lastupdate,'note':note,'copyright':cp_right,'base':'base.html'})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def set_lang_EN(request):
  v_name='set_lang_EN'
  try:
    log_runMES.to_debug({'views':'set_lang_EN'})
    request.session['lang']='en'
    activate('en')
    return render(request,'runMES/home.html',{'version':version,'lastupdate':lastupdate,'note':note,'copyright':cp_right,'base':'base.html'})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
def test(request):
  if request.session['lang']:
    activate(request.session['lang'])

  info={'ETX':'ETX message',red_font('ERR'):red_font('test red fonts')}
  return render(request,'runMES/return_info.html',{'load_title':'Testing','info':info,'timestamp':timezone.now()})

def lot_detail_dt(request,pk):
  v_name='lot_detail_dt'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    # log_runMES.to_debug("in lot_detail_dt")
    # data table column titles
    field_set=['id','name','product','curr_eq','process_step','step_recipe','step_dcplan','is_hold','is_finish','ctrl_state','next_operation']
    # query_tbl_by_fields_w_filter(txt_table_name,set_fields,txt_filter_field,any_filter_val)
    reply=trans.tx_query_tbl_by_fields_w_filter('Lot',field_set,'id',pk)
    # log_runMES.to_debug('reply:'+str(reply))
    data_set=reply['DATA_SET'][0]
    # rotate row and column
    new_data=[]
    length=len(field_set)
    i=0
    while i<length:
      new_data.append([field_set[i],data_set[i]])
      # log_runMES.to_debug({'views':'lot_detail_dt','new_data':new_data})
      i=i+1
    col_set=['Item','Values']
    load_title='Lot Detail'
    return render(request,'runMES/dt_clean_form.html',{'load_title':load_title,'col':col_set,'row':new_data})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
def lot_detail(request,pk):
  v_name='lot_detail'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    mylot=get_object_or_404(Lot,pk=pk)
    if mylot:
      form=forms.LotInfoForm(instance=mylot)
      for f in form.fields:
        # log_runMES.to_debug({'view':'lot_detail','f':f})
        form.fields[f].widget.attrs['readonly']=True

      return render(request,'runMES/comm_detail.html',{'load_title':'Lot Detail','form':form})
    else:
      return render(request,'runMES/return_info.html',{'info':{'views':'lot_detail','ECD':'E12','ETX':red_font(_('Lot Not Exist'))},'timestamp':timezone.now()})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_info(request):
  v_name='lot_info'
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    log_runMES.to_debug({'views':'lot_info','lang':request.session['lang']})
    mylot=request.POST['lot_field']
    try:
      if Lot.objects.filter(name=mylot):
        lot_obj=Lot.objects.get(name=mylot)
        form=forms.LotInfoForm(instance=lot_obj)
        for f in form.fields:
          # log_runMES.to_debug({'view':'lot_detail','f':f})
          form.fields[f].widget.attrs['readonly']=True

        return render(request,'runMES/comm_detail_plan.html',{'load_title':v_name,'form':form})
      else:
        return render(request,'runMES/return_info.html',
                      {'info':{'views':v_name,'ECD':'E12','ETX':red_font(_('Lot Not Exist')),'LOT':mylot},'timestamp':timezone.now()})
    except Exception as e:
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Error':red_font(e),'LOT':mylot},'timestamp':timezone.now()})
  else:
    return render(request,'runMES/lot_info.html')

@login_required
def eq_detail(request,pk):
  v_name='eq_detail'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    myeq=get_object_or_404(Eq,pk=pk)
    if myeq:
      form=forms.EqInfoForm(instance=myeq)
      for f in form.fields:
        # log_runMES.to_debug({'view':'eq_detail','f':f})
        form.fields[f].widget.attrs['readonly']=True

      return render(request,'runMES/comm_detail.html',{'load_title':'EQ Detail','form':form})
    else:
      return render(request,'runMES/return_info.html',
                    {'load_title':'EQ Detail','info':{'ECD':'E12','ETX':red_font(_('Lot Not Exist'))},'timestamp':timezone.now()})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_hold(request):
  v_name='lot_hold'
  group=request.user.groups.values_list('name',flat=True)
  mylog.debug({'views':v_name,'group':group})
  try:
    v_name='lot_hold'
    if 'Super' not in group:
      mylog.debug({'views':v_name,'group':group,'Super':False})
      return HttpResponseRedirect(reverse('home'))
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotHoldForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        if not Lot.objects.filter(name=lot):
          return render(request,'runMES/return_info.html',
                        {'info':{'views':v_name,'ECD':'E12','ETX':red_font(_('Lot Not Exist')),'LOT':lot},'timestamp':timezone.now()})
        hold_code=form.cleaned_data['hold_code'].name
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        # tx_lot_hold(lot_txt,op_txt,is_hold_bool,hold_code_txt,release_code_txt,annotation_txt):
        reply=trans.tx_lot_hold(lot,op,True,hold_code,'',annotation)
        # log_runMES.to_debug(reply)
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))
        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'HOLD_CODE':hold_code,'OP':op}

        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.LotHoldForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/lot_hold.html',{'form':form,'username':str(request.user)})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_release(request):
  v_name='lot_release'
  try:
    v_name='lot_release'
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotReleaseForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot'].name
        release_code=form.cleaned_data['release_code'].name
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        # tx_lot_hold(lot_txt,op_txt,is_hold_bool,hold_code_txt,release_code_txt,annotation_txt):
        reply=trans.tx_lot_hold(lot,op,False,'',release_code,annotation)
        # log_runMES.to_debug(reply)
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))
        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'RELEASE_CODE':release_code,'OP':op}

        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.LotReleaseForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/lot_release.html',{'form':form,'username':str(request.user)})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_bonus(request):
  v_name='lot_bonus'
  try:
    v_name='lot_bonus'
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.BonusForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        if not Lot.objects.filter(name=lot):
          return render(request,'runMES/return_info.html',
                        {'info':{'views':v_name,'ECD':'E12','ETX':red_font(_('Lot Not Exist')),'LOT':lot},'timestamp':timezone.now()})
        qty=form.cleaned_data['qty']
        code=form.cleaned_data['bonus_code'].name
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        # tx_bonus_scrap(lot_txt,qty_int,bonus_scrap_txt,code_txt,op_txt,annotation_txt):
        reply=trans.tx_bonus_scrap(lot,qty,'B',code,op,annotation)
        log_runMES.to_debug({'views':v_name,'reply':reply})
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          old_etx=reply['ETX']
          etx=_(old_etx)
          log_runMES.to_debug({'views':v_name,'etx':etx})
          if ecd is not '0':
            etx=red_font(etx)

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'QTY':qty,'CODE':code,'OP':op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.BonusForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Bonus','form':form,'username':str(request.user)})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_scrap(request):
  v_name='lot_scrap'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.ScrapForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        qty=form.cleaned_data['qty']
        code=form.cleaned_data['scrap_code'].name
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        # tx_bonus_scrap(lot_txt,qty_int,bonus_scrap_txt,code_txt,op_txt,annotation_txt):
        reply=trans.tx_bonus_scrap(lot,qty,'S',code,op,annotation)
        # log_runMES.to_debug(reply)
        return render(request,'runMES/return_info.html',{'info':reply,'timestamp':timezone.now()})
    else:
      form=forms.ScrapForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Scrap','form':form,'username':str(request.user)})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_ship(request):
  v_name='lot_ship'
  try:
    v_name='lot_ship'
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotShipForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        lot_set=Lot.objects.filter(name=lot)
        if not lot_set:
          info={'ECD':'L12','ETX':red_font(_('Lot Not Exist')),'LOT':lot}
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
        if lot_set[0].ctrl_state!='F':
          info={'ECD':'L01','ETX':red_font(_('Lot State Mismatch')),'LOT':lot,'STATE':lot_set[0].ctrl_state}
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        # tx_lot_ship(lot_txt,op_txt,anno_txt):
        reply=trans.tx_lot_ship(lot,op,annotation)
        # log_runMES.to_debug(reply)
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          old_etx=reply['ETX']
          etx=_(old_etx)
          log_runMES.to_debug({'views':v_name,'etx':etx})
          if ecd is not '0':
            etx=red_font(etx)

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'OP':op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.LotShipForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Ship','form':form,'username':str(request.user)})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def eq_hold(request):
  v_name='eq_hold'
  try:
    v_name='eq_hold'
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.EqHoldForm(request.POST)
      if form.is_valid():
        eq=form.cleaned_data['eq']
        hold_code=form.cleaned_data['hold_code'].name
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        if not Eq.objects.filter(name=eq):
          info={'views':v_name,'ECD':'E05','ETX':red_font(_('EQ Not Exist')),'EQ':eq,'OP':op}
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

        # tx_eq_hold(eq_txt,op_txt,is_hold_bool,hold_code_txt,release_code_txt,annotation_txt):
        reply=trans.tx_eq_hold(eq,op,True,hold_code,'',annotation)
        # log_runMES.to_debug(reply)
        log_runMES.to_debug({'view':v_name,'reply':reply})
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          old_etx=reply['ETX']
          etx=_(old_etx)
          log_runMES.to_debug({'views':v_name,'etx':etx})
          if ecd is not '0':
            etx=red_font(etx)

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'EQ':eq,'OP':op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.EqHoldForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/eq_hold.html',{'form':form,'timestamp':timezone.now()})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def eq_release(request):
  v_name='eq_release'
  try:
    v_name='eq_release'
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.EqReleaseForm(request.POST)
      if form.is_valid():
        eq=form.cleaned_data['eq'].name
        release_code=form.cleaned_data['release_code'].name
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']

        if not Eq.objects.filter(name=eq):
          info={'views':v_name,'ECD':'E05','ETX':red_font(_('EQ Not Exist')),'EQ':eq,'OP':op}
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

        # tx_eq_hold(eq_txt,op_txt,is_hold_bool,hold_code_txt,release_code_txt,annotation_txt):
        reply=trans.tx_eq_hold(eq,op,False,'',release_code,annotation)
        log_runMES.to_debug({'view':'eq_release','reply':reply})
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          old_etx=reply['ETX']
          etx=_(old_etx)
          log_runMES.to_debug({'views':v_name,'etx':etx})
          if ecd is not '0':
            etx=red_font(etx)

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'EQ':eq,'OP':op}

        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.EqReleaseForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/eq_release.html',{'form':form})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def eq_ctrl_state(request):
  v_name='eq_ctrl_state'
  try:
    v_name='eq_ctrl_state'
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.EqCtrlStateForm(request.POST)
      if form.is_valid():
        eq=form.cleaned_data['eq']
        state=form.cleaned_data['ctrl_state']
        op=form.cleaned_data['op']
        anno=form.cleaned_data['annotation']
        # tx_eq_change_state(eq_txt,state_txt)
        reply=trans.tx_eq_change_state(eq,state,op,anno)
        # log_runMES.to_debug({'views':v_name,'reply':reply})
        etx=''
        err=''
        ecd=''

        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))
        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'EQ':eq,'STATE':state,'OP':op}
        log_runMES.to_debug(info)
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.EqCtrlStateForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'EQ Control State','form':form,'base':'modeling_base.html'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_query_eq(request):
  v_name='lot_query_eq'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    # log_runMES.to_debug({'views':'lot_query_eq'})
    if request.method=='POST':
      lot=request.POST['lot_field']
      reply=trans.qry_lot_query_eq(lot)
      etx=''
      err=''
      ecd=''
      if 'ERR' in reply:
        err=red_font(reply['ERR'])
      if 'ECD' in reply:
        ecd=reply['ECD']
      if 'ETX' in reply:
        etx=reply['ETX']
        if ecd is not '0':
          etx=red_font(_(etx))
      info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot}
      if reply['ECD']!='0':
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      # log_runMES.to_debug('lot:' + str(lot))
      log_runMES.to_debug({'views':'lot_query_eq','reply':reply})
      eqobj_list=reply['EQ_LIST']
      field_set=['name','description','eq_type','parent','area','group','ctrl_state','is_hold','is_virtual','active']
      data_set=[]
      for eq in eqobj_list:
        f_set=[]
        for f in field_set:
          f_set.append(getattr(eq,f))
        data_set.append(f_set)

      log_runMES.to_debug({'views':'lot_query_eq','EQ LIST':data_set})
      load_title='Available EQ List'
      return render(request,'runMES/dt_clean_form.html',{'load_title':load_title,'col':field_set,'row':data_set})

    else:
      return render(request,'runMES/lot_query_eq.html')

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def eq_query_lot(request):
  v_name='eq_query_lot'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    log_runMES.to_debug({'views':'eq_query_lot'})

    if request.method=='POST':
      eq=request.POST['eq_field']
      op=str(request.user)
      reply=trans.qry_eq_query_lot(eq,op)
      etx=''
      err=''
      ecd=''
      if 'ERR' in reply:
        err=red_font(reply['ERR'])
      if 'ECD' in reply:
        ecd=reply['ECD']
      if 'ETX' in reply:
        etx=reply['ETX']
        if ecd is not '0':
          etx=red_font(_(etx))
      info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'EQ':eq,'OP':op}

      if reply['ECD']!='0':
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      # log_runMES.to_debug('lot:' + str(lot))
      log_runMES.to_debug({'views':'lot_query_eq','reply':reply})
      lot_list=reply['LOT_LIST']
      field_set=['name','product','workorder','curr_eq','lot_priority','process_step','step_recipe','step_check','step_dcplan','step_breaking','step_binning','is_hold','ctrl_state','next_operation','qty']
      dt_field_set=['name','product','WO','curr_eq','priority','Step','recipe','Check','DC','Break','Bin','hold','state','next','qty']
      data_set=[]
      for l in lot_list:
        lot_obj=Lot.objects.get(name=l)
        f_set=[]
        for f in field_set:
          f_set.append(getattr(lot_obj,f))
        data_set.append(f_set)

      load_title='Available Lot List'
      return render(request,'runMES/dt_clean_form.html',{'load_title':load_title,'col':dt_field_set,'row':data_set})

    else:
      return render(request,'runMES/eq_query_lot.html')

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_query_dc(request):
  v_name='lot_query_dc'
  if request.session['lang']:
    activate(request.session['lang'])
  log_runMES.to_debug("in lot_query_dc")
  if request.method=='POST':
    log_runMES.to_debug("In POST")
    lot=request.POST['lot_field']
    eq=request.POST['eq_field']
    op=str(request.user)
    try:
      lot_obj=Lot.objects.get(name=lot)
      dc_plan=lot_obj.step_dcplan
      if dc_plan is '' or dc_plan is None:
        info={'views':v_name,'ECD':'D01','ETX':_('Data Collection Not Exist'),'LOT':lot}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      eq_obj=lot_obj.curr_eq
      if eq_obj.name!=eq:
        info={'views':v_name,'ECD':'L09','ETX':_('Lot Not In EQ'),'LOT':lot,'EQ':eq}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      if dc_plan and eq_obj:
        # tx_dcplan_find_dcitem(dcplan_name_txt,op_txt):
        reply=trans.qry_dcplan_item(dc_plan,op)
        # log_runMES.to_debug({'dcitem':reply})
        dcitem_count=reply['DCITEM_COUNT']
        dcitem_set=reply['DCITEM_SET']
        log_runMES.to_debug({'view':v_name,'dcitem_set':dcitem_set})
        return render(request,'runMES/lot_dc.html',{'dcitem_set':dcitem_set,'dc_plan':dc_plan,'lot':lot,'eq':eq_obj.name,'op':op})

    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e,'lot':lot}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

  else:
    return render(request,'runMES/lot_query_dc.html')

@login_required
@csrf_exempt
def lot_dc(request):
  v_name='lot_dc'
  log_runMES.to_debug({'views':v_name,'user':str(request.user)})
  if request.session['lang']:
    activate(request.session['lang'])
  op=str(request.user)
  log_runMES.to_debug({'views':v_name,'op':op})
  if request.method=='POST':
    # log_runMES.to_debug({'views':'lot_dc','POST':request.POST})
    mydict=dict(request.POST)
    log_runMES.to_debug({'views':'lot_dc','dict':mydict})
    lot=mydict['lot'][0]
    dcplan=mydict['dc_plan'][0]
    eq=mydict['eq'][0]
    anno=mydict['anno_field'][0]
    dc_itemset=[]
    cnt=0
    for name in mydict['item_name']:
      item={}
      item['item_name']=mydict['item_name'][cnt]
      item['category']=mydict['category'][cnt]
      item['unit']=mydict['unit'][cnt]
      item['data_type']=mydict['data_type'][cnt]
      item['val']=mydict['val'][cnt]
      dc_itemset.append(item)
      cnt=cnt+1

    log_runMES.to_debug({'views':v_name,'item_set':dc_itemset})
    try:
      # tx_dc(lot_txt,eq_txt,dcplan_txt,item_set,op_txt,anno_txt):
      reply=trans.tx_dc(lot,eq,dcplan,dc_itemset,op,anno)
      log_runMES.to_debug({'views':v_name,'tx_dc':reply})
      etx=''
      err=''
      ecd=''
      oos=''
      next_op=''
      if 'ERR' in reply:
        err=red_font(reply['ERR'])
      if 'ECD' in reply:
        ecd=reply['ECD']
      if 'ETX' in reply:
        etx=reply['ETX']
        if ecd is not '0':
          etx=red_font(_(etx))
      if 'OOS' in reply:
        if reply['OOS']!='':
          oos=red_font(reply['OOS'])
      if 'NEXT_OP' in reply:
        next_op=reply['NEXT_OP']
      info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'EQ':eq,'OOS':oos,'NEXT_OP':next_op,'OP':op}
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    except Exception as e:
      mylog.exception(e)
      mylog.error({'views':v_name,'ERR':e})
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

# def lot_list_query(request):
#   v_name='lot_list_query'
#   try:
#     if request.session['lang']:
#       activate(request.session['lang'])
#     log_runMES.to_info({'views':'lot_list_query'})
#     mylog.debug({'views':v_name,'before':str(datetime.now())})
#     field_set=['id','name','product','workorder','lot_type','curr_eq','lot_priority','process_step','step_recipe','step_check','step_dcplan','step_breaking','step_binning','is_hold','ctrl_state','next_operation','qty']
#     dt_field_set=['id','name','product','WO','type','curr_eq','priority','Step','recipe','Check','DC','Break','Bin','hold','state','next','qty']
#     data_set=[]
#     lot_list=Lot.objects.exclude(ctrl_state='T').exclude(ctrl_state='S')
#     for l in lot_list:
#       f_set=[]
#       for f in field_set:
#         f_set.append(getattr(l,f))
#       data_set.append(f_set)
#     mylog.debug({'views':v_name,'before':str(datetime.now())})
#     load_title='Lot List Query'
#     return render(request,'runMES/dt_navbar_form.html',{'load_title':load_title,'col':dt_field_set,'row':data_set})
#   except Exception as e:
#     mylog.exception(e)
#     return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def lot_list_query(request):
  v_name='lot_list_query'
  dt_field_set=['id','name','product','WO','type','curr_eq','priority','Step','recipe','Check','DC','Break','Bin','hold','state','next','qty']
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    log_runMES.to_info({'views':'lot_list_query'})
    data_set=[]
    rs0=redis.Redis(db=0)
    cnt=0
    while eval(rs0.get('lot_wait')):
      time.sleep(1)
      cnt=cnt+1
      if cnt > settings.LOT_LIST_TIMEOUT:
        return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':'Lots Query Timeout'},'timestamp':timezone.now()})

    r1=redis.Redis(db=1)
    lot_list=[]
    for l in r1.scan_iter():
      lot_list.append(l)
    lot_list.sort()

    for l in lot_list:
      lot=r1.get(l.decode('utf-8'))
      if lot:
        f_set=[]
        field_set=eval(lot)

        for f in field_set:
          f_set.append(f)
        data_set.append(f_set)
    #mylog.debug({'views':v_name,'after':str(datetime.now())})
    load_title='Lot List Query(WIP)'
    return render(request,'runMES/dt_navbar_form.html',{'load_title':load_title,'col':dt_field_set,'row':data_set})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def lot_finish_list_query(request):
  v_name='lot_finish_list_query'
  try:
    log_runMES.to_info({'views':v_name})
    if request.session['lang']:
      activate(request.session['lang'])
    field_set=['id','name','product','workorder','lot_type','curr_eq','process_step','step_recipe','step_check','step_dcplan','step_breaking','step_binning',
               'is_hold','ctrl_state','next_operation','qty']
    dt_field_set=['id','name','product','WO','type','curr_eq','Step','recipe','Check','DC','Break','Bin','hold','state','next','qty']
    data_set=[]
    lot_list=Lot.objects.filter(ctrl_state='F')
    for l in lot_list:
      f_set=[]
      for f in field_set:
        f_set.append(getattr(l,f))
      data_set.append(f_set)

    load_title='Lot List Query(Finished)'
    return render(request,'runMES/dt_navbar_form.html',{'load_title':load_title,'col':dt_field_set,'row':data_set})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})


def lot_ship_list_query(request):
  v_name='lot_ship_list_query'
  try:
    log_runMES.to_info({'views':'lot_ship_list_query'})
    if request.session['lang']:
      activate(request.session['lang'])
    field_set=['id','name','product','workorder','lot_type','curr_eq','process_step','step_recipe','step_check','step_dcplan','step_breaking','step_binning',
               'is_hold','ctrl_state','next_operation','qty']
    dt_field_set=['id','name','product','WO','type','curr_eq','Step','recipe','Check','DC','Break','Bin','hold','state','next','qty']
    data_set=[]
    lot_list=Lot.objects.filter(ctrl_state='S')
    for l in lot_list:
      f_set=[]
      for f in field_set:
        f_set.append(getattr(l,f))
      data_set.append(f_set)

    load_title='Lot List Query(Shipped)'
    return render(request,'runMES/dt_navbar_form.html',{'load_title':load_title,'col':dt_field_set,'row':data_set})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def lot_term_list_query(request):
  v_name='lot_term_list_query'
  try:
    log_runMES.to_info({'views':'lot_term_list_query'})
    if request.session['lang']:
      activate(request.session['lang'])
    field_set=['id','name','product','workorder','lot_type','curr_eq','process_step','step_recipe','step_check','step_dcplan','step_breaking','step_binning',
               'is_hold','ctrl_state','next_operation','qty']
    dt_field_set=['id','name','product','WO','type','curr_eq','Step','recipe','Check','DC','Break','Bin','hold','state','next','qty']
    data_set=[]
    lot_list=Lot.objects.filter(ctrl_state='T')
    for l in lot_list:
      f_set=[]
      for f in field_set:
        f_set.append(getattr(l,f))
      data_set.append(f_set)

    load_title='Lot List Query(Terminated)'
    return render(request,'runMES/dt_navbar_form.html',{'load_title':load_title,'col':dt_field_set,'row':data_set})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def lot_list_link_query(request):
  v_name='lot_list_link_query'
  try:
    log_runMES.to_info({'views':"lot_list_link_query"})
    if request.session['lang']:
      activate(request.session['lang'])
    # data table column titles
    field_set=['id','name','product','curr_eq','process_step','step_recipe','step_dcplan','step_binning','is_hold','is_finish','ctrl_state','next_operation']
    # query_tbl_by_fields_w_filter(table_obj,set_fields,txt_filter_field,any_filter_val):
    reply=trans.tx_query_tbl_by_fields_w_filter(Lot,field_set,None,None)
    log_runMES.to_debug('reply:'+str(reply))
    data_set=reply['DATA_SET']
    load_title='Lot List Query'
    return render(request,'runMES/dt_navbar_form.html',{'load_title':load_title,'col':field_set,'row':data_set})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@csrf_exempt
@login_required
def lot_hist_query(request):
  v_name='lot_hist_query'
  try:
    # log_runMES.to_info({'view':"lot_hist query"})
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      log_runMES.to_info({'view':"lot_hist query"})
      mytext=request.POST
      # log_runMES.to_debug({'post_text':mytext})
      input_fld=mytext['input_fld']
      log_runMES.to_debug('input_fld:'+str(input_fld))
      # data table column titles
      field_set=['lot','eq','op','recipe','product','process','process_step','qty','transaction','trans_time','annotation']
      try:
        lot_list=LotStepHist.objects.filter(lot=input_fld).order_by('trans_time')
        data_set=[]
        for l in lot_list:
          f_set=[]
          for f in field_set:
            f_set.append(getattr(l,f))
          data_set.append(f_set)

        return render(request,'runMES/dt_clean_form.html',{'col':field_set,'row':data_set})

      except Exception as e:
        info={'views':v_name,'ERR':e}
        mylog.error(info)
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

    else:
      form_title='Lot History Query'
      label_name='Lot ID'
      return render(request,'runMES/query_form.html',{'form_title':form_title,'label_name':label_name})

  except Exception as e:
    mylog.exception(e)

@csrf_exempt
@login_required
def lot_dc_hist_query(request):
  v_name='lot_dc_hist_query'
  # log_runMES.to_info({'view':"lot_dc query"})
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    log_runMES.to_info({'view':"lot_dc query reply"})
    mytext=request.POST
    # log_runMES.to_debug({'post_text':mytext})
    input_fld=mytext['input_fld']
    # log_runMES.to_debug('input_fld:'+str(input_fld))
    # data table column titles
    field_set=['Lot','EQ','DCPlan','Tran','Time','Annotation','OP','Item','Type','Unit','Value','TID']
    try:
      plan_set=DcPlanHist.objects.filter(lot=input_fld).order_by('trans_time')
      log_runMES.to_debug({'views':v_name,'plans':plan_set})
      data_set=[]
      if plan_set:
        for p in plan_set:
          item_set=DcValueHist.objects.filter(dcplan_hist=p)
          log_runMES.to_debug({'views':'lot_dc_hist','item_set':item_set})
          sub_set=[]
          for i in item_set:
            sub_set.append(p.lot)
            sub_set.append(p.eq)
            sub_set.append(p.dcplan)
            sub_set.append(p.trans_type)
            sub_set.append(p.trans_time)
            sub_set.append(p.annotation)
            sub_set.append(p.op)
            sub_set.append(i.dcitem)
            sub_set.append(i.datatype)
            sub_set.append(i.unit)
            sub_set.append(i.value)
            sub_set.append(i.tid)
            data_set.append(sub_set)
            sub_set=[]
          log_runMES.to_debug({'views':v_name,'data_set':data_set})

        return render(request,'runMES/dt_clean_form.html',{'col':field_set,'row':data_set})
      else:
        info={'views':v_name,'ECD':'D01','ETX':red_font(_('Data Collection Not Exist'))}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
  else:
    form_title='Lot DC Hist Query'
    label_name='Lot ID'
    return render(request,'runMES/query_form.html',{'form_title':form_title,'label_name':label_name})

@csrf_exempt
@login_required
def eq_record_hist(request):
  v_name='eq_record_hist'
  # log_runMES.to_info({'view':"eq_record_hist query"})
  if request.session['lang']:
    activate(request.session['lang'])
  else:
    activate(default_lang)
  if request.method=='POST':
    log_runMES.to_info({'view':"eq_record_hist_query"})
    mytext=request.POST
    # log_runMES.to_debug({'post_text':mytext})
    input_fld=mytext['input_fld']
    # log_runMES.to_debug('input_fld:'+str(input_fld))
    # data table column titles
    field_set=['EQ','DCPlan','Tran','Time','Annotation','OP','Item','Type','Unit','Value','TID']
    try:
      plan_set=DcPlanHist.objects.filter(trans_type='E',eq=input_fld).order_by('-trans_time')[:200]
      log_runMES.to_debug({'views':'eq_record_hist','plans':plan_set})
      data_set=[]
      if plan_set:
        for p in plan_set:
          item_set=DcValueHist.objects.filter(dcplan_hist=p)
          log_runMES.to_debug({'views':'eq_record_hist','item_set':item_set})
          sub_set=[]
          for i in item_set:
            sub_set.append(p.eq)
            sub_set.append(p.dcplan)
            sub_set.append(p.trans_type)
            sub_set.append(p.trans_time)
            sub_set.append(p.annotation)
            sub_set.append(p.op)
            sub_set.append(i.dcitem)
            sub_set.append(i.datatype)
            sub_set.append(i.unit)
            sub_set.append(i.value)
            sub_set.append(i.tid)
            data_set.append(sub_set)
            sub_set=[]
          log_runMES.to_debug({'views':v_name,'data_set':data_set})

        return render(request,'runMES/dt_clean_form.html',{'col':field_set,'row':data_set})
      else:
        info={'views':v_name,'ECD':'D01','ETX':red_font(_('Data Collection Not Exist'))}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
  else:
    form_title='EQ Record Hist Query'
    label_name='EQ'
    return render(request,'runMES/query_form.html',{'form_title':form_title,'label_name':label_name})

@csrf_exempt
@login_required
def lot_split_merge_hist(request):
  v_name='lot_split_merge_hist'
  # log_runMES.to_info({'view':"lot_split_merge_hist"})
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    log_runMES.to_info({'view':"lot_split_merge_hist"})
    mytext=request.POST
    # log_runMES.to_debug({'post_text':mytext})
    input_fld=mytext['input_fld']
    # log_runMES.to_debug('input_fld:'+str(input_fld))
    # data table column titles
    field_set=['Parent','P_Qty','Child','C_Qty','S/M','OP','TID','Time','Annotation']
    try:
      obj_set=LotSplitMergeHist.objects.filter(parent_lot=input_fld)
      log_runMES.to_debug({'views':v_name,'obj_set':obj_set})

      # if obj_set:
      data_set=[]
      sub_set=[]
      for p in obj_set:
        sub_set.append(p.parent_lot)
        sub_set.append(p.parent_qty)
        sub_set.append(p.child_lot)
        sub_set.append(p.child_qty)
        sub_set.append(p.split_merge)
        sub_set.append(p.op)
        sub_set.append(p.tid)
        sub_set.append(p.trans_time)
        sub_set.append(p.annotation)
        data_set.append(sub_set)
        sub_set=[]

      log_runMES.to_debug({'views':v_name,'data_set':data_set})
      return render(request,'runMES/dt_clean_form.html',{'col':field_set,'row':data_set})
    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
  else:
    form_title='Lot Split Merge Hist Query'
    label_name='Parent Lot'
    return render(request,'runMES/query_form.html',{'form_title':form_title,'label_name':label_name})

@csrf_exempt
@login_required
def lot_bonus_scrap_hist(request):
  v_name='lot_bonus_scrap_hist'
  # log_runMES.to_info({'view':"lot_bonus_scrap_hist"})
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    log_runMES.to_info({'view':"lot_bonus_scrap_hist"})
    mytext=request.POST
    # log_runMES.to_debug({'post_text':mytext})
    input_fld=mytext['input_fld']
    # log_runMES.to_debug('input_fld:'+str(input_fld))
    # data table column titles
    field_set=['Lot','Step','EQ','B/S','Old Qty','B/S Qty','Code','OP','TID','Time','Annotation']
    try:
      obj_set=BonusScrapHist.objects.filter(lot=input_fld)
      log_runMES.to_debug({'views':'lot_bonus_scrap_hist','obj_set':obj_set})

      # if obj_set:
      data_set=[]
      sub_set=[]
      for p in obj_set:
        sub_set.append(p.lot)
        sub_set.append(p.process_step)
        sub_set.append(p.eq)
        sub_set.append(p.bonus_scrap)
        sub_set.append(p.lot_old_qty)
        sub_set.append(p.bonus_scrap_qty)
        sub_set.append(p.code)
        sub_set.append(p.op)
        sub_set.append(p.tid)
        sub_set.append(p.trans_time)
        sub_set.append(p.annotation)
        data_set.append(sub_set)
        sub_set=[]

      log_runMES.to_debug({'views':'lot_bonus_scrap_hist','data_set':data_set})
      return render(request,'runMES/dt_clean_form.html',{'col':field_set,'row':data_set})

    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
  else:
    form_title='Lot Bonus Scrap Hist Query'
    label_name='Parent Lot'
    return render(request,'runMES/query_form.html',{'form_title':form_title,'label_name':label_name})

@csrf_exempt
@login_required
def lot_hold_release_hist(request):
  v_name='lot_hold_release_hist'
  # log_runMES.to_info({'view':"lot_hold_release_hist"})
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    log_runMES.to_info({'view':"lot_hold_release_hist"})
    mytext=request.POST
    # log_runMES.to_debug({'post_text':mytext})
    input_fld=mytext['input_fld']
    # log_runMES.to_debug('input_fld:'+str(input_fld))
    # data table column titles
    field_set=['Lot','H/R','HoldCode','ReleaseCode','OP','TID','Time','Annotation']
    try:
      obj_set=LotHoldHist.objects.filter(lot=input_fld)
      log_runMES.to_debug({'views':'lot_hold_release_hist','obj_set':obj_set})

      data_set=[]
      sub_set=[]
      for p in obj_set:
        sub_set.append(p.lot)
        sub_set.append(p.hold_release)
        sub_set.append(p.hold_code)
        sub_set.append(p.release_code)
        sub_set.append(p.op)
        sub_set.append(p.tid)
        sub_set.append(p.timestamp)
        sub_set.append(p.annotation)
        data_set.append(sub_set)
        sub_set=[]

      log_runMES.to_debug({'views':v_name,'data_set':data_set})
      return render(request,'runMES/dt_clean_form.html',{'col':field_set,'row':data_set})
    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
  else:
    form_title='Lot Hold Release Hist Query'
    label_name='Lot'
    return render(request,'runMES/query_form.html',{'form_title':form_title,'label_name':label_name})

@login_required
@csrf_exempt
@transaction.atomic
def lot_start(request):
  v_name='lot_start'
  if request.session['lang']:
    activate(request.session['lang'])
  try:
    if request.method=='POST':
      # log_runMES.to_debug({'post':request})
      data=request.POST
      workorder=data['workorder']
      # log_runMES.to_debug({'views':'lot_start','workorder:':workorder})
      if not WorkOrder.objects.filter(name=workorder):
        return render(request,'runMES/return_info.html',
                      {'info':{'ECD':'WO-01','ETX':red_font(_('Work Order Not Exist')),'WORK ORDER':workorder,'timestamp':timezone.now()}})
      else:
        w_obj=WorkOrder.objects.get(name=workorder)
        product_name=w_obj.product.name
        qty=w_obj.qty
        qty_left=w_obj.qty_left
        owner=w_obj.owner
        start_date=w_obj.start_date
        target_date=w_obj.target_date
        lot_type=w_obj.lot_type
        lot_priority=w_obj.lot_priority
        # log_runMES.to_debug(
        #   {'VIEWS':'lot_start','product':product_name,'qty':qty,'qty_left':qty_left,'owner':owner,'target_date':start_date,'target_date':target_date})
        reply=trans.tx_workorder_find_lotstart(workorder)
        lot_list=reply['lot_list']
        form=forms.LotStartForm(
          initial={'op':str(request.user),'target_time':target_date,'product':product_name,'work_order':workorder,'type':lot_type,'priority':lot_priority})
        form.fields['op'].widget.attrs['readonly']=True
        form.fields['product'].widget.attrs['readonly']=True
        form.fields['work_order'].widget.attrs['readonly']=True
        form.fields['type'].widget.attrs['readonly']=True
        form.fields['priority'].widget.attrs['readonly']=True
        if lot_list:
          log_runMES.to_debug({'views':v_name,'tx_workorder_find_lotstart':lot_list})
          return render(request,'runMES/lot_start_list.html',
                        {'form':form,'workorder':workorder,'product':product_name,'qty':str(qty),'qty_left':str(qty_left),'owner':owner,
                         'target_date':target_date,'lotstart_hist':lot_list})
        else:
          return render(request,'runMES/lot_start_list.html',
                        {'form':form,'workorder':workorder,'product':product_name,'qty':str(qty),'qty_left':str(qty_left),'owner':owner,
                         'target_date':target_date})
    else:
      return render(request,'runMES/lot_start.html',{'title':'Lot Start'})
  except Exception as e:
    mylog.exception(e)
    log_runMES.to_debug({'views':v_name,'ERR':e})
    info={'views':v_name,'ERR':red_font(e)}
    return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def lot_start_batch_query(request):
  v_name='lot_start_batch_query'
  if request.session['lang']:
    activate(request.session['lang'])
  try:
    if request.method=='POST':
      # log_runMES.to_debug({'post':request})
      data=request.POST
      workorder=data['workorder']
      if not WorkOrder.objects.filter(name=workorder):
        return render(request,'runMES/return_info.html',{'info':{'ECD':'WO-01','ETX':'Word Order not found','WORK ORDER':workorder,'timestamp':timezone.now()}})
      else:
        w_obj=WorkOrder.objects.get(name=workorder)
        product_name=w_obj.product.name
        qty=w_obj.qty
        qty_left=w_obj.qty_left
        owner=w_obj.owner
        # start_date=w_obj.start_date
        target_date=w_obj.target_date
        lot_type=w_obj.lot_type
        lot_priority=w_obj.lot_priority
        form=forms.BatchLotStartForm(
          initial={'op':str(request.user),'target_time':target_date,'product':product_name,'work_order':workorder,'type':lot_type,'priority':lot_priority})
        form.fields['op'].widget.attrs['readonly']=True
        form.fields['product'].widget.attrs['readonly']=True
        form.fields['work_order'].widget.attrs['readonly']=True
        form.fields['type'].widget.attrs['readonly']=True
        form.fields['priority'].widget.attrs['readonly']=True
        return render(request,'runMES/lot_start_batch.html',
                      {'form':form,'workorder':workorder,'product':product_name,'qty':str(qty),'qty_left':str(qty_left),'owner':owner,
                       'target_date':target_date})
    else:
      return render(request,'runMES/lot_start_query.html',{'title':'Batch Lot Start'})
  except Exception as e:
    mylog.exception(e)
    log_runMES.to_debug({'view':v_name,'ERR':e})
    info={'views':v_name,'ERR':red_font(e)}
    return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_start_add(request):
  v_name='lot_start_add'
  try:
    v_name='lot_start_add'
    log_runMES.to_debug('in lot_start_add')
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=="POST":
      form=forms.LotStartForm(request.POST)
      if form.is_valid():
        data=form.cleaned_data
        new_lot=data['name']
        new_lot_qty=data['qty']
        lot_type=data['type']
        new_op=data['op']
        new_target_time=data['target_time']
        product=data['product']
        workorder=data['work_order']
        log_runMES.to_debug({'views':v_name,'new_lot':new_lot,'new_lot_qty':new_lot_qty,'lot_type':lot_type,'new_op':new_op,'new_target_time':str(new_target_time),'workorder':workorder,'product':product})
        # tx_lot_start(lot_txt, qty_int, work_order_txt, lot_type_txt, op_txt, product_txt, annotation_txt)
        reply=trans.tx_lot_start(new_lot,int(new_lot_qty),workorder,lot_type,new_op,product,'')
        log_runMES.to_debug({'views':v_name,'reply':reply})
        etx=''
        err=''
        ecd=''
        lot_set=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))
        if 'LOT SET' in reply:
          lot_set=red_font(reply['LOT SET'])

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':new_lot,'QTY':new_lot_qty,'LOT_SET':lot_set,'OP':new_op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      else:
        return render(request,'runMES/return_info.html',{'info':{'ECD':'F01','ETX':red_font(_('Form Input Error')),'timestamp':timezone.now()}})
    else:
      return render(request,'runMES/lot_start.html')

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_start_batch(request):
  v_name='lot_start_batch'
  try:
    log_runMES.to_debug(v_name)
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=="POST":
      form=forms.BatchLotStartForm(request.POST)
      if form.is_valid():
        data=form.cleaned_data
        pre_lot=data['name']
        new_lot_qty=data['qty']
        lot_type=data['type']
        new_op=data['op']
        new_target_time=data['target_time']
        product=data['product']
        workorder=data['work_order']
        log_runMES.to_debug({'VIEWS':v_name,'new_lot':pre_lot,'new_lot_qty':new_lot_qty,'lot_type':lot_type,'new_op':new_op,'new_target_time':new_target_time,
                     'workorder':workorder,'product':product})
        reply=trans.tx_batch_lot_start(pre_lot,int(new_lot_qty),workorder,lot_type,new_op,product,'')
        etx=''
        err=''
        ecd=''
        lot_set=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))
        if 'LOT SET' in reply:
          lot_set=reply['LOT SET']

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'PRE_LOT':pre_lot,'QTY':new_lot_qty,'LOT_SET':lot_set,'OP':new_op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      else:
        return render(request,'runMES/return_info.html',{'info':{'ECD':'F01','ETX':red_font(_('Form Input Error')),'timestamp':timezone.now()}})
    else:
      return render(request,'runMES/lot_start_batch.html',{'title':'Auto Lot Start'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_record(request):
  v_name='lot_record'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotRecordForm(request.POST)
      if form.is_valid():
        step_obj=form.cleaned_data['step']
        op=form.cleaned_data['op']
        step_txt=step_obj.name
        if step_obj.dcplan:
          reply=trans.qry_dcplan_item(step_obj.dcplan.name,op)
          etx=''
          err=''
          ecd=''
          if 'ERR' in reply:
            err=red_font(reply['ERR'])
            info={'views':v_name,'ERR':err,'STEP':step_obj,'OP':op}
            return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
          if 'ECD' in reply:
            ecd=reply['ECD']
          if 'ETX' in reply:
            etx=reply['ETX']
            if ecd is not '0':
              etx=red_font(_(etx))
              info={'views':v_name,'ECD':ecd,'ETX':etx,'STEP':step_txt,'OP':op}
              return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

          dcitem_set=reply['DCITEM_SET']
          # log_runMES.to_debug({'views':'lot_record','dcitem_set':dcitem_set})
          return render(request,'runMES/record_dc.html',{'dcitem_set':dcitem_set,'dc_plan':step_obj.dcplan.name,'step':step_txt,'op':op})
        else:
          info={'views':v_name,'ECD':'D01','ETX':'Data Collection Not Exist','STEP':step_txt,'OP':op}
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      else:
        return render(request,'runMES/return_info.html',{'info':{'ECD':'F01','ETX':red_font(_('Form Input Error'))},'timestamp':timezone.now()})
    else:
      form=forms.LotRecordForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Record','form':form,'base':'modeling_base.html'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def record_dc(request):
  v_name='record_dc'
  if request.session['lang']:
    activate(request.session['lang'])
  # log_runMES.to_debug('in record_dc')
  if request.method=='POST':
    # log_runMES.to_debug({'views':'record_dc','POST':request.POST})
    mydict=dict(request.POST)
    # log_runMES.to_debug({'view':'record_dc','dict':mydict})
    lot=mydict['lot_field'][0]
    dcplan=mydict['dc_plan'][0]
    eq=mydict['eq_field'][0]
    step=mydict['step'][0]
    op=str(request.user)
    annotation=mydict['anno_field'][0]
    dc_itemset=[]
    if lot is '' or eq is '':
      return render(request,'runMES/return_info.html',{'info':{'ECD':'F01','ETX':red_font(_('Form Input Error'))},'timestamp':timezone.now()})
    if dcplan:
      cnt=0
      for name in mydict['item_name']:
        item={}
        item['item_name']=mydict['item_name'][cnt]
        item['category']=mydict['category'][cnt]
        item['unit']=mydict['unit'][cnt]
        item['data_type']=mydict['data_type'][cnt]
        item['val']=mydict['val'][cnt]
        dc_itemset.append(item)
        cnt=cnt+1

    # log_runMES.to_debug({'item_set':dc_itemset})
    try:
      # tx_lot_record(lot_txt,eq_txt,step_txt,op_txt,dcplan_txt,item_set,anno_txt)
      reply=trans.tx_lot_record(lot,eq,step,op,dcplan,dc_itemset,annotation)
      # log_runMES.to_debug({'views':'record_dc','hist_reply':reply})
      etx=''
      err=''
      ecd=''
      oos=''
      if 'ERR' in reply:
        err=red_font(reply['ERR'])
      if 'ECD' in reply:
        ecd=reply['ECD']
      if 'ETX' in reply:
        etx=reply['ETX']
        if ecd is not '0':
          etx=red_font(_(etx))

      info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'EQ':eq,'STEP':step,'OP':op}
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e,'LOT':lot,'EQ':eq,'STEP':step,'OP':op}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

@login_required
@csrf_exempt
def eq_record(request):
  v_name='eq_record'
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    form=forms.EqRecordForm(request.POST)
    if form.is_valid():
      try:
        eq=form.cleaned_data['eq']
        anno=form.cleaned_data['anno']
        if not anno:
          anno=''

        eq_set=Eq.objects.filter(name=eq)
        if not eq_set:
          return render(request,'runMES/return_info.html',{'info':{'ECD':'E05','ETX':red_font(_('EQ Not Exist')),'EQ':eq},'timestamp':timezone.now()})

        eq_obj=Eq.objects.get(name=eq)
        #eq_list=Eq.objects.filter(freeze=True,active=True,group__in=[r.eq_group for r in EqRecord.objects.filter(freeze=True,active=True)])
        # log_runMES.to_debug({'views':'eq_record','eq_list':eq_list})
        # if eq_obj not in eq_list:
        eq_rec_obj=EqRecord.objects.filter(eq_group=eq_obj.group,active=True,freeze=True)
        if not eq_rec_obj:
          return render(request,'runMES/return_info.html',{'info':{'ECD':'E06','ETX':'EQ record not exist','EQ':eq},'timestamp':timezone.now()})
        #eq_group=eq_obj.group
        # eq_rec_set=[]
        # for o in eq_rec_obj:
        #   eq_rec_set.append(o.name)
        op=form.cleaned_data['op']
        #eq_rec_set=EqRecord.objects.filter(eq_group=eq_obj.group)
        #mylog.debug({'views':v_name,'eq_rec':eq_rec_set})
        #form=forms.QueryEqRecordForm(initial={'eq_rec_choices':eq_rec_set})
        form=forms.QueryEqRecordForm(eq_group=eq_obj.group)
        return render(request,'runMES/eq_record_query.html',{'load_title':'Query EQ Record','form':form,'eq':eq,'op':op,'anno':anno})

      except Exception as e:
        mylog.exception(e)
        info={'view':v_name,'ERR':e}
        log_runMES.to_debug(info)
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      info={'ECD':'F01','ETX':'Form Input Error'}
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
  else:
    form=forms.EqRecordForm(initial={'op':str(request.user)})
    form.fields['op'].widget.attrs['readonly']=True
    return render(request,'runMES/comm_change.html',{'load_title':'EQ Record','form':form,'base':'modeling_base.html'})

@login_required
@csrf_exempt
def eq_record_query(request):
  v_name='eq_record_query'
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    #mylog.debug({'views':v_name,'request.POST':request.POST})
    dic=request.POST
    #mylog.debug({'views':v_name,'name':dic['name']})
    op=request.user

    try:
      name=dic['name']
      eq=dic['eq']
      eq_record_obj=EqRecord.objects.get(name=name)
      if eq_record_obj.dcplan:
        reply=trans.qry_dcplan_item(eq_record_obj.dcplan.name,op)
        dcitem_set=reply['DCITEM_SET']
        log_runMES.to_debug({'views':'eq_record','DC PLAN':eq_record_obj.dcplan.name,'EQ RECORD':eq_record_obj,'DCITEM SET':dcitem_set})
        log_runMES.to_debug({'views':v_name,'eq_record':eq_record_obj.name,'dcitem_set':dcitem_set,'eq':eq,'op':op})
        return render(request,'runMES/record_eq.html',{'eq':eq,'eq_record':eq_record_obj.name,'dcitem_set':dcitem_set,'dc_plan':eq_record_obj.dcplan.name,'op':op})
      else:
        info={'view':v_name,'ECD':'D01','ETX':'Data Collection Not Exist'}
        log_runMES.to_debug(info)
        return render(request,'runMES/return_info.html',{'OP':op,'EQ RECORD':eq_record_obj.name})
    except Exception as e:
      mylog.exception(e)
      info={'view':v_name,'ERR':e}
      log_runMES.to_debug(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
  else:
    return render(request,'runMES/return_info.html',{'load_title':'Query EQ Record','info':{'ECD':'F01','ETX':red_font(_('Form Invalid'))},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def record_eq(request):
  v_name='record_eq'
  # log_runMES.to_debug('in record_eq')
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    log_runMES.to_debug({'views':'record_eq','POST':request.POST})
    mydict=dict(request.POST)
    # log_runMES.to_debug({'view':'record_eq','dict':mydict})
    dcplan=request.POST['dc_plan_name']
    eq_record=mydict['eq_record'][0]
    eq=mydict['eq'][0]
    op=mydict['op'][0]
    annotation=mydict['anno_field'][0]
    dc_itemset=[]
    # log_runMES.to_debug({'view':'record_eq','dcplan':dcplan})
    if dcplan:
      cnt=0
      for name in mydict['item_name']:
        item={}
        item['item_name']=mydict['item_name'][cnt]
        item['category']=mydict['category'][cnt]
        item['unit']=mydict['unit'][cnt]
        item['data_type']=mydict['data_type'][cnt]
        item['val']=mydict['val'][cnt]
        dc_itemset.append(item)
        cnt=cnt+1

    log_runMES.to_debug({'item_set':dc_itemset})
    try:
      # tx_record_eq_hist(eq_txt,eq_record,op_txt,dcplan_txt,item_set,anno_txt)
      reply=trans.tx_eq_record(eq,eq_record,op,dcplan,dc_itemset,annotation)
      log_runMES.to_debug({'views':'record_dc','hist_reply':reply})
      etx=''
      err=''
      ecd=''
      oos=''
      if 'ERR' in reply:
        err=red_font(reply['ERR'])
      if 'ECD' in reply:
        ecd=reply['ECD']
      if 'ETX' in reply:
        etx=reply['ETX']
        if ecd is not '0':
          etx=red_font(_(etx))
      if 'OOS' in reply:
        if reply['OOS']!={}:
          oos=red_font(reply['OOS'])

      info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'OOS':oos,'EQ':eq,'OP':op}
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_step_in(request):
  v_name='lot_step_in'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotStepInForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        eq=form.cleaned_data['eq']
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        reply=trans.tx_step_in(lot,eq,op,annotation)
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'EQ':eq,'OP':op}
        if reply['ECD']!='0':
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
        # log_runMES.to_debug(reply)
        lot_obj=Lot.objects.get(name=lot)
        # step_obj=lot_obj.process_step
        qty=lot_obj.qty
        next_op=lot_obj.next_operation
        recipe=lot_obj.step_recipe
        product=lot_obj.product
        step=lot_obj.process_step
        step_instruction=lot_obj.process_step.instruction
        work_order_obj=WorkOrder.objects.get(name=lot_obj.workorder)
        work_order_instruction=work_order_obj.instruction
        # reply.update({'STEP INSTRUCTION':step_instruction,'WO INSTRUCTION':work_order_instruction})
        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'EQ':eq,'RECIPE':recipe,'STEP INSTRUCTION':step_instruction,'WO INSTRUCTION':work_order_instruction,'QTY':qty,'NEXT_OP':next_op,'PRODUCT':product,'PROCESS STEP':step,'OP':op,}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.LotStepInForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Step In','form':form,'base':'modeling_base.html'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_step_out(request):
  v_name='lot_step_out'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotStepOutForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        eq=form.cleaned_data['eq']
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        reply=trans.tx_step_out(lot,eq,op,annotation)
        log_runMES.to_info(reply)
        etx=''
        err=''
        ecd=''
        next_op=''
        product=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))
        if 'NEXT_OP' in reply:
          next_op=reply['NEXT_OP']
        if 'PRODUCT' in reply:
          product=reply['PRODUCT']
        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'EQ':eq,'NEXT_OP':next_op,'PRODUCT':product,'OP':op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.LotStepOutForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Step OUT','form':form,'base':'modeling_base.html'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_run_card(request):
  v_name='lot_run_card'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotRunCardForm(request.POST)
      if form.is_valid():
        lot_txt=form.cleaned_data['lot']
        try:
          lot_obj=Lot.objects.get(name=lot_txt)
          p_obj=lot_obj.process
          pp_list=ProcessProcessStep.objects.filter(process=p_obj)
          field_set=['name','category','recipe','eq_group','step_check','dcplan','binning','instruction']
          data_set=[]
          for p in pp_list:
            f_set=[]
            for f in field_set:
              f_set.append(getattr(p.process_step,f))
            data_set.append(f_set)
          load_title='Process Step List'
          return render(request,'runMES/dt_clean_form.html',{'load_title':load_title,'col':field_set,'row':data_set})

        except Exception as e:
          info={'views':v_name,'ERR':e,'lot':lot_txt}
          mylog.error(info)
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.LotRunCardForm
      return render(request,'runMES/comm_change.html',{'load_title':'Query Run Card','form':form,'base':'modeling_base.html'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def lotinfo(request,pk):
  v_name='lotinfo'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    mylot=get_object_or_404(Lot,pk=pk)
    form=forms.LotInfoForm(instance=mylot)
    col=form.fields
    # log_runMES.to_debug({'views':'lotinfo','col':col})
    row=form.clean()
    # log_runMES.to_debug({'views':'lotinfo','row':row})
    return render(request,'runMES/dt_clean_form.html',{'load_title':'Lot Detail','col':col,'row':row})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_ctrl_state(request):
  try:
    v_name='lot_ctrl_state'
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotCtrlStateForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        state=form.cleaned_data['ctrl_state']
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        reply=trans.tx_lot_ctrl_state_change(lot,state,op,annotation)
        log_runMES.to_info(reply)
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'STATE':state,'OP':op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      else:
        info={'views':v_name,'ECD':'F01','ETX':'Form Input Error'}
        mylog.error(info)
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.LotCtrlStateForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      # log_runMES.to_debug({'views':'lot_ctrl_state','form':form})
      return render(request,'runMES/comm_change.html',{'form':form,'load_title':'Lot Control State:'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

class EqStatusUpdate(UpdateView):
  model=Eq
  fields=['status']

@login_required
@csrf_exempt
def change_product(request):
  v_name='change_product'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.ChangeProductForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        to_product=form.cleaned_data['to_product']
        to_process_step=form.cleaned_data['to_process_step']
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        info={'views':'change_product','lot':lot,'to_product':to_product,'to_process_step':to_process_step,'op':op,'annotation':annotation}
        log_runMES.to_debug({'views':'change_product is_valid','info':info})
        reply=trans.tx_change_product(lot,to_product,to_process_step,op,annotation)
        log_runMES.to_info({'views':v_name,'reply':reply})
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'PRODUCT':to_product,'STEP':to_process_step,'OP':op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      else:
        info={'views':v_name,'ERR':form.errors}
        mylog.error(info)
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.ChangeProductForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      # log_runMES.to_debug({'views':'lot_ctrl_state','form':form})
      return render(request,'runMES/comm_change.html',{'form':form,'load_title':'Change Product:'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def eq_list_query(request):
  v_name='eq_list_query'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    else:
      activate(default_lang)
    # data table column titles
    field_set=['id','name','description','eq_type','parent','area','group','ctrl_state','is_hold','is_virtual','active']
    data_set=[]
    eq_list=Eq.objects.filter(active=True,freeze=True)
    for l in eq_list:
      f_set=[]
      for f in field_set:
        f_set.append(getattr(l,f))
      data_set.append(f_set)

    load_title='EQ List Query'
    return render(request,'runMES/dt_navbar_form.html',{'load_title':load_title,'col':field_set,'row':data_set})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_split(request):
  v_name='lot_split'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotSplitForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['parent_lot']
        qty=form.cleaned_data['child_qty']
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']

        lot_obj=Lot.objects.filter(name=lot)
        if not lot_obj:
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ECD':'L12','ETX':_('Lot Not Exist'),'LOT':lot},'timestamp':timezone.now()})
        # can not manual split lot run state
        if lot_obj[0].ctrl_state=='R':
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ECD':'L01','ETX':_('Lot State Mismatch'),'LOT':lot,'STATE':lot_obj[0].ctrl_state},'timestamp':timezone.now()})

        # tx_split_lot(parent_lot_txt,op_txt,child_qty_int,anno_txt)
        reply=trans.tx_split_lot(lot,op,qty,annotation)
        log_runMES.to_debug(reply)
        etx=''
        err=''
        ecd=''
        err_info=False
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
          err_info=True
        if 'ECD' in reply:
          ecd=reply['ECD']
          err_info=True
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'QTY':qty,'OP':op}
        if err_info:
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
        else:
          return render(request,'runMES/return_info.html',{'info':reply,'timestamp':timezone.now()})
      else:
        return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ECD':'F01','ETX':_('Form Input Error')},'timestamp':timezone.now()})
    else:
      form=forms.LotSplitForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Split','form':form,'base':'modeling_base.html'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_merge(request):
  v_name='lot_merge'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.LotMergeForm(request.POST)
      if form.is_valid():
        parent_lot=form.cleaned_data['parent_lot']
        child_lot=form.cleaned_data['child_lot']
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        # tx_merge_lot(parent_lot_txt,child_lot_txt,op_txt,anno_txt)
        reply=trans.tx_merge_lot(parent_lot,child_lot,op,annotation)
        log_runMES.to_debug({'views':v_name,'reply':reply})
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(etx)

        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'PARENT':parent_lot,'CHILD':child_lot,'OP':op}
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      else:
        return render(request,'runMES/return_info.html',{'info':{'views':'v_name','ECD':'F01','ETX':_('Form Input Error')},'timestamp':timezone.now()})
    else:
      form=forms.LotMergeForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Merge','form':form,'base':'modeling_base.html'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_query_bin(request):
  v_name='lot_query_bin'
  # log_runMES.to_debug({"views":'lot_query_bin','request':request})
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    log_runMES.to_debug({"views":'lot_query_bin','post':request.POST})
    lot=request.POST['lot_field']
    eq=request.POST['eq_field']
    op=str(request.user)
    try:
      reply=trans.qry_lot_bin(lot,eq,op)
      log_runMES.to_debug({"views":'lot_query_bin','reply':reply})
      if reply['ECD']!='0':
        return render(request,'runMES/return_info.html',{'info':reply,'timestamp':timezone.now()})
      else:
        grade_set=reply['GRADE_SET']
        lot_qty=reply['LOT_QTY']
        binning=reply['BINNING']
        return render(request,'runMES/lot_bin.html',{'views':v_name,'grade_set':grade_set,'binning':binning,'lot':lot,'eq':eq,'lot_qty':lot_qty,'op':op})
    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e,'lot':lot}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
  else:
    return render(request,'runMES/lot_query_bin.html')

@login_required
@csrf_exempt
def lot_bin(request):
  v_name='lot_bin'
  if request.session['lang']:
    activate(request.session['lang'])
  if request.method=='POST':
    mydict=dict(request.POST)
    log_runMES.to_debug({'views':'lot_bin','dict':mydict})
    lot=mydict['lot'][0]
    eq=mydict['eq'][0]
    lot_qty=mydict['lot_qty'][0]
    binning=mydict['lot_bin'][0]
    anno=mydict['anno_field'][0]
    grade_set=[]
    cnt=0
    total_qty=0
    for g in mydict['grade']:
      if mydict['qty'][cnt]:
        item={}
        item['grade']=mydict['grade'][cnt]
        item['description']=mydict['description'][cnt]
        item['qty']=mydict['qty'][cnt]
        if int(item['qty'])<0:
          return render(request,'runMES/return_info.html',
                        {'info':{'views':v_name,'ECD':'L14','ETX':_('Lot Qty Error'),'QTY':item['qty'],'timestamp':timezone.now()}})
        total_qty=total_qty+int(item['qty'])
        grade_set.append(item)
      cnt=cnt+1
    log_runMES.to_debug({'views':'lot_bin','grade_set':grade_set})
    if total_qty!=int(lot_qty):
      return render(request,'runMES/return_info.html',
                    {'info':{'views':v_name,'ECD':'L14','ETX':_('Lot Qty Error'),'LOT QTY':lot_qty,'TOTAL QTY':str(total_qty)},'timestamp':timezone.now()})
    try:
      # def tx_bin_hist(lot_txt,bin_txt,grade_set,op_txt,anno_txt):
      reply=trans.tx_lot_bin(lot,eq,binning,grade_set,str(request.user),anno)
      lot_obj=Lot.objects.get(name=lot)
      etx=''
      err=''
      ecd=''
      child_set=''
      if 'ERR' in reply:
        err=red_font(reply['ERR'])
      if 'ECD' in reply:
        ecd=reply['ECD']
      if 'ETX' in reply:
        etx=reply['ETX']
        if ecd is not '0':
          etx=red_font(_(etx))
      if 'CHILD LOT' in reply:
        child_set=['CHILD LOT']
      next_op=''
      if lot_obj.next_operation:
        next_op=lot_obj.next_operation

      info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'EQ':eq,'GRADE SET':child_set,'NEXT_OP':next_op}
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    except Exception as e:
      mylog.exception(e)
      info={'views':v_name,'ERR':e}
      mylog.error(info)
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_breaking(request):
  v_name='lot_breaking'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    if request.method=='POST':
      form=forms.BreakingForm(request.POST)
      if form.is_valid():
        lot=form.cleaned_data['lot']
        eq=form.cleaned_data['eq']
        op=form.cleaned_data['op']
        annotation=form.cleaned_data['annotation']
        reply=trans.tx_lot_breaking(lot,eq,op,annotation)
        # log_runMES.to_debug(reply)
        return render(request,'runMES/return_info.html',{'info':reply,'timestamp':timezone.now()})
      else:
        return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ECD':'F01','ETX':_('Form Input Error')},'timestamp':timezone.now()})
    else:
      form=forms.BreakingForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Breaking','form':form,'base':'modeling_base.html'})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def upload_csv(request):
  v_name='upload_csv'
  log_runMES.to_debug({'views':v_name,'request':request})
  cnt=1
  line=''
  if request.session['lang']:
    activate(request.session['lang'])
  else:
    activate(default_lang)

  if request.method=='GET':
    return render(request,"runMES/upload_csv.html")
  # if not GET, then proceed
  else:
    sid=transaction.savepoint()
    try:
      log_runMES.to_debug({'views':v_name,'POST':request.POST})
      csv_file=request.FILES["file"]
      if not csv_file.name.endswith('.csv'):
        log_runMES.to_warning({'views':v_name,request:'File is not CSV type'})
        #return HttpResponseRedirect(reverse("runMES:upload_csv"))
        return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('File is not CSV type')},'timestamp':timezone.now()})
      # if file is too large, return
      if csv_file.multiple_chunks():
        log_runMES.to_warning({'views':v_name, request:"Uploaded file is too big (%.2f MB)."%(csv_file.size/(1000*1000),)})
        return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Upload file exceed')},'timestamp':timezone.now()})

      file_data=csv_file.read().decode("utf-8")
      lines=file_data.splitlines()
      r_dicts=list(csv.DictReader(lines))
      log_runMES.to_debug({'views':v_name,'r_dicts':r_dicts})
      op=str(request.user)
      for line in r_dicts:
        log_runMES.to_debug({'views':v_name,'line':line})
        #log_runMES.to_debug({'views':v_name,'name':line['name'],'ERP_ref':line['ERP_ref'],'anno':line['annotation']})
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        ERP_ref=line['ERP_ref']
        product=line['product']
        if not product:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Product Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        lot_type=line['lot_type']
        if not lot_type:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('LotType Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        qty=int(line['qty'])
        lot_priority=int(line['lot_priority'])
        if not lot_priority:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Lot Priority Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        target_date=line['target_date']
        if not target_date:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Target Date Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        #op=line['op']
        owner=line['owner']
        owner_email=line['owner_email']
        owner_phone=line['owner_phone']
        instruction=line['instruction']
        annotation=line['annotation']

        log_runMES.to_debug({'views':v_name,'work order':name,'ERP_ref':ERP_ref,'product':product,'lot_type':lot_type,'qty':str(qty),'lot_priority':str(lot_priority),'target_date':target_date,'op':op,'owner':owner,'owner_mail':owner_email,'owner_phone':owner_phone,'instruction':instruction,'annotation':annotation})

        #def tx_work_order(order_txt,erp_ref_txt,product_txt,lot_type_txt,qty_int,lot_priority_int,target_date_txt,op_txt,owner_txt,owner_email_txt,owner_phone_txt,instruction_txt,annotation_txt)
        reply=trans.tx_work_order(name,ERP_ref,product,lot_type,qty,lot_priority,target_date,op,owner,owner_email,owner_phone,instruction,annotation)
        log_runMES.to_debug({'views':v_name,'tx_work_order reply':reply})
        cnt=cnt+1
        if reply['ECD']!='0':
          log_runMES.to_warning({'views':v_name,'ERR':reply})
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':reply,'timestamp':timezone.now()})

      transaction.savepoint_commit(sid)
      rec=cnt-1
      #log_runMES.to_info({'views':v_name,'record count':str(rec)})
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(rec)},'timestamp':timezone.now()})

    except Exception as e:
      #transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'line#':str(cnt),'Line':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def work_order(request):
  v_name='work_order'

  try:
    if request.session['lang']:
      activate(request.session['lang'])
    else:
      activate(default_lang)

    if request.method=='POST':
      #log_runMES.to_debug({'views':'work_order','post':request.POST,'user':str(request.user)})
      form=forms.WorkOrderForm(request.POST)
      if form.is_valid():
        data=form.cleaned_data
        name=data['workorder']
        ERP_ref=data['ERP_ref']
        product=data['product']
        lot_type=data['lot_type']
        qty=int(data['qty'])
        lot_priority=int(data['lot_priority'])
        target_date=data['target_date']
        op=data['op']
        owner=data['owner']
        owner_email=data['owner_email']
        owner_phone=data['owner_phone']
        instruction=data['instruction']
        annotation=data['annotation']
        log_runMES.to_debug({'views':v_name,'work order':name,'ERP_ref':ERP_ref,'product':product,'lot_type':lot_type,'qty':str(qty),'lot_priority':str(lot_priority),'target_date':target_date,'op':op,'owner':owner,'owner_mail':owner_email,'owner_phone':owner_phone,'instruction':instruction,'annotation':annotation})

        # def tx_work_order(order_txt,erp_ref_txt,product_txt,lot_type_txt,qty_int,lot_priority_int,target_date_txt,op_txt,owner_txt,owner_email_txt,owner_phone_txt,instruction_txt,annotation_txt)
        reply=trans.tx_work_order(name,ERP_ref,product,lot_type,qty,lot_priority,target_date.strftime('%Y-%m-%d'),op,owner,owner_email,owner_phone,instruction,
                                  annotation)
        log_runMES.to_debug({'views':v_name,'tx_work_order reply':reply})
        if reply['ECD']!='0':
          log_runMES.to_warning({'views':v_name,'ERR':reply})
          return render(request,'runMES/return_info.html',{'info':reply,'timestamp':timezone.now()})

      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK'},'timestamp':timezone.now()})
    else:
      form=forms.WorkOrderForm(initial={'op':str(request.user),'target_date':datetime.now()})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'Work Order','form':form})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

def work_order_query(request):
  v_name='work_order_query'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    else:
      activate(default_lang)
    # data table column titles
    field_set=['id','name','ERP_ref','product','lot_type','qty','qty_left','lot_priority','start_date','target_date','owner_email','is_close','active']
    data_set=[]
    wo_list=WorkOrder.objects.filter()
    for l in wo_list:
      f_set=[]
      for f in field_set:
        f_set.append(getattr(l,f))
      data_set.append(f_set)

    load_title='Work Order Query'
    return render(request,'runMES/dt_navbar_form.html',{'load_title':load_title,'col':field_set,'row':data_set})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def work_order_detail(request,pk):
  v_name='work_order_detail'
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    else:
      activate(default_lang)
    log_runMES.to_debug({'views':v_name,'op':str(request.user)})
    wo=get_object_or_404(WorkOrder,pk=pk)
    if request.method=='GET':
      form=forms.WorkOrderDetailForm(
        initial={'workorder':wo.name,'ERP_ref':wo.ERP_ref,'product':wo.product,'lot_type':wo.lot_type,'qty':wo.qty,'qty_left':wo.qty_left,
                 'lot_priority':wo.lot_priority,'owner':wo.owner,'owner_email':wo.owner_email,'owner_phone':wo.owner_phone,'start_date':wo.start_date,
                 'instruction':wo.instruction,'annotation':wo.annotation,'op':str(request.user),'active':wo.active,'freeze':wo.freeze})
      form.fields['workorder'].widget.attrs['readonly']=True
      form.fields['ERP_ref'].widget.attrs['readonly']=True
      form.fields['product'].widget.attrs['disabled']='disable'
      form.fields['lot_type'].widget.attrs['disabled']='disable'
      form.fields['qty'].widget.attrs['readonly']=True
      form.fields['qty_left'].widget.attrs['readonly']=True
      form.fields['lot_priority'].widget.attrs['readonly']=True
      form.fields['owner'].widget.attrs['readonly']=True
      form.fields['owner_email'].widget.attrs['readonly']=True
      form.fields['owner_phone'].widget.attrs['readonly']=True
      form.fields['start_date'].widget.attrs['readonly']=True
      form.fields['target_date'].widget.attrs['readonly']=True
      form.fields['instruction'].widget.attrs['readonly']=True
      form.fields['annotation'].widget.attrs['readonly']=True
      form.fields['op'].widget.attrs['readonly']=True
      form.fields['freeze'].widget.attrs['disabled']='disable'
      return render(request,'runMES/comm_change.html',{'load_title':'Work Order Update','form':form})
    else:
      if request.method=='POST':
        form=forms.WorkOrderDetailForm(request.POST)
        log_runMES.to_debug({'view':v_name,'request_POST':request.POST})
        if form.is_valid():
          workorder=form.cleaned_data['workorder']
          op=form.cleaned_data['op']
          is_close=form.cleaned_data['is_close']
          close_date=form.cleaned_data['close_date']
          if close_date:
            if close_date<wo.start_date:
              log_runMES.to_debug({'views':v_name,'ERR':'close date < start date'})

          active=form.cleaned_data['active']

          log_runMES.to_debug({'views':v_name,'name':workorder,'op':op,'is_close':str(is_close),'close_date':str(close_date),'active':str(active)})
          #form.save()
          #def tx_work_order_change(order_txt,op_txt,is_close_bol,close_date_txt,active_bol):
          reply=trans.tx_work_order_change(workorder,op,is_close,str(datetime.date(close_date)),active)

          # log_runMES.to_debug({'views':v_name},reply)
          etx=''
          err=''
          ecd=''
          if 'ERR' in reply:
            err=red_font(reply['ERR'])
          if 'ECD' in reply:
            ecd=reply['ECD']
          if 'ETX' in reply:
            etx=reply['ETX']
            if ecd is not '0':
              etx=red_font(_(etx))

          info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'OP':op}
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
        else:
          return render(request,'runMES/return_info.html',{'load_title':'Work Order Detail','info':{'ECD':'F01','ETX':red_font(_('Form Invalid'))},'timestamp':timezone.now()})
    return render(request,'runMES/return_info.html',{'load_title':'Work Order Detail','info':{'ECD':'W01','ETX':red_font(_('Work Order Not Exist'))},'timestamp':timezone.now()})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def eq_step_in_query(request):
  v_name='eq_step_in_query'
  log_runMES.to_debug({'views':v_name,'request':str(request)})
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    else:
      activate(default_lang)

    if request.method=='POST':
      form=forms.EqRecordForm(request.POST)
      #log_runMES.to_debug({'view':v_name,'request_POST':request.POST})
      if form.is_valid():
        eq=form.cleaned_data['eq']
        op=form.cleaned_data['op']
        anno=form.cleaned_data['anno']
        if not anno:
          anno=''
        reply=trans.qry_eq_query_lot(eq,op)
        log_runMES.to_debug({'views':v_name,'eq_query_lot':str(reply)})
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))
        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'EQ':eq,'OP':op}

        if reply['ECD']!='0':
          return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now(),'anno':anno})
        lot_list=reply['LOT_LIST']
        log_runMES.to_debug({'views':v_name,'lot_list':str(lot_list)})
        eq_form=forms.LotChoiceForm()
        eq_form.fields['lot'].choices=[(lot, lot) for lot in lot_list]
        return render(request,'runMES/eq_step_in.html',{'form':eq_form,'eq':eq})
    else:
      form=forms.EqRecordForm(initial={'op':str(request.user)})
      form.fields['op'].widget.attrs['readonly']=True
      return render(request,'runMES/comm_change.html',{'load_title':'EQ Lot StepIn','form':form})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def eq_step_in(request):
  v_name='eq_step_in'
  log_runMES.to_debug({'views':v_name,'request':str(request)})
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    else:
      activate(default_lang)

    if request.method=='POST':
      log_runMES.to_debug({'views':v_name,'POST':str(request.POST)})
      lot=request.POST['lot']
      eq=request.POST['eq']
      if request.POST['anno']:
        anno=request.POST['anno']
      else:
        anno=''
      op=str(request.user)
      log_runMES.to_debug({'views':v_name,'lot':lot,'eq':eq,'op':op,'anno':anno})
      reply=trans.tx_step_in(lot,eq,op,anno)
      etx=''
      err=''
      ecd=''
      if 'ERR' in reply:
        err=red_font(reply['ERR'])
      if 'ECD' in reply:
        ecd=reply['ECD']
      if 'ETX' in reply:
        etx=reply['ETX']
        if ecd is not '0':
          etx=red_font(_(etx))

      info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'EQ':eq,'OP':op}
      if reply['ECD']!='0':
        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
      # log_runMES.to_debug(reply)
      lot_obj=Lot.objects.get(name=lot)
      # step_obj=lot_obj.process_step
      qty=lot_obj.qty
      next_op=lot_obj.next_operation
      recipe=lot_obj.step_recipe
      product=lot_obj.product
      step=lot_obj.process_step
      step_instruction=lot_obj.process_step.instruction
      work_order_obj=WorkOrder.objects.get(name=lot_obj.workorder)
      work_order_instruction=work_order_obj.instruction
      info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'EQ':eq,'RECIPE':recipe,'STEP INSTRUCTION':step_instruction,'WO INSTRUCTION':work_order_instruction,'QTY':qty,'NEXT_OP':next_op,'PRODUCT':product,'PROCESS STEP':step,'OP':op,}
      return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':'Request Error'},'timestamp':timezone.now()})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
def lot_priority_change(request):
  v_name='lot_priority_change'
  log_runMES.to_debug({'views':v_name,'request':str(request)})
  try:
    if request.session['lang']:
      activate(request.session['lang'])
    else:
      activate(default_lang)

    if request.method=='POST':
      form=forms.LotPriorityForm(request.POST)
      #log_runMES.to_debug({'view':v_name,'request_POST':request.POST})
      if form.is_valid():
        lot=form.cleaned_data['lot']
        priority=form.cleaned_data['lot_priority']
        op=str(request.user)
        anno=form.cleaned_data['annotation']
        reply=trans.tx_change_lot_priority(lot,priority,op,anno)
        log_runMES.to_debug({'views':v_name,'change_lot_priority':str(reply)})
        etx=''
        err=''
        ecd=''
        if 'ERR' in reply:
          err=red_font(reply['ERR'])
        if 'ECD' in reply:
          ecd=reply['ECD']
        if 'ETX' in reply:
          etx=reply['ETX']
          if ecd is not '0':
            etx=red_font(_(etx))
        info={'views':v_name,'ECD':ecd,'ETX':etx,'ERR':err,'LOT':lot,'OP':op}

        return render(request,'runMES/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      form=forms.LotPriorityForm()
      return render(request,'runMES/comm_change.html',{'load_title':'Lot Priority Change','form':form})

  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})
