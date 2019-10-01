from .models import *
from django.contrib import admin
from django.contrib import messages
from django import forms
from django.db.models.fields.reverse_related import ManyToOneRel, ManyToManyRel
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.models import LogEntry
from django.core.exceptions import ValidationError
from functools import partial
from django.contrib.admin.utils import flatten_fieldsets
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _

import logging

mylog=logging.getLogger('runMES')

admin.site.site_header='runMES Admin'
admin.site.site_title='runMES Admin'
admin.site.index_title='runMES Site Admin'

#base admin for save_model override, check freeze models
class BaseAdmin(admin.ModelAdmin):
  save_as = True
  def has_delete_permission(self, request, obj=None):
    if obj:
      if obj.freeze is True:
        return False
      else:
        return True
  def get_readonly_fields(self, request, obj=None):
    if obj:
      if obj.freeze is True:
        self.save_as = False
        #mylog.debug({'admin':'BaseAdmin.get_readonly','self':self,'obj':obj.id})
        readonly=[]
        for f in obj._meta.get_fields():
          if f.name is not 'active' and f.name is not 'instruction' and f.name is not 'id' and f.name is not 'process_step' and f.name is not 'is_close' and f.name is not 'close_date' and f.name is not 'annotation' and f.name is not 'step_check' and f.name is not 'owner_mail':
            if not isinstance(f, ManyToOneRel):
              if not isinstance(f, ManyToManyRel):
                readonly.append(f.name)

        return readonly
      #mylog.debug({'admin':'BaseAdmin.get_readonly','readony':readonly})
    return self.readonly_fields

class BaseTabularInline(admin.TabularInline):
  def has_delete_permission(self, request, obj=None):
    if obj:
      if obj.freeze is True:
        return False
      else:
        return True
  def get_readonly_fields(self, request, obj=None):
    if obj:
      if obj.freeze is True:
        #mylog.debug({'admin':'BaseAdmin.get_readonly','self':self,'obj':obj.id})
        readonly=[]
        for f in obj._meta.get_fields():
          if f.name is not 'active' and f.name is not 'id':
            if not isinstance(f, ManyToOneRel):
              if not isinstance(f, ManyToManyRel):
                readonly.append(f.name)

        return readonly
      #mylog.debug({'admin':'BaseAdmin.get_readonly','readony':readonly})
    return self.readonly_fields


class DcItemSpecAdmin(admin.ModelAdmin):
  model=DcItemSpec
  fields=['name','dcitem']
  list_display = ['name','dcitem_name','exact_text','spec_low','spec_high','OOS_hold_lot','OOS_hold_eq','OOS_mail','active','freeze']
  list_filter = ['active','freeze']
  #autocomplete_fields = ['dcitem']
  actions=['delete_model']
  ordering = ['name']

  def dcitem_name(self,obj):
    if obj.dcitem:
      return obj.dcitem.name
    else:
      return obj.dcitem

  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == "dcitem":
      kwargs["queryset"] = DcItem.objects.filter(freeze=True,active=True).order_by('name')

    return super().formfield_for_foreignkey(db_field, request, **kwargs)

  change_form_template ='admin/spec_add_form.html'
  add_form_template = 'admin/spec_add_form.html'

  #protect critical fields from change
  def get_readonly_fields(self, request, obj=None):
    if obj:
      if obj.freeze is True:
        self.save_as = False
        #mylog.debug({'admin':'BaseAdmin.get_readonly','self':self,'obj':obj.id})
        readonly=[]
        for f in obj._meta.get_fields():
          if f.name is 'name' or f.name is 'dcitem' or f.name is 'freeze':
            if not isinstance(f, ManyToOneRel):
              if not isinstance(f, ManyToManyRel):
                readonly.append(f.name)
        return readonly
    return self.readonly_fields

  # remove default delete action
  def get_actions(self,request):
    actions=super(DcItemSpecAdmin,self).get_actions(request)
    del actions['delete_selected']
    return actions

  #protect frozen records
  def delete_model(self, request, obj):
    mylog.debug({'admin.DcItemSpecAdmin':'delete_model','request':request,'obj':obj,'obj.[0]':obj[0].freeze})
    try:
      frz=obj[0].freeze
      if frz is True:
        info=obj[0].name + ' - Freeze model can not delete!'
        messages.add_message(request,messages.WARNING,info)
        return False
      else:
        obj[0].delete()
    except Exception as e:
      mylog.debug({'admin':'DcItemSpecAdmin','Exception':e})

  # def formfield_for_foreignkey(self,db_field,request,**kwargs):
  #   if db_field.name=="dcitem":
  #     kwargs["queryset"]=DcItem.objects.filter(freeze=True)
  #   return super().formfield_for_foreignkey(db_field,request,**kwargs)

  @csrf_exempt
  def change_view(self, request, object_id, form_url='', extra_context=None):
    mylog.debug({'admin.DcItemSpecAdmin':'change_view','request':request,'object_id':object_id})
    if request.method=='POST':
      mylog.debug({'admin.DcItemSpecAdmin':'change_view','request.POST':request.POST})
      data=request.POST
      item_spec_obj=DcItemSpec.objects.get(pk=object_id)

      #for first query info, get all fields from DB, prepare 3 input templates
      if 'change' not in data:
        spec_name=item_spec_obj.name
        item_obj=item_spec_obj.dcitem
        selected=item_obj.pk
        active=item_spec_obj.active
        freeze=item_spec_obj.freeze
        data_type=item_spec_obj.dcitem.dcitem_category.data_type
        oos_hold_lot=item_spec_obj.OOS_hold_lot
        oos_hold_eq=item_spec_obj.OOS_hold_eq
        oos_send_mail=item_spec_obj.OOS_mail

        # 3 templates for each data_type, turn on change flag
        if data_type=='T':
          val=item_spec_obj.exact_text
          mylog.debug({'admin.DcItemSpec':'freeze=True, change_view.prepare for query','spec_name':spec_name,'val':val,'item':item_obj,'item_key':selected,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail,'active':active,'freeze':freeze,})

          return render(request,'admin/dc_txt_spec_form.html',{'spec_name':spec_name,'val':val,'item':item_obj,'item_key':selected,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail,'active':active,'freeze':freeze,'change':True})

        elif data_type=='I':
          target=item_spec_obj.spec_target
          spec_high=item_spec_obj.spec_high
          spec_low=item_spec_obj.spec_low
          screen_high=item_spec_obj.screen_high
          screen_low=item_spec_obj.screen_low

          return render(request,'admin/dc_int_spec_form.html',{'spec_name':spec_name,'item':item_obj,'item_key':selected,'target':target,'spec_high':spec_high,'spec_low':spec_low,'screen_high':screen_high,'screen_low':screen_low,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail,'active':active,'freeze':freeze,'change':True})

        elif data_type=='F':
          target=item_spec_obj.spec_target
          spec_high=item_spec_obj.spec_high
          spec_low=item_spec_obj.spec_low
          screen_high=item_spec_obj.screen_high
          screen_low=item_spec_obj.screen_low

          return render(request,'admin/dc_num_spec_form.html',{'spec_name':spec_name,'item':item_obj,'item_key':selected,'target':target,'spec_high':spec_high,'spec_low':spec_low,'screen_high':screen_high,'screen_low':screen_low,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail,'active':active,'freeze':freeze,'change':True})
        else:
          mylog.debug({'admin.DcItemSpec':'not fit T,I,F','spec_name':spec_name,'data type':data_type,'item':item_obj,'active':active,'freeze':freeze})
          info={'Change Spec Item':'Failed - not fit T,I,F','Spec Name':spec_name,'data type':data_type,'Data Type':data_type}
          return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})


      #second post from template, change flag in data(save button)
      elif 'change' in data:
        mylog.debug({'admin.DcItemSpec':'change_view','change in data, data':data})
        spec_name=data['spec_name']
        item_key=data['item_key']
        item_obj=DcItem.objects.get(pk=int(item_key))
        item_name=item_obj.name
        if 'active' in data:
          active=True
        else:
          active=False

        if 'freeze' in data:
          freeze=True
        else:
          freeze=False

        unit=data['unit']
        data_type=data['data_type']

        if data_type=='T':
          val=data['val']
          if 'oos_hold_lot' in data:
            oos_hold_lot=True
          else:
            oos_hold_lot=False
          if 'oos_hold_eq' in data:
            oos_hold_eq=True
          else:
            oos_hold_eq=False
          if 'oos_send_mail' in data:
            oos_send_mail=True
          else:
            oos_send_mail=False
          mylog.debug({'admin.DcItemSpecAdmin':'change_view save contents','spec_name':spec_name,'item_obj':item_obj,'name':item_name,'active':active,'freeze':freeze,'unit':unit,'data_type':data_type,'val':val,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail})

          try:
            item_spec_obj=DcItemSpec.objects.get(pk=object_id)
            item_spec_obj.name=spec_name
            item_spec_obj.dcitem=item_obj
            item_spec_obj.exact_text=val
            item_spec_obj.OOS_hold_lot=oos_hold_lot
            item_spec_obj.OOS_hold_eq=oos_hold_eq
            item_spec_obj.OOS_mail=oos_send_mail
            item_spec_obj.active=active
            item_spec_obj.freeze=freeze
            item_spec_obj.save()

            info={'Change Spec Item':'Success','Spec Name':spec_name,'Unit':unit,'Data Type':data_type,'Spec Val':val,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail}
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now})

          except Exception as e:
            mylog.debug({'Change Spec Item':'Exception','Err':type(e)})
            info={'Change spec Item':'Failed','Error':e,'Item Name':item_name,'Unit':unit,'Data Type':data_type,'Spec Val':val}
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})

        elif data_type in ['I','F']:
          err_msg=''
          spec_high=float(data['spec_high'])
          spec_low=float(data['spec_low'])
          target=None
          if 'target' in data:
            target_str=data['target']
            if target_str is not '':
              target=float(target_str)
              if spec_high<target:
                err_msg='Spec High < Spec Target'

              if spec_low>target:
                err_msg='Spec Low > Spec Target'


          screen_h=data['screen_high']
          #mylog.debug({'admin.DcSpecDcItemAdmin':'change_view','screen_high':screen_h})
          if screen_h is not '':
            screen_high=float(screen_h)
            if screen_high<=spec_high:
              err_msg='Screen High <= Spec High'
          else:
            screen_high=None

          screen_l=data['screen_low']
          #mylog.debug({'admin.DcSpecDcItemAdmin':'change_view','screen_low':screen_l})
          if screen_l is not '':
            screen_low=float(screen_l)
            if screen_low>=spec_low:
              err_msg='Screen Low <= Spec Low'
          else:
            screen_low=None
          if 'oos_hold_lot' in data:
            oos_hold_lot=True
          else:
            oos_hold_lot=False
          if 'oos_hold_eq' in data:
            oos_hold_eq=True
          else:
            oos_hold_eq=False
          if 'oos_send_mail' in data:
            oos_send_mail=True
          else:
            oos_send_mail=False

          mylog.debug({'admin.DcItemSpecAdmin':'change_view spec_reply','spec_name':spec_name,'item_obj':item_obj,'name':item_name,'active':active,'freeze':freeze,'unit':unit,'data_type':data_type,'target':target,'spec_high':spec_high,'spec_low':spec_low,'screen_high':screen_high,'screen_low':screen_low,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail})

          if err_msg is not "":
            info={'Add cd spec Item':'Failed','Error':err_msg,'Item Name':item_name}
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})

          try:
            item_spec_obj=DcItemSpec.objects.get(pk=object_id)
            item_spec_obj.name=spec_name
            item_spec_obj.dcitem=item_obj
            item_spec_obj.spec_target=target
            item_spec_obj.spec_high=spec_high
            item_spec_obj.spec_low=spec_low
            item_spec_obj.screen_high=screen_high
            item_spec_obj.screen_low=screen_low
            item_spec_obj.OOS_hold_lot=oos_hold_lot
            item_spec_obj.OOS_hold_eq=oos_hold_eq
            item_spec_obj.OOS_mail=oos_send_mail
            item_spec_obj.active=active
            item_spec_obj.freeze=freeze
            item_spec_obj.save()

            info={'Change dc spec Item':'OK','Spec Name':spec_name,'Unit':unit,'Data Type':data_type,'Spec Target':target,'Spec High':spec_high,'Spec Low':spec_low,'Screen High':screen_high,'Screen Low':screen_low,'OOS Hold Lot':oos_hold_lot,'OOS Hold EQ':oos_hold_eq,'OOS Send Mail':oos_send_mail}
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})

          except Exception as e:
            mylog.debug({'Admin.DcItemSpecAdmin':'change_view','exception':e})
            info={'Add cd spec Item':'Failed','Error':e,'Spec Name':spec_name}
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})
        else:
          mylog.debug({'Change dc spec Item':'data type no case fit'})
          info={'Change dc spec Item':'data type no case fit'}
          return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})
      else:
        mylog.debug({'Change dc spec Item':'no case fit'})
        info={'Change dc spec Item':'Error, Not Save or Delete cases exist'}
        return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})
    else:
      return super().change_view(request,object_id,form_url,extra_context)

  @csrf_exempt
  def add_view(self,request,form_url='',extra_context=None):
    mylog.debug({'admin.DcItemSpecAdmin':'add_view','request':request})
    if request.method=='POST':
      mylog.debug({'admin.DcItemSpecAdmin':'add_view','request.POST':request.POST})
      data = request.POST
      if 'dcitem' in data:
        spec_name=request.POST['name']
        selected=int(request.POST['dcitem'])
        if 'active' in data:
          active=True
        else:
          active=False
        if 'freeze' in data:
          freeze=True
        else:
          freeze=False

        mylog.debug({'admin.DcItemSpecAdmin':'add_view-dcitem','request.POST':request.POST})
        mylog.debug({'admin.DcItemSpecAdmin':'add_view-dcitem','spec_name':spec_name,'selected':selected})
        item_obj=DcItem.objects.get(pk=int(selected))
        data_type=item_obj.dcitem_category.data_type

        # 3 templates for each data_type
        if data_type=='T':
          return render(request,'admin/dc_txt_spec_form.html',{'spec_name':spec_name,'item':item_obj,'item_key':selected,'active':active,'freeze':freeze})
        elif data_type=='I':
          return render(request,'admin/dc_int_spec_form.html',{'spec_name':spec_name,'item':item_obj,'item_key':selected,'active':active,'freeze':freeze})
        elif data_type=='F':
          return render(request,'admin/dc_num_spec_form.html',{'spec_name':spec_name,'item':item_obj,'item_key':selected,'active':active,'freeze':freeze})

      else:
        mylog.debug({'admin.DcItemSpecAdmin':'add_view-non dcitem','request.POST':request.POST})
        spec_name=data['spec_name']
        item_key=data['item_key']
        item_obj=DcItem.objects.get(pk=item_key)
        item_name=item_obj.name
        if 'active' in data:
          active=True
        else:
          active=False
        if 'freeze' in data:
          freeze=True
        else:
          freeze=False
        unit=item_obj.dcitem_category.unit
        data_type=item_obj.dcitem_category.data_type
        if data_type=='T':
          val=data['val']
          if 'oos_hold_lot' in data:
            oos_hold_lot=True
          else:
            oos_hold_lot=False
          if 'oos_hold_eq' in data:
            oos_hold_eq=True
          else:
            oos_hold_eq=False
          if 'oos_send_mail' in data:
            oos_send_mail=True
          else:
            oos_send_mail=False
          mylog.debug({'admin.DcItemSpecAdmin':'add_view save contents','spec_name':spec_name,'item_key':item_key,'item_name':item_name,'active':active,'freeze':freeze,'unit':unit,'data_type':data_type,'val':val,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail})
          try:
            l=DcItemSpec(name=spec_name,dcitem=item_obj,exact_text=val,OOS_hold_lot=oos_hold_lot,OOS_hold_eq=oos_hold_eq,OOS_mail=oos_send_mail,freeze=freeze,active=active)
            l.save()
            info={'Add spec Item':'Success','Spec Name':spec_name,'item_name':item_name,'Unit':unit,'Data Type':data_type,'Spec Val':val,'OOS Hold Lot':oos_hold_lot,'OOS Hold EQ':oos_hold_eq,'OOS Send Mail':oos_send_mail}
            #messages.info(request,info)
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})

          except Exception as e:
            mylog.debug({'Admin.DcItemSpecAdmin':'add_view','exception':e})
            info={'Add dc spec Item':'Failed','Error':e,'Spec Name':spec_name}
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})

        else:
          err_msg=''
          spec_high=float(data['spec_high'])
          spec_low=float(data['spec_low'])
          target=None
          if 'target' in data:
            target_str=data['target']
            if target_str is not '':
              target=float(target_str)
              if spec_high < target:
                err_msg='Spec High < Spec Target'

              if spec_low>target:
                err_msg='Spec Low > Spec Target'

          if spec_low>spec_high:
            err_msg='Spec Low > Spec High'

          screen_h=data['screen_high']
          #mylog.debug({'admin.DcSpecDcItemAdmin':'add_view','screen_high':screen_h})
          if screen_h is not '':
            screen_high=float(screen_h)
            if screen_high<=spec_high:
              err_msg='Screen High <= Spec High'
          else:
            screen_high=None

          screen_l=data['screen_low']
          if screen_l is not '':
            screen_low=float(screen_l)
            if screen_low>=spec_low:
              err_msg='Screen Low <= Spec Low'
          else:
            screen_low=None
          if 'oos_hold_lot' in data:
            oos_hold_lot=True
          else:
            oos_hold_lot=False
          if 'oos_hold_eq' in data:
            oos_hold_eq=True
          else:
            oos_hold_eq=False
          if 'oos_send_mail' in data:
            oos_send_mail=True
          else:
            oos_send_mail=False

          mylog.debug({'admin.DcItemSpecAdmin':'add_view spec_reply','spec_name':spec_name,'name':item_name,'active':active,'freeze':freeze,'unit':unit,'data_type':data_type,'target':target,'spec_high':spec_high,'spec_low':spec_low,'screen_high':screen_high,'screen_low':screen_low,'oos_hold_lot':oos_hold_lot,'oos_hold_eq':oos_hold_eq,'oos_send_mail':oos_send_mail})

          if err_msg is not "":
            info={'Add cd spec Item':'Failed','Error':err_msg,'Item Name':item_name}
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})

          try:
            l=DcItemSpec(name=spec_name,dcitem=item_obj,spec_target=target,spec_high=spec_high,spec_low=spec_low,screen_high=screen_high,screen_low=screen_low,OOS_hold_lot=oos_hold_lot,OOS_hold_eq=oos_hold_eq,OOS_mail=oos_send_mail,freeze=freeze,active=active)
            l.save()
            info={'Add cd spec Item':'Success','Spec Name':spec_name,'Unit':unit,'Data Type':data_type,'Spec Target':target,'Spec High':spec_high,'Spec Low':spec_low,'Screen High':screen_high,'Screen Low':screen_low,'OOS Hold Lot':oos_hold_lot,'OOS Hold EQ':oos_hold_eq,'OOS Send Mail':oos_send_mail}
            #messages.info(request,info)
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now})
          except Exception as e:
            mylog.debug({'Admin.DcItemSpecAdmin':'add_view','exception':e})
            info={'Add cd spec Item':'Failed','Error':e,'Spec Name':spec_name}
            return render(request,'admin/return_info.html',{'info':info,'timestamp':timezone.now()})

    else:
      #form=DcSpecForm
      return super().add_view(request,form_url,extra_context)

admin.site.register(DcItemSpec,DcItemSpecAdmin)

class DcItemCategoryAdmin(BaseAdmin):
  list_display = ['name','data_type','unit','active','freeze']
  list_filter = ['active','freeze']
  ordering = ['name']

admin.site.register(DcItemCategory,DcItemCategoryAdmin)

class DcItemAdmin(BaseAdmin):
  list_display = ['name','description','dcitem_category','data_type','unit','active','freeze']
  search_fields=['name']
  list_filter=['dcitem_category__name','active','freeze']
  ordering=['name']

  def data_type(self,obj):
    if obj.dcitem_category:
      return obj.dcitem_category.data_type
    else:
      return ''

  def unit(self,obj):
    if obj.dcitem_category:
      return obj.dcitem_category.unit
    else:
      return ''

  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == "dcitem_category":
      kwargs["queryset"] = DcItemCategory.objects.filter(freeze=True,active=True).order_by('name')
    return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(DcItem,DcItemAdmin)

@admin.register(DcPlanDcItem)
class DcPlanDcItemAdmin(admin.ModelAdmin):
  #ordering = ['dcplan__name']
  search_fields = ['dcplan__name','dcitems__name']


class DcPlanDcItemInline(BaseTabularInline):
  model=DcPlanDcItem
  fields=['dcitems','dcitem_spec','is_required']
  autocomplete_fields=['dcitems']
  ordering = ['dcplan']

  def formfield_for_foreignkey(self,db_field,request,**kwargs):
    if db_field.name=="dcitems":
      kwargs["queryset"]=DcItem.objects.filter(freeze=True,active=True).order_by('name')
    return super().formfield_for_foreignkey(db_field,request,**kwargs)

class DcPlanAdmin(BaseAdmin):
  model = DcPlan
  save_as = True
  list_display = ['name','dcitems_name','dcitem_spec_name','active','freeze','lastupdate']
  list_filter = ['active','freeze']
  search_fields=['name','dcitems__name','description']
  ordering = ['name']
  #readonly_fields = ['lastupdate']
  inlines=[DcPlanDcItemInline]

  # def formfield_for_manytomany(self, db_field, request, **kwargs):
  #   if db_field.name == "dcitems":
  #     kwargs["queryset"] = DcItem.objects.filter(freeze=True)
  #   return super().formfield_for_manytomany(db_field, request, **kwargs)

  def dcitems_name(self,obj):
    if obj.dcitems:
      obj_set=DcPlanDcItem.objects.filter(dcplan_id=obj)
      if obj_set:
        return ' > '.join([p.dcitems.name for p in obj_set])
      else:
        return ''
    else:
      return ''

  def dcitem_spec_name(self,obj):
    if obj.dcitem_spec:
      obj_set=DcPlanDcItem.objects.filter(dcplan_id=obj)
      if obj_set:
        l=''
        for obj in obj_set:
          if obj.dcitem_spec:
            l=l+obj.dcitem_spec.name+'>'
        return l
      else:
        return ''
    else:
      return ''

admin.site.register(DcPlan,DcPlanAdmin)

class BinGradeAdmin(BaseAdmin):
  model=BinGrade
  list_display = ['name','description','lastupdate','active','freeze']
  list_filter = ['active','freeze']
  save_as = True

admin.site.register(BinGrade,BinGradeAdmin)

class Binning_BinGradeInline(BaseTabularInline):
  model=Binning_BinGrade
  fields=['binning','bin_grades']
  #autocomplete_fields=['dcitems']

  def formfield_for_foreignkey(self,db_field,request,**kwargs):
    if db_field.name=="bin_grades":
      kwargs["queryset"]=BinGrade.objects.filter(freeze=True,active=True).order_by('name')
    return super().formfield_for_foreignkey(db_field,request,**kwargs)

class BinningAdmin(BaseAdmin):
  model=Binning
  save_as = True
  list_display=['name','active','freeze','lastupdate']
  list_filter=['active','freeze']
  inlines=[Binning_BinGradeInline]

admin.site.register(Binning,BinningAdmin)

@admin.register(Breaking)
class BreakingAdmin(BaseAdmin):
  save_as=True
  list_display=['name','break_qty','new_product','active','freeze','lastupdate']
  list_filter=['active','freeze']

class ProcessStepAdmin(BaseAdmin):
  model=ProcessStep
  save_as = True
  list_display=['name','cat','eq_group','recipe','step_check','dc','brk','bin','active','freeze','lastupdate']
  search_fields=['name','category__name']
  list_filter=['category__name','active','freeze']

  def cat(self,obj):
    if obj.category:
      return obj.category.name
    else:
      return obj.category

  def dc(self,obj):
    if obj.dcplan:
      return obj.dcplan.name
    else:
      return obj.dcplan

  def step_chk(self,obj):
    if obj.step_check:
      return obj.step_check.name
    else:
      return obj.step_check

  def bin(self,obj):
    if obj.binning:
      return obj.binning.name
    else:
      return obj.binning

  def brk(self,obj):
    if obj.breaking:
      return obj.breaking.name
    else:
      return obj.breaking

  def formfield_for_foreignkey(self,db_field,request,**kwargs):
    if db_field.name=="category":
      kwargs["queryset"]=StepCategory.objects.filter(freeze=True,active=True).order_by('name')
    if db_field.name=="dcplan":
      kwargs["queryset"]=DcPlan.objects.filter(freeze=True,active=True).order_by('name')
    if db_field.name=="step_check":
      kwargs["queryset"]=EqRecord.objects.filter(freeze=True,active=True).order_by('name')
    if db_field.name=="binning":
      kwargs["queryset"]=Binning.objects.filter(freeze=True,active=True).order_by('name')
    if db_field.name=="breaking":
      kwargs["queryset"]=Breaking.objects.filter(freeze=True,active=True).order_by('name')
    return super().formfield_for_foreignkey(db_field,request,**kwargs)


admin.site.register(ProcessStep,ProcessStepAdmin)

class LotRecordAdmin(BaseAdmin):
  model=LotRecord
  save_as = True
  list_display=['name','dcplan_name','active','freeze','lastupdate']
  ordering=('name',)
  search_fields=['name']
  list_filter=['active','freeze']

  def dcplan_name(self,obj):
    if obj.dcplan:
      return obj.dcplan.name
    else:
      return obj.dcplan

  def formfield_for_foreignkey(self,db_field,request,**kwargs):
    if db_field.name=="dcplan":
      kwargs["queryset"]=DcPlan.objects.filter(freeze=True,active=True).order_by('name')
    return super().formfield_for_foreignkey(db_field,request,**kwargs)

admin.site.register(LotRecord,LotRecordAdmin)

@admin.register(EqRecord)
class EqRecordAdmin(BaseAdmin):
  model=EqRecord
  save_as = True
  list_display=['name','eq_group','dcplan_name','active','freeze','lastupdate']
  ordering=('name',)
  search_fields=['name']
  list_filter=['active','freeze']

  def dcplan_name(self,obj):
    if obj.dcplan:
      return obj.dcplan.name
    else:
      return obj.dcplan

  def formfield_for_foreignkey(self,db_field,request,**kwargs):
    if db_field.name=="dcplan":
      kwargs["queryset"]=DcPlan.objects.filter(freeze=True,active=True).order_by('name')
    if db_field.name=="eq_group":
      kwargs["queryset"]=EqGroup.objects.filter(freeze=True,active=True).order_by('name')
    return super().formfield_for_foreignkey(db_field,request,**kwargs)


class ProcessInline(BaseTabularInline):
  model=ProcessProcessStep
  fields = ['process_step']
  #autocomplete_fields = ['process_step']

  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == "process_step":
      kwargs["queryset"]=ProcessStep.objects.filter(freeze=True,active=True).order_by('name')
    return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ProcessAdmin(BaseAdmin):
  model=Process
  list_display = ['name','process_step_name','active','freeze','lastupdate']
  search_fields=['name','description']
  list_filter=['name','active','freeze']
  inlines=[ProcessInline]

  def process_step_name(self,obj):
    if obj.process_step:
      #mylog.debug({'process_step':obj.process_step.all()})
      obj_set=ProcessProcessStep.objects.filter(process_id=obj)
      if obj_set:
        #mylog.debug({'obj_set':obj_set})
        return ' > '.join([p.process_step.name for p in obj_set])
      else:
        return ''
    else:
      return ''

admin.site.register(Process,ProcessAdmin)

class StepCategoryAdmin(BaseAdmin):
  list_display=['name','active','freeze','lastupdate']
  search_fields=['name']
  list_filter=('active','freeze')

admin.site.register(StepCategory,StepCategoryAdmin)

@admin.register(ProcessParameters)
class ProcessParametersAdmin(BaseAdmin):
  list_display=['name','process','data_type','active','freeze','lastupdate']
  search_fields=['name','process']
  list_filter=('active','freeze')
  ordering = ['process']


# class productForm(forms.ModelForm):
#   def __init__(self,*args,**kwargs):
#     super(productForm,self).__init__(*args,**kwargs)
#     self.fields['process'].required=False
#     self.fields['unit'].required=True
#
#   class Meta:
#     model=Product
#     fields=['name','process','unit','active','freeze']

class ProductAdmin(BaseAdmin):
  #form=productForm
  list_display = ['name','process','unit','active','freeze','lastupdate']
  search_fields = ['name','process','description']
  list_filter=('active','freeze')

  # def formfield_for_foreignkey(self, db_field, request, **kwargs):
  #   if db_field.name == "process":
  #     kwargs["queryset"] = Process.objects.filter(freeze=True,active=True).order_by('name')
  #   return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Product,ProductAdmin)

class ProductParametersAdmin(BaseAdmin):
  search_fields = ['name','product']
  list_filter = ('active', 'freeze')

admin.site.register(ProductParameters,ProductParametersAdmin)

class EqGroupAdmin(BaseAdmin):
  list_display = ['name','description','owner_mail','freeze','active','lastupdate']
  ordering = ['name']

admin.site.register(EqGroup,EqGroupAdmin)

class EqAdmin(BaseAdmin):
  list_display = ['name','group_name','eq_type','parent','area_name','active','freeze','lastupdate']
  list_filter=['area__name','group__name','eq_type']
  ordering=['name']
  #readonly_fields = ['is_hold','hold_reason','is_virtual','last_product','last_recipe','last_eq_record','eq_record_time']

  def group_name(self,obj):
    if obj.group:
      return obj.group.name
    else:
      return obj.group

  def area_name(self,obj):
    if obj.area:
      return obj.area.name
    else:
      return obj.area

  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == "group":
      kwargs["queryset"] = EqGroup.objects.filter(freeze=True,active=True).order_by('name')
    if db_field.name == "area":
      kwargs["queryset"] = Area.objects.filter(freeze=True,active=True).order_by('name')
    return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Eq,EqAdmin)


# class WorkOrderAdmin(BaseAdmin):
#   list_display = ['name','product','qty','qty_left','lot_priority','op','start_date','target_date','owner','is_close','close_date','active','freeze']
#   list_filter=['is_close','active','freeze']
#   readonly_fields = ['qty_left','op']
#   search_fields = ['name']
#   ordering=['name']
#
#   def save_model(self, request, obj, form, change):
#     if not obj.pk:
#       obj.qty_left=obj.qty
#       obj.op=request.user
#
#     super().save_model(request,obj,form,change)
#
#   def formfield_for_foreignkey(self, db_field, request, **kwargs):
#     if db_field.name == "product":
#       kwargs["queryset"] = Product.objects.filter(freeze=True,active=True).order_by('name')
#     return super().formfield_for_foreignkey(db_field, request, **kwargs)
#
# admin.site.register(WorkOrder,WorkOrderAdmin)

#admin.site.register(LotCustState,LotCustStateAdmin)
@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
  list_display = ['name','workorder','product','process','process_step','is_hold','ctrl_state','next_operation','start_time','target_time','is_active']
  search_fields=['name','workorder']
  list_filter = ['ctrl_state','is_active']
  ordering = ['name']

class BonusScrapCodeAdmin(BaseAdmin):
  list_display = ['bonus_scrap','name','description','lastupdate','active','freeze']
  list_filter = ['bonus_scrap']
  ordering = ['bonus_scrap']
  save_as=True

admin.site.register(BonusScrapCode,BonusScrapCodeAdmin)

class LotHoldReleaseCodeAdmin(BaseAdmin):
  list_display = ['hold_release','name','description','lastupdate','active','freeze']
  list_filter = ['hold_release']
  ordering = ['hold_release']
  save_as=True

admin.site.register(LotHoldReleaseCode,LotHoldReleaseCodeAdmin)

class EqHoldReleaseCodeAdmin(BaseAdmin):
  list_display = ['hold_release','name','description','lastupdate','active','freeze']
  list_filter = ['hold_release']
  ordering = ['hold_release']
  save_as=True

admin.site.register(EqHoldReleaseCode,EqHoldReleaseCodeAdmin)


# admin.site.register(lot_hist)
# admin.site.register(EqHist)
admin.site.register(Area)

@admin.register(MailQueue)
class MailQueueAdmin(admin.ModelAdmin):
  list_display=['receiver','subject','record_timestamp','deliver_timestamp']
  list_filter=['is_deliver']


# admin.site.register(EqStateHist)
# admin.site.register(DcPlanHist)
# admin.site.register(DcValueHist)
#
# admin.site.register(LotStartHist)

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
  list_display=['content_type','user','action_time','object_id','object_repr','action_flag','change_message']
  def has_delete_permission(self, request, obj=None):
    return False
  def has_add_permission(self,request):
    return False
  def has_change_permission(self, request, obj=None):
    return False
# admin.site.register(UserSession)
# admin.site.register(AccessFunctions)
# admin.site.register(GroupAccess)
