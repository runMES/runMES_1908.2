from django.shortcuts import render
from django.db import transaction
from runMES.models import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.html import format_html
from django.shortcuts import redirect
from django.core.validators import EmailValidator
from datetime import datetime
from django.contrib.auth.models import User,Group
import logging
from MQTT import log_runMES
import csv
from runMES import views as runMES_view

mylog=logging.getLogger('runMES')

# Create your views here.
def red_font(msg):
  return format_html('<span style="color: #cc0033; font-weight: bold;">{0}</span>',msg)

@login_required
@csrf_exempt
def modeling_home(request):
  v_name='modeling_home'
  groups=request.user.groups.values_list('name',flat=True)
  mylog.debug({'modeling_view':v_name,'groups':groups,'request':request})
  try:
    return render(request,'modeling/modeling_home.html',{'version':runMES_view.version,'lastupdate':runMES_view.lastupdate,'note':runMES_view.note,'copyright':runMES_view.cp_right,'base':'modeling_base.html'})
  except Exception as e:
    mylog.exception(e)
    return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':e},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def dc_category(request):
  v_name='model_dc_category'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  line=''
  recs=0
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Data Item Category Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        data_type=line['data_type']
        if not data_type:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Data Type Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        unit=line['unit']
        if not unit:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Unit Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if DcItemCategory.objects.filter(name=name,freeze=True):
          render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DcItemCategory Already Frozen'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        DcItemCategory.objects.create(name=name,description=description,data_type=data_type,unit=unit,active=True,freeze=True)
        info={'views':v_name,'name':name,'description':description,'data_type':data_type,'unit':unit,'op':op}
        ModelImportLog.objects.create(name='DcItemCategory',contents=info)
        recs=recs+1
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def dc_item(request):
  v_name='model_dc_item'
  mylog.debug({'modeling_view':v_name,'request':request})
  line=''
  cnt=1
  recs=0
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Data Item Import'})
  # if not GET, then proceed
  else:

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

      sid=transaction.savepoint()
      for line in r_dicts:
        log_runMES.to_debug({'views':v_name,'line':line})
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        dcitem_category=line['dcitem_category']

        if not DcItemCategory.objects.filter(name=dcitem_category,active=True,freeze=True):
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DeItemCategory Not Found Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        obj=DcItemCategory.objects.get(name=dcitem_category,active=True,freeze=True)

        if DcItem.objects.filter(name=name,freeze=True):
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DeItem Name Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        DcItem.objects.create(name=name,description=description,dcitem_category=obj,active=True,freeze=True)
        info={'views':v_name,'name':name,'description':description,'dcitem_category':dcitem_category,'op':op}
        ModelImportLog.objects.create(name='DcItem',contents=info)
        recs=recs+1
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def dc_spec(request):
  v_name='model_dc_spec'
  mylog.debug({'modeling_view':v_name,'request':request})
  groups=request.user.groups.values_list('name',flat=True)
  line=''
  cnt=1
  recs=0
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Data Item Spec Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if DcItemSpec.objects.filter(name=name,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DcItemSpec Name Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        dcitem=line['dcitem']
        if not DcItem.objects.filter(name=dcitem,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DcItem Not Found Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        obj=DcItem.objects.get(name=dcitem,active=True,freeze=True)
        exact_text=line['exact_text']
        spec_target=None
        if line['spec_target']:
          spec_target=float(line['spec_target'])
        spec_high=None
        if line['spec_high']:
          spec_high=float(line['spec_high'])
        spec_low=None
        if line['spec_low']:
          spec_low=float(line['spec_low'])
        screen_high=None
        if line['screen_high']:
          screen_high=float(line['screen_high'])
        screen_low=None
        if line['screen_low']:
          screen_low=line['screen_low']
        OOS_hold_lot=False
        if line['OOS_hold_lot']=='1':
          OOS_hold_lot=True
        OOS_hold_eq=False
        if line['OOS_hold_eq']=='1':
          OOS_hold_eq=True
        OOS_mail=False
        if line['OOS_mail']=='1':
          OOS_mail=True

        if screen_high and screen_low:
          if screen_low>=screen_high:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('screen_low>=screen_high'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if spec_high and spec_low:
          if spec_low>=spec_high:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('spec_low>=spec_high'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if spec_high and screen_high:
          if spec_high>=screen_high:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('spec_high>=screen_high'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if spec_low and screen_low:
          if spec_low<=screen_low:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('spec_low<=screen_low'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if spec_low and screen_high:
          if spec_low>=screen_high:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('spec_low>=screen_high'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if spec_high and screen_low:
          if spec_high>=screen_low:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('spec_high>=screen_low'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if spec_high and spec_target:
          if spec_high<spec_target:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('spec_high<spec_target'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if spec_low and spec_target:
          if spec_low<spec_target:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('spec_low<spec_target'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        DcItemSpec.objects.create(name=name,dcitem=obj,exact_text=exact_text,spec_target=spec_target,spec_high=spec_high,spec_low=spec_low,screen_high=screen_high,screen_low=screen_low,OOS_hold_lot=OOS_hold_lot,OOS_hold_eq=OOS_hold_eq,OOS_mail=OOS_mail,active=True,freeze=True)
        recs=recs+1

        info={'views':v_name,'name':name,'dcitem':obj.name,'exact_text':exact_text,'spec_target':spec_target,'spec_high':spec_high,'spec_low':spec_low,'screen_high':screen_high,'screen_low':screen_low,'OOS_hold_lot':OOS_hold_lot,'OOS_hold_eq':OOS_hold_eq,'OOS_mail':OOS_mail,'op':op}
        ModelImportLog.objects.create(name='DcItemSpec',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(cnt-1)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def dc_plan(request):
  v_name='model_dc_plan'
  mylog.debug({'modeling_view':v_name,'request':request})
  line=''
  cnt=1
  recs=0
  groups=request.user.groups.values_list('name',flat=True)

  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Data Plan Import'})
  # if not GET, then proceed
  else:
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

      sid=transaction.savepoint()
      dcplan_set=[]
      for line in r_dicts:
        log_runMES.to_debug({'views':v_name,'line':line})
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=None
        if line['description']:
          description=line['description']
        dcitems=line['dcitems']
        if not DcItem.objects.filter(name=dcitems,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DcItem Not Found Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        dcitem_spec=None
        if line['dcitem_spec']:
          dcitem_spec=line['dcitem_spec']

        plan_obj=None
        if DcPlan.objects.filter(name=name,freeze=True):
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DcPlan Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        elif DcPlan.objects.filter(name=name,active=True):
          plan_obj=DcPlan.objects.get(name=name,active=True)
        else:
          plan_obj=DcPlan.objects.create(name=name,description=description,active=True)
          dcplan_set.append(plan_obj)

        item_obj=DcItem.objects.get(name=dcitems,active=True,freeze=True)

        spec_obj=None
        if dcitem_spec:
          if not DcItemSpec.objects.filter(name=dcitem_spec,active=True,freeze=True):
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DcItemSpec Not Found'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

          spec_obj=DcItemSpec.objects.get(name=dcitem_spec,active=True,freeze=True)

        DcPlanDcItem.objects.create(dcplan=plan_obj,dcitems=item_obj,dcitem_spec=spec_obj)

        info={'views':v_name,'dcplan':plan_obj.name,'dcitem':dcitems,'dcspec':dcitem_spec,'op':op}
        ModelImportLog.objects.create(name='DcPlan',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      for p in dcplan_set:
        p.freeze=True
        p.save()
        recs=recs+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def model_area(request):
  v_name='model_area'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  line=''
  recs=0
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Area Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        if Area.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Area Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        Area.objects.create(name=name,description=description,active=True,freeze=True)
        info={'views':v_name,'name':name,'description':description,'op':op}
        ModelImportLog.objects.create(name='Area',contents=info)
        recs=recs+1
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def model_eq_group(request):
  v_name='model_eq_group'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'EQ Group Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if EqGroup.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('EqGroup Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        description=line['description']
        owner_mail=line['owner_mail']
        if owner_mail:
          EmailValidator(owner_mail)

        EqGroup.objects.create(name=name,description=description,owner_mail=owner_mail,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'owner_mail':owner_mail,'op':op}
        ModelImportLog.objects.create(name='EqGroup',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def model_eq(request):
  v_name='model_eq_group'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'EQ Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if Eq.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Eq Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        eq_type=line['eq_type']
        if eq_type not in ['L','A','S','D','T']:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('eq_type Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        parent=line['parent']
        parent_obj=None
        if parent:
          if not Eq.objects.filter(name=parent,active=True,freeze=True):
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('parent Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
          else:
            parent_obj=Eq.objects.get(name=parent,active=True,freeze=True)

        area=line['area']
        area_obj=None
        if not area or not Area.objects.filter(name=area,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('area Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        area_obj=Area.objects.get(name=area,active=True,freeze=True)

        eq_group=line['eq_group']
        if not eq_group or not EqGroup.objects.filter(name=eq_group,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('EqGroup Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        eq_group_obj=EqGroup.objects.get(name=eq_group,active=True,freeze=True)

        Eq.objects.create(name=name,description=description,eq_type=eq_type,parent=parent_obj,area=area_obj,group=eq_group_obj,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'eq_type':eq_type,'area':area,'eq_group':eq_group,'op':op}
        ModelImportLog.objects.create(name='Eq',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      #transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def lot_record(request):
  v_name='model_lot_record'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Lot Record Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if LotRecord.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('LotRecord Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        dcplan=line['dcplan']
        if not dcplan or not DcPlan.objects.filter(name=dcplan,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('dcplan Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        dcplan_obj=DcPlan.objects.get(name=dcplan,active=True,freeze=True)

        LotRecord.objects.create(name=name,description=description,dcplan=dcplan_obj,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'dcplan':dcplan,'op':op}
        ModelImportLog.objects.create(name='LotRecord',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def eq_record(request):
  v_name='model_eq_record'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'EQ Record Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if EqRecord.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('EqRecord Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        instruction=line['instruction']
        eq_group=line['eq_group']
        if not eq_group or not EqGroup.objects.filter(name=eq_group,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('EQ Group Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        eq_group_obj=EqGroup.objects.get(name=eq_group,active=True,freeze=True)

        dcplan=line['dcplan']
        if not dcplan or not DcPlan.objects.filter(name=dcplan,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DC Plan Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        dcplan_obj=DcPlan.objects.get(name=dcplan,active=True,freeze=True)

        EqRecord.objects.create(name=name,description=description,instruction=instruction,eq_group=eq_group_obj,dcplan=dcplan_obj,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'instruction':instruction,'eq_group':eq_group,'dcplan':dcplan,'op':op}
        ModelImportLog.objects.create(name='EqRecord',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def bin_grade(request):
  v_name='model_bin_grade'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Bin Grade Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if BinGrade.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('BinGrade Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']

        BinGrade.objects.create(name=name,description=description,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'op':op}
        ModelImportLog.objects.create(name='BinGrade',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def binning(request):
  v_name='model_binning'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  line=''
  recs=0
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Binning Import'})
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

      bin_set=[]
      for line in r_dicts:
        log_runMES.to_debug({'views':v_name,'line':line})
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if Binning.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Binning Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        bin_grade=line['bin_grade']

        bin_grade_obj=None
        if not bin_grade or not BinGrade.objects.filter(name=bin_grade,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('area Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        bin_grade_obj=BinGrade.objects.get(name=bin_grade,active=True,freeze=True)

        bin_obj=None
        if Binning.objects.filter(name=name,active=True):
          bin_obj=Binning.objects.get(name=name,active=True)
        else:
          bin_obj=Binning.objects.create(name=name,description=description,active=True)
          bin_set.append(bin_obj)

        Binning_BinGrade.objects.create(binning=bin_obj,bin_grades=bin_grade_obj)
        info={'views':v_name,'name':name,'description':description,'bin_grade':bin_grade,'op':op}
        ModelImportLog.objects.create(name='Binning',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      for b in bin_set:
        b.freeze=True
        b.save()
        recs=recs+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def step_category(request):
  v_name='model_step_category'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Step Category Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if StepCategory.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('StepCategory Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']

        StepCategory.objects.create(name=name,description=description,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'op':op}
        ModelImportLog.objects.create(name='StepCategory',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def process_step(request):
  v_name='model_process_step'
  mylog.debug({'modeling_view':v_name,'request':request})
  line=''
  cnt=1
  recs=0
  sid=transaction.savepoint()
  groups=request.user.groups.values_list('name',flat=True)

  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Process Step Import'})
  # if not GET, then proceed
  else:
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if ProcessStep.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('ProcessStep Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=None
        if line['description']:
          description=line['description']
        recipe=line['recipe']
        if not recipe:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Recipe Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        instruction=line['instruction']
        eq_group=line['eq_group']
        if not eq_group or not EqGroup.objects.filter(name=eq_group,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('EQ Group Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        eq_group_obj=EqGroup.objects.get(name=eq_group,active=True,freeze=True)

        category=line['category']
        category_obj=None
        if not category or not StepCategory.objects.filter(name=category,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Step Category Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        category_obj=StepCategory.objects.get(name=category,active=True,freeze=True)

        step_check=line['step_check']
        step_check_obj=None
        if step_check:
          if not EqRecord.objects.filter(name=step_check,active=True,freeze=True):
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Step Check Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
          step_check_obj=EqRecord.objects.get(name=step_check,active=True,freeze=True)

        dcplan=line['dcplan']
        dcplan_obj=None
        if dcplan:
          if DcPlan.objects.filter(name=name,active=True,freeze=True):
            dcplan_obj=DcPlan.objects.get(name=name,active=True,freeze=True)
          else:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('DC Plan Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        breaking=line['breaking']
        breaking_obj=None
        if breaking:
          if Breaking.objects.filter(name=name,active=True,freeze=True):
            breaking_obj=Breaking.objects.get(name=name,active=True,freeze=True)
          else:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Breaking Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        binning=line['binning']
        binning_obj=None
        if binning:
          if Binning.objects.filter(name=name,active=True,freeze=True):
            binning_obj=Binning.objects.get(name=name,active=True,freeze=True)
          else:
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Binning Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        ProcessStep.objects.create(name=name,description=description,recipe=recipe,instruction=instruction,eq_group=eq_group_obj,category=category_obj,step_check=step_check_obj,dcplan=dcplan_obj,breaking=breaking_obj,binning=binning_obj,active=True,freeze=True)
        recs=recs+1

        info={'views':v_name,'name':name,'description':description,'recipe':recipe,'instruction':instruction,'eq_group':eq_group,'category':category,'step_check':step_check,'dcplan':dcplan,'breaking':breaking,'binning':binning,'op':op}
        ModelImportLog.objects.create(name='ProcessStep',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def process(request):
  v_name='model_process'
  mylog.debug({'modeling_view':v_name,'request':request})
  line=''
  cnt=1
  recs=0
  groups=request.user.groups.values_list('name',flat=True)
  sid=transaction.savepoint()

  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Process Import'})
  # if not GET, then proceed
  else:
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

      process_set=[]
      for line in r_dicts:
        log_runMES.to_debug({'views':v_name,'line':line})
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if Process.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Process Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=None
        if line['description']:
          description=line['description']

        if Process.objects.filter(name=name,active=True):
          process_obj=Process.objects.get(name=name,active=True)
        else:
          process_obj=Process.objects.create(name=name,description=description,active=True)
          process_set.append(process_obj)

        step=line['process_step']
        if not step:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Process Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if ProcessStep.objects.filter(name=step,active=True,freeze=True):
          step_obj=ProcessStep.objects.get(name=step,active=True,freeze=True)
        else:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Process Step Not Found'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        ProcessProcessStep.objects.create(process=process_obj,process_step=step_obj)

        info={'views':v_name,'process':name,'process_step':step,'op':op}
        ModelImportLog.objects.create(name='Process',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      for p in process_set:
        p.freeze=True
        p.save()
        recs=recs+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def product(request):
  v_name='model_product'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Product Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if Product.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Product Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        description=line['description']
        unit=line['unit']
        if not unit:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Unit Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        process=line['process']
        process_obj=None
        if process:
          if not Process.objects.filter(name=process,active=True,freeze=True):
            transaction.savepoint_rollback(sid)
            return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Process Not Fount Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
          process_obj=Process.objects.get(name=process,active=True,freeze=True)

        Product.objects.create(name=name,description=description,unit=unit,process=process_obj,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'process':process,'op':op}
        ModelImportLog.objects.create(name='Product',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def breaking(request):
  v_name='model_breaking'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  line=''
  recs=0
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Breaking Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if Breaking.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Breaking Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        new_product=line['new_product']
        break_qty=line['break_qty']

        if not new_product:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('new_product empty'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if not break_qty:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('break_qty empty'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        if not Product.objects.filter(name=new_product,active=True,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('new product not found'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        else:
          product_obj=Product.objects.get(name=new_product,active=True,freeze=True)

        if int(break_qty)<1:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('new qty error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        Breaking.objects.create(name=name,description=description,break_qty=int(break_qty),new_product=product_obj,active=True,freeze=True)
        recs=recs+1

        info={'views':v_name,'name':name,'description':description,'break_qty':break_qty,'new_product':new_product,'op':op}
        ModelImportLog.objects.create(name='Breaking',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def bonus_scrap(request):
  v_name='model_bonus_scrap'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Bonus Scrap Code Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if BonusScrapCode.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('BonusScrapCode Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        bonus_scrap_code=line['bonus_scrap']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('name empty'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if bonus_scrap_code not in ['B','S']:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('bonus scrap code error (B or S)'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        BonusScrapCode.objects.create(name=name,description=description,bonus_scrap=bonus_scrap_code,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'bonus_scape':bonus_scrap_code,'op':op}
        ModelImportLog.objects.create(name='BonusScrapCode',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def lot_hold_release(request):
  v_name='model_lot_hold_release'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'Lot Hold Release Code Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if LotHoldReleaseCode.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('LotHoldReleaseCode Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        hold_release_code=line['hold_release']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('name empty'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if hold_release_code not in ['H','R']:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Lot hold release code error (H or R)'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        LotHoldReleaseCode.objects.create(name=name,description=description,hold_release=hold_release_code,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'hold_release':hold_release_code,'op':op}
        ModelImportLog.objects.create(name='LotHoldReleaseCode',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})


@login_required
@csrf_exempt
@transaction.atomic
def eq_hold_release(request):
  v_name='model_lot_hold_release'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'EQ Hold Release Code Import'})
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
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if EqHoldReleaseCode.objects.filter(name=name,freeze=True):
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('EqHoldReleaseCode Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        description=line['description']
        hold_release_code=line['hold_release']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('name empty'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if hold_release_code not in ['H','R']:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('EQ hold release code error (H or R)'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        EqHoldReleaseCode.objects.create(name=name,description=description,hold_release=hold_release_code,active=True,freeze=True)
        recs=recs+1
        info={'views':v_name,'name':name,'description':description,'hold_release':hold_release_code,'op':op}
        ModelImportLog.objects.create(name='EqLotHoldReleaseCode',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

@login_required
@csrf_exempt
@transaction.atomic
def user_account(request):
  v_name='model_user_account'
  mylog.debug({'modeling_view':v_name,'request':request})
  cnt=1
  recs=0
  line=''
  groups=request.user.groups.values_list('name',flat=True)
  if 'Admin' not in groups:
    return redirect('/modeling/')

  if request.method=='GET':
    return render(request,"modeling/upload_csv.html",{'load_title':'User Account Import'})
  # if not GET, then proceed
  else:
    sid=transaction.savepoint()
    try:
      log_runMES.to_debug({'views':v_name,'POST':request.POST})
      csv_file=request.FILES["file"]
      if not csv_file.name.endswith('.csv'):
        log_runMES.to_warning({'views':v_name,request:'File is not CSV type'})
        # return HttpResponseRedirect(reverse("runMES:upload_csv"))
        return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('File is not CSV type')},'timestamp':timezone.now()})
      # if file is too large, return
      if csv_file.multiple_chunks():
        log_runMES.to_warning({'views':v_name,request:"Uploaded file is too big (%.2f MB)."%(csv_file.size/(1000*1000),)})
        return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Upload file exceed')},'timestamp':timezone.now()})

      file_data=csv_file.read().decode("utf-8")
      lines=file_data.splitlines()
      r_dicts=list(csv.DictReader(lines))
      log_runMES.to_debug({'views':v_name,'r_dicts':r_dicts})
      op=str(request.user)
      op_group=Group.objects.get(name='OP')
      super_group=Group.objects.get(name='Super')
      mgr_group=Group.objects.get(name='Manager')
      adm_group=Group.objects.get(name='Admin')

      for line in r_dicts:
        log_runMES.to_debug({'views':v_name,'line':line})
        name=line['name']
        if not name:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Name Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
        if User.objects.filter(username=name).exists():
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('User Name Already Existed Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        pwd=line['password']
        if not pwd:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('Password Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        user_right=[]
        op_right=line['OP']
        if op_right=='1':
          user_right.append(op_group)
        super_right=line['Super']
        if super_right=='1':
          user_right.append(super_group)
        manager_right=line['Manager']
        if manager_right=='1':
          user_right.append(mgr_group)
        admin_right=line['Admin']
        if admin_right=='1':
          user_right.append(adm_group)

        if not user_right:
          transaction.savepoint_rollback(sid)
          return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font('User Right Empty Error'),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})

        log_runMES.to_debug({'model_views':v_name,'user_right':user_right})
        user=User.objects.create_user(password=pwd,username=name,is_active=True)
        user.save()
        user.groups.set(user_right)

        recs=recs+1
        info={'views':v_name,'name':name,'groups':user_right,'op':op}
        ModelImportLog.objects.create(name='User Account',contents=info)
        log_runMES.to_info(info)
        cnt=cnt+1

      transaction.savepoint_commit(sid)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'Result':'OK','Records':str(recs)},'timestamp':timezone.now()})

    except Exception as e:
      transaction.savepoint_rollback(sid)
      mylog.exception(e)
      return render(request,'runMES/return_info.html',{'info':{'views':v_name,'ERR':red_font(e),'Line#':str(cnt),'Content':str(line)},'timestamp':timezone.now()})
