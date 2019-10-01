from django import forms
from django.forms import ModelForm
from django.forms.widgets import SelectDateWidget,SplitDateTimeWidget
from django.contrib.admin import widgets
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from runMES.models import *
from django.core.validators import MaxValueValidator, MinValueValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core import validators
from django.core.validators import validate_slug
from crispy_forms.layout import Layout
import logging
from datetime import datetime

mylog = logging.getLogger('runMES')

class LotInfoForm(ModelForm):
  #test=forms.CharField(label='test field',initial='test')
  class Meta:
    model = Lot
    fields = '__all__'
    #readonly_fields='__all__'
    labels = {
      'name': _('Lot ID'),
    }

class EqInfoForm(ModelForm):
  class Meta:
    model = Eq
    fields = '__all__'
    #readonly_fields = '__all__'


class LotRecordForm(forms.Form):
  step_obj=LotRecord.objects.filter(active=True,freeze=True)
  step = forms.ModelChoiceField(step_obj)
  op=forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))

  def new_data(self):
    data = self.cleaned_data['step']
    data.append(self.cleaned_data['op'])
    return data

class EqRecordForm(forms.Form):
  eq = forms.CharField(label='EQ:',max_length=30)
  op=forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))
  anno=forms.CharField(max_length=30,label='Annotation:',required=False)

  def new_data(self):
    data = self.cleaned_data['eq']
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['anno'])
    return data

class LotChoiceForm(forms.Form):
  lot=forms.ChoiceField(label='Choose Lot:')

  def new_data(self):
    data=self.cleaned_data['lot']

    return data

class QueryEqRecordForm(forms.Form):
  def __init__(self,eq_group,*args,**kwargs):
    super(QueryEqRecordForm,self).__init__(*args,**kwargs)
    # self.fields['name']=forms.ModelChoiceField(
    #   queryset=EqRecord.objects.filter(eq_group=eq_group)
    # )
    self.fields['name']=forms.ChoiceField(choices=[(o.name, str(o)) for o in EqRecord.objects.filter(eq_group=eq_group)])

  # class Meta:
  #   model=EqRecord
  #   fields=('name',)


  # eq_rec_obj=None
  # eq_rec=forms.ModelChoiceField(eq_rec_obj,label='EQ Record:')

  # eq_rec_choices=()
  # eq_rec=forms.ChoiceField(choices=eq_rec_choices,label='EQ Record:',widget=forms.Select())

  def new_data(self):
    data=self.cleaned_data['name']
    return data


class LotStepInForm(forms.Form):
  # lotObj = lot.objects.get(pk=id)
  lot = forms.CharField(label='LOT:', max_length=30)
  eq = forms.CharField(label='EQ:', max_length=30)
  annotation = forms.CharField(label='Annotation:', max_length=100, required=False)
  op=forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))

  def new_data(self):
    data = self.cleaned_data['lot']
    data.append(self.cleaned_data['eq'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

  def __init__(self, *args, **kwargs):
    super(LotStepInForm, self).__init__(*args, **kwargs)
    self.helper = FormHelper()
    self.helper.add_input(Submit('submit', 'StepIn'))


class LotStepOutForm(forms.Form):
  # lotObj = lot.objects.get(pk=id)
  lot = forms.CharField(label='LOT:', max_length=30)
  eq = forms.CharField(label='EQ:', max_length=30)
  annotation = forms.CharField(label='Annotation:', max_length=100, required=False)
  op=forms.CharField(label='OP:',max_length=30)

  def new_data(self):
    data = self.cleaned_data['lot']
    data.append(self.cleaned_data['eq'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

class LotHoldForm(forms.Form):
  lot = forms.CharField(label='LOT:', max_length=30)
  hold_code_obj=LotHoldReleaseCode.objects.filter(freeze=True,hold_release='H')
  hold_code=forms.ModelChoiceField(hold_code_obj,label='Hold Code:')
  op = forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))
  annotation = forms.CharField(label='Annotation:', max_length=100, required=False)

  def new_data(self):
    data = self.cleaned_data['lot']
    data.append(self.cleaned_data['hold_code'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

class LotReleaseForm(forms.Form):
  lot_obj=Lot.objects.filter(is_hold=True)
  lot = forms.ModelChoiceField(lot_obj,label='LOT:')
  release_code_obj=LotHoldReleaseCode.objects.filter(freeze=True,hold_release='R')
  release_code=forms.ModelChoiceField(release_code_obj,label='Release Code:')
  op = forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))
  annotation = forms.CharField(label='Annotation:', max_length=100, required=False)

  def new_data(self):
    data = self.cleaned_data['lot']
    data.append(self.cleaned_data['release_code'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

class LotPriorityForm(forms.Form):
  lot=forms.CharField(label='LOT:',max_length=30)
  lot_priority_choices=((1,'Urgent'),(2,'Hot'),(3,'High'),(4,'Regular'),(5,'Low'))
  lot_priority=forms.IntegerField(label='Lot Priority:',widget=forms.Select(choices=lot_priority_choices),initial=3,required=True)
  annotation=forms.CharField(label='Annotation:',max_length=100,required=False)

  def new_data(self):
    data = self.cleaned_data['lot']
    data.append(self.cleaned_data['lot_priority'])
    data.append(self.cleaned_data['annotation'])


class LotShipForm(forms.Form):
  lot = forms.CharField(label='Lot:',max_length=30)
  op = forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))
  annotation = forms.CharField(label='Annotation:', max_length=100, required=False)

  def new_data(self):
    data = self.cleaned_data['lot']
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

class LotRunCardForm(forms.Form):
  lot=forms.CharField(label='LOT:',max_length=30)
  def new_data(self):
    data = self.cleaned_data['lot']
    return data

class BonusForm(forms.Form):
  lot=forms.CharField(label='Lot:',max_length=30)
  bonus_code_choice=BonusScrapCode.objects.filter(bonus_scrap='B')
  bonus_code=forms.ModelChoiceField(bonus_code_choice,label='Bonus Code')
  qty=forms.IntegerField()
  op=forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))
  annotation=forms.CharField(label='Annotation:', max_length=100, required=False)

  def new_data(self):
    data=self.cleaned_data['lot']
    data.append(self.cleaned_data['bonus_code'])
    data.append(self.cleaned_data['qty'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

class ScrapForm(forms.Form):
  lot=forms.CharField(label='Lot:',max_length=30)
  bonus_code_choice=BonusScrapCode.objects.filter(bonus_scrap='S')
  scrap_code=forms.ModelChoiceField(bonus_code_choice,label='Scrap Code')
  qty=forms.IntegerField()
  op=forms.CharField(label='OP:',max_length=30,widget=forms.TextInput(attrs={'autofocus':False}))
  annotation=forms.CharField(label='Annotation:',max_length=100,required=False)

  def new_data(self):
    data=self.cleaned_data['lot']
    data.append(self.cleaned_data['scrap_code'])
    data.append(self.cleaned_data['qty'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

class EqHoldForm(forms.Form):
  eq = forms.CharField(label='eq:', max_length=30)
  hold_code_obj=EqHoldReleaseCode.objects.filter(freeze=True,hold_release='H')
  hold_code=forms.ModelChoiceField(hold_code_obj,label='Hold Code:')
  op = forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))
  annotation = forms.CharField(label='Annotation:', max_length=100, required=False)

  def new_data(self):
    data = self.cleaned_data['eq']
    data.append(self.cleaned_data['hold_code'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

class EqReleaseForm(forms.Form):
  eq_obj=Eq.objects.filter(is_hold=True)
  eq = forms.ModelChoiceField(eq_obj,label='EQ:')
  release_code_obj=EqHoldReleaseCode.objects.filter(freeze=True,hold_release='R')
  release_code=forms.ModelChoiceField(release_code_obj,label='Release Code:')
  op = forms.CharField(label='OP:',max_length=30, widget=forms.TextInput(attrs={'autofocus': False}))
  annotation = forms.CharField(label='Annotation:', max_length=100, required=False)

  def new_data(self):
    data = self.cleaned_data['eq']
    data.append(self.cleaned_data['release_code'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['annotation'])
    return data

class WorkOrderInfoForm(ModelForm):
  class Meta:
    model=WorkOrder
    fields='__all__'
    labels={
      'name':_('Work Order'),
    }
    widgets={'close_date':SelectDateWidget}


class WorkOrderForm(forms.Form):
  workorder = forms.CharField(label='Work Order:',max_length=30,required=True)
  ERP_ref=forms.CharField(label='ERP_ref:',max_length=30,required=False)
  product_obj=Product.objects.filter(freeze=True,active=True)
  product = forms.ModelChoiceField(product_obj,label='Product:',required=True)
  qty = forms.IntegerField(label='Qty:', max_value=10000, min_value=1,required=True)
  #qty_left=forms.IntegerField(label='Qty Left:', max_value=10000, min_value=1,required=False)
  lot_type_choices=WorkOrder.lot_type_choices
  lot_type=forms.CharField(max_length=1,label='Lot Type:',widget=forms.Select(choices=lot_type_choices),required=True)
  lot_priority_choices=((1,'Urgent'),(2,'Hot'),(3,'High'),(4,'Regular'),(5,'Low'))
  lot_priority=forms.IntegerField(label='Lot Priority:',widget=forms.Select(choices=lot_priority_choices),initial=3,required=True)
  #start_date=forms.DateTimeField(label='Start Date:',disabled=True)
  target_date=forms.DateTimeField(label='Target Date:',widget=SelectDateWidget(), required=True)
  op = forms.CharField(label='OP:',max_length=30)
  owner = forms.CharField(label='Owner:',max_length=30,required=False)
  owner_email=forms.CharField(label='Owner email:',max_length=30,required=True)
  owner_phone=forms.CharField(label='Owner Phone:',max_length=30,required=False)
  #is_close=forms.BooleanField(label='Is Closed',required=False)
  #close_date=forms.DateTimeField(label='Closed Date:',widget=SelectDateWidget(),required=False)
  instruction=forms.CharField(label='Instruction:',max_length=2048,widget=forms.Textarea,required=False)
  annotation = forms.CharField(label='Annotation:', max_length=30, required=False)
  active=forms.BooleanField()
  freeze=forms.BooleanField()

  def new_data(self):
    data = self.cleaned_data['workorder']
    data.append(self.cleaned_data['ERP_ref'])
    data.append(self.cleaned_data['product'].name)
    data.append(self.cleaned_data['lot_type'])
    data.append(self.cleaned_data['qty'])
    #data.append(self.cleaned_data['qty_left'])
    data.append(self.cleaned_data['target_date'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['owner'])
    data.append(self.cleaned_data['owner_email'])
    data.append(self.cleaned_data['owner_phone'])
    #data.append(self.cleaned_data['is_close'])
    #data.append(self.cleaned_data['close_date'])
    data.append(self.cleaned_data['instruction'])
    data.append(self.cleaned_data['annotation'])
    data.append(self.cleaned_data['active'])
    data.append(self.cleaned_data['freeze'])
    return data

class WorkOrderDetailForm(forms.Form):
  workorder=forms.CharField(label='Work Order:',max_length=30,required=False)
  ERP_ref=forms.CharField(label='ERP_ref:',max_length=30,required=False)
  product_obj=Product.objects.filter(freeze=True,active=True)
  product=forms.ModelChoiceField(product_obj,label='Product:',required=False)
  qty=forms.IntegerField(label='Qty:',max_value=10000,min_value=1,required=False)
  qty_left=forms.IntegerField(label='Qty Left:',max_value=10000,min_value=1,required=False)
  #lot_type_choices=WorkOrder.lot_type_choices
  lot_type=forms.CharField(max_length=1,label='Lot Type:',required=False)
  #lot_priority_choices=((1,'Urgent'),(2,'Hot'),(3,'High'),(4,'Regular'),(5,'Low'))
  lot_priority=forms.IntegerField(label='Lot Priority:',required=False)
  start_date=forms.DateTimeField(label='Start Date:',required=False)
  target_date=forms.DateTimeField(label='Target Date:',required=False)
  op=forms.CharField(label='OP:',max_length=30,required=False)
  owner=forms.CharField(label='Owner:',max_length=30,required=False)
  owner_email=forms.CharField(label='Owner email:',max_length=30,required=False)
  owner_phone=forms.CharField(label='Owner Phone:',max_length=30,required=False)
  is_close=forms.BooleanField(label='Is Closed',required=False)
  close_date=forms.DateTimeField(label='Closed Date:',widget=SelectDateWidget(),required=False)
  instruction=forms.CharField(label='Instruction:',max_length=2048,widget=forms.Textarea,required=False)
  annotation=forms.CharField(label='Annotation:',max_length=30,required=False)
  active=forms.BooleanField(required=False)
  freeze=forms.BooleanField(disabled=True,required=False)

  def new_data(self):
    data=self.cleaned_data['workorder']
    data.append(self.cleaned_data['ERP_ref'])
    data.append(self.cleaned_data['product'].name)
    data.append(self.cleaned_data['lot_type'])
    data.append(self.cleaned_data['qty'])
    data.append(self.cleaned_data['qty_left'])
    data.append(self.cleaned_data['target_date'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['owner'])
    data.append(self.cleaned_data['owner_email'])
    data.append(self.cleaned_data['owner_phone'])
    data.append(self.cleaned_data['is_close'])
    data.append(self.cleaned_data['close_date'])
    data.append(self.cleaned_data['instruction'])
    data.append(self.cleaned_data['annotation'])
    data.append(self.cleaned_data['active'])
    data.append(self.cleaned_data['freeze'])
    return data

# class CalendarWidget(forms.TextInput):
#     class Media:
#       css={
#         'all':('pretty.css',)
#       }
#       js=('animations.js','actions.js')


class LotStartForm(forms.Form):
  name=forms.CharField(label='Lot',max_length=16,validators=[validators.validate_slug],help_text=" ('Aa-Zz', '0-9', '_', '-' ONLY) Max 16")
  qty=forms.IntegerField(label='Qty')
  priority=forms.IntegerField(label='Lot Priority')
  op=forms.CharField(label='OP',max_length=30)
  target_time=forms.SplitDateTimeField(label='Target Time',widget=widgets.AdminSplitDateTime)
  product=forms.CharField(label='Product',max_length=30)
  work_order=forms.CharField(label='Work Order',max_length=30)
  type=forms.CharField(label='Lot Type')

  def new_data(self):
    data=self.cleaned_data['name']
    data.append(self.cleaned_data['qty'])
    data.append(self.cleaned_data['priority'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['target_time'])
    data.append(self.cleaned_data['product'])
    data.append(self.cleaned_data['work_order'])
    data.append(self.cleaned_data['type'])

class BatchLotStartForm(forms.Form):
  name=forms.CharField(label='Start Lot ID',max_length=12,validators=[validators.validate_slug],help_text=" ('Aa-Zz', '0-9', '_', '-' ONLY, Max 12, extension '-' '1-n' will add on automatically)")
  qty=forms.IntegerField(label='Lot Qty',help_text=" (Max batch size 9999)")
  priority=forms.IntegerField(label='Lot Priority')
  op=forms.CharField(label='OP',max_length=30)
  target_time=forms.SplitDateTimeField(label='Target Time',widget=widgets.AdminSplitDateTime)
  product=forms.CharField(label='Product',max_length=30)
  work_order=forms.CharField(label='Work Order',max_length=30)
  type=forms.CharField(label='Lot Type')

  def new_data(self):
    data=self.cleaned_data['name']
    data.append(self.cleaned_data['qty'])
    data.append(self.cleaned_data['priority'])
    data.append(self.cleaned_data['op'])
    data.append(self.cleaned_data['target_time'])
    data.append(self.cleaned_data['product'])
    data.append(self.cleaned_data['work_order'])
    data.append(self.cleaned_data['type'])

class LotCtrlStateForm(forms.Form):
  states=Lot.ctrl_state_choices
  lot=forms.CharField(label='Lot',max_length=30)
  ctrl_state=forms.ChoiceField(choices=states)
  annotation=forms.CharField(max_length=100,required=False)
  op=forms.CharField()

  def new_data(self):
    data=self.cleaned_data['lot']
    data.append(self.cleaned_data['ctrl_state'])
    data.append(self.cleaned_data['annotation'])
    data.append(self.cleaned_data['op'])

class EqCtrlStateForm(forms.Form):
  states=Eq.ctrl_state_choices
  eq=forms.CharField(label='EQ',max_length=30)
  ctrl_state=forms.ChoiceField(choices=states)
  annotation=forms.CharField(max_length=100,required=False)
  op=forms.CharField()

  def new_data(self):
    data=self.cleaned_data['eq']
    data.append(self.cleaned_data['ctrl_state'])
    data.append(self.cleaned_data['annotation'])
    data.append(self.cleaned_data['op'])

class LotSplitForm(forms.Form):
  parent_lot=forms.CharField(label='Parent Lot',max_length=30)
  child_qty=forms.IntegerField(label='Child Lot Qty')
  annotation=forms.CharField(max_length=100,required=False)
  op=forms.CharField(max_length=30)

  def new_data(self):
    data=self.cleaned_data['name']
    data.append(self.cleaned_data['parent_lot'])
    data.append(self.cleaned_data['child_qty'])
    data.append(self.cleaned_data['annotation'])
    data.append(self.cleaned_data['op'])

class LotMergeForm(forms.Form):
  parent_lot=forms.CharField(label='Parent Lot',max_length=30)
  child_lot=forms.CharField(label='Child Lot',max_length=30)
  annotation=forms.CharField(max_length=100,required=False)
  op=forms.CharField(max_length=30)

  def new_data(self):
    data=self.cleaned_data['parent_lot']
    data.append(self.cleaned_data['child_lot'])
    data.append(self.cleaned_data['annotation'])
    data.append(self.cleaned_data['op'])

class ChangeProductForm(forms.Form):
  lot=forms.CharField(label='Lot',max_length=30)
  to_product=forms.CharField(label='To Product',max_length=30)
  to_process_step=forms.CharField(label='To Process Step',max_length=30,required=False)
  annotation=forms.CharField(max_length=100,required=False)
  op=forms.CharField(max_length=30)

  # check input data and find related models
  def clean_lot(self):
    data=self.cleaned_data['lot']
    lot_obj=Lot.objects.filter(name=data)
    if not lot_obj:
      raise ValidationError(_('Product Not Exist'),code='invalid')
    if lot_obj[0].ctrl_state != 'I': #idle state for manual change product
      raise ValidationError(_('Lot State mismatch'),code='invalid')
    else:
      return data

  def clean_to_product(self):
    data=self.cleaned_data['to_product']
    p_obj=Product.objects.filter(name=data,freeze=True,active=True)
    if not p_obj:
      raise ValidationError(_('Product not found'),code='invalid')
    else:
      return data

  def clean_to_process_step(self):
    data=self.cleaned_data['to_process_step']
    ps_obj=ProcessStep.objects.filter(name=data,freeze=True,active=True)
    if not ps_obj:
      return ''
    else:
      return data

  def new_data(self):
    data=self.cleaned_data['lot']
    data.append(self.cleaned_data['to_product'])
    data.append(self.cleaned_data['to_process_step'])
    data.append(self.cleaned_data['annotation'])
    data.append(self.cleaned_data['op'])

class BreakingForm(forms.Form):
  lot=forms.CharField(label='Lot:',max_length=30)
  eq=forms.CharField(label='EQ:',max_length=30)
  annotation=forms.CharField(max_length=100,required=False)
  op=forms.CharField(max_length=30)

  # check input data and find related models
  def clean_lot(self):
    data=self.cleaned_data['lot']
    lot_obj=Lot.objects.filter(name=data)
    if not lot_obj:
      raise ValidationError(_('Lot not found'),code='invalid')
    return data

  def clean_eq(self):
    data=self.cleaned_data['eq']
    eq_obj=Eq.objects.filter(name=data)
    if not eq_obj:
      raise ValidationError(_('EQ not found'),code='invalid')
    return data

  def new_data(self):
    data=self.cleaned_data['lot']
    data.append(self.cleaned_data['eq'])
    data.append(self.cleaned_data['annotation'])
    data.append(self.cleaned_data['op'])

class ChangePWDForm(forms.Form):
  name=forms.CharField(label='User Name:',max_length=30)
  old_pwd=forms.CharField(label='Old Password:',max_length=30)
  new_pwd=forms.CharField(label='New Password:',max_length=30)

  def clean_old_pwd(self):
    data=self.cleaned_data['old_pwd']
    if data.strip()=='':
      raise ValidationError(_('Input Space Only Error'),code='invalid')
    return data

  def clean_new_pwd(self):
    data=self.cleaned_data['new_pwd']
    if data.strip()=='':
      raise ValidationError(_('Input Space Only Error'),code='invalid')
    return data

  def new_data(self):
    data=self.cleaned_data['name']
    data.append(self.cleaned_data['old_pwd'])
    data.append(self.cleaned_data['new_pwd'])
