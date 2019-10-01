from django.db import models
from django.core.validators import MaxValueValidator,MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.conf import settings
# from django.contrib.auth.models import Group
# from django.contrib.sessions.models import Session
from django.db.models import F,Q,When
import logging

# Create your models here.

mylog=logging.getLogger('runMES')

# class UserSession(models.Model):
#   user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
#   session=models.ForeignKey(Session,on_delete=models.CASCADE)
#   start_time=models.DateTimeField(db_index=True,default=timezone.now,null=True,blank=True)
#
#   def __str__(self):
#     return self.user.name
#
# class AccessFunctions(models.Model):
#   name=models.CharField(db_index=True,max_length=30,unique=True)
#   description=models.CharField(max_length=30,blank=True)
#
#   def __str__(self):
#     return self.name
#
# class GroupAccess(models.Model):
#   group=models.ForeignKey(Group,on_delete=models.CASCADE)
#   func=models.ForeignKey(AccessFunctions,on_delete=models.CASCADE)

class LotShipHist(models.Model):
  lot=models.CharField(max_length=30,db_index=True)
  workorder=models.CharField(max_length=30)
  owner=models.CharField(max_length=30,null=True,blank=True)
  grade=models.CharField(max_length=30,null=True,blank=True)
  qty=models.IntegerField()
  ship_date=models.DateTimeField(auto_now=True)
  annotation=models.CharField(max_length=100)

  def __str__(self):
    return self.lot+", date:"+str(self.ship_date)+', qty:'+str(self.qty)


class DcItemCategory(models.Model):
  name=models.CharField(max_length=30,unique=True)
  description=models.CharField(max_length=30,blank=True,null=True)
  data_type_choice=(('I','INTEGER'),('F','FLOAT'),('T','TEXT'),('B','BOOLEAN'))
  data_type=models.CharField(max_length=1,verbose_name='Type',choices=data_type_choice)
  unit=models.CharField(max_length=30)
  #version=models.SmallIntegerField(verbose_name='Ver',db_index=True,default=0)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',default=False)
  freeze=models.BooleanField(verbose_name='Frz',default=False)

  def __str__(self):
    return self.name

class DcItem(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  description=models.CharField(max_length=30,blank=True,null=True)
  dcitem_category=models.ForeignKey(DcItemCategory,verbose_name='Category',on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',default=True)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

class DcItemSpec(models.Model):
  name=models.CharField(max_length=30,db_index=True,unique=True)
  dcitem=models.ForeignKey(DcItem,on_delete=models.CASCADE,verbose_name='Item',limit_choices_to={'freeze':True})
  exact_text=models.CharField(verbose_name='TxtSpec',max_length=30,blank=True,null=True)
  spec_target=models.FloatField(verbose_name='Target',blank=True,null=True)
  spec_high=models.FloatField(verbose_name='SpecH',blank=True,null=True)
  spec_low=models.FloatField(verbose_name='SpecL',blank=True,null=True)
  screen_high=models.FloatField(verbose_name='ScreenH',blank=True,null=True)
  screen_low=models.FloatField(verbose_name='ScreenL',blank=True,null=True)
  OOS_hold_lot=models.BooleanField(verbose_name='HoldLot',default=False)
  OOS_hold_eq=models.BooleanField(verbose_name='HoldEQ',default=False)
  OOS_mail=models.BooleanField(verbose_name='Mail',default=False)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=True)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

class DcPlan(models.Model):
  name=models.CharField(max_length=30,db_index=True,unique=True)
  description=models.CharField(max_length=30,blank=True,null=True)
  dcitems=models.ManyToManyField(DcItem,verbose_name='Items',through='DcPlanDcItem')
  dcitem_spec=models.ManyToManyField(DcItemSpec,verbose_name='Spec',through='DcPlanDcItem',blank=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=False)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

class DcPlanDcItem(models.Model):
  dcplan=models.ForeignKey(DcPlan,on_delete=models.CASCADE,db_index=True)
  dcitems=models.ForeignKey(DcItem,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  dcitem_spec=models.ForeignKey(DcItemSpec,on_delete=models.CASCADE,limit_choices_to={'freeze':True},null=True,blank=True)
  is_required=models.BooleanField(default=True)

  def __str__(self):
    return 'Plan:'+str(self.dcplan.name)+',Item:'+str(self.dcitems.name)

class Breaking(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  new_product=models.ForeignKey('Product',verbose_name='New Prod',on_delete=models.CASCADE)
  break_qty=models.IntegerField(verbose_name='Brk Qty')
  description=models.CharField(max_length=30,blank=True,null=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=False)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

class BinGrade(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  description=models.CharField(max_length=30,blank=True,null=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=True)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

class Binning(models.Model):
  name=models.CharField(max_length=30,db_index=True,unique=True)
  bin_grades=models.ManyToManyField(BinGrade,verbose_name='Bin_Grade',through='Binning_BinGrade')
  description=models.CharField(max_length=30,blank=True,null=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=False)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

class Binning_BinGrade(models.Model):
  binning=models.ForeignKey(Binning,on_delete=models.CASCADE,db_index=True)
  bin_grades=models.ForeignKey(BinGrade,on_delete=models.CASCADE,limit_choices_to={'freeze':True})

class StepCategory(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  description=models.CharField(max_length=30,null=True,blank=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=False)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

class ProcessStep(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  description=models.CharField(max_length=30,null=True,blank=True)
  category=models.ForeignKey(StepCategory,verbose_name='Category',on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  recipe=models.CharField(max_length=30)
  eq_group=models.ForeignKey('EqGroup',verbose_name='EQ Grp',on_delete=models.CASCADE)
  step_check=models.ForeignKey('EqRecord',verbose_name='StepChk',on_delete=models.CASCADE,null=True,blank=True,limit_choices_to={'freeze':True})
  dcplan=models.ForeignKey(DcPlan,verbose_name='DC Plan',related_name='dc_plan',blank=True,null=True,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  breaking=models.ForeignKey(Breaking,verbose_name='Break',blank=True,null=True,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  binning=models.ForeignKey(Binning,verbose_name='Bin',blank=True,null=True,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  instruction=models.TextField(max_length=2048,null=True,blank=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=False)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

  def save(self,*args,**kwargs):
    if self.step_check:
      if self.step_check.eq_group != self.eq_group:
        raise ValidationError('StepChk EQ group is not the same')

    super().save(*args,**kwargs)

class LotRecord(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  description=models.CharField(max_length=30,null=True,blank=True)
  dcplan=models.ForeignKey(DcPlan,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=False)
  freeze=models.BooleanField(verbose_name='frz',db_index=True,default=False)

  def __str__(self):
    return self.name+',DCP:'+str(self.dcplan)

class Process(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  process_step=models.ManyToManyField(ProcessStep,verbose_name='Step',through='ProcessProcessStep')
  description=models.CharField(max_length=30,null=True,blank=True)
  lastupdate=models.DateTimeField(auto_now=True)
  active=models.BooleanField(verbose_name='Act',default=False,db_index=True)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  def __str__(self):
    return self.name

class ProcessProcessStep(models.Model):
  process=models.ForeignKey(Process,on_delete=models.CASCADE)
  process_step=models.ForeignKey(ProcessStep,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  lastupdate=models.DateTimeField(auto_now=True)

  def __str__(self):
    return 'process:'+str(self.process.name)+',step:'+str(self.process_step.name)

class ProcessParameters(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  process=models.ForeignKey(Process,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  data_choices=(('N','NUMERIC'),('T','TEXT'),)
  data_type=models.CharField(max_length=1,choices=data_choices,)
  lastupdate=models.DateTimeField(auto_now=True)
  value=models.CharField(max_length=30,default='')
  active=models.BooleanField(default=False)
  freeze=models.BooleanField(default=False)

  def __str__(self):
    return self.name

class Product(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  process=models.ForeignKey(Process,blank=True,null=True,on_delete=models.CASCADE,limit_choices_to={'active':True,'freeze':True})
  unit=models.CharField(max_length=30)
  description=models.CharField(max_length=30,blank=True,null=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',default=False)
  freeze=models.BooleanField(verbose_name='Frz',default=False)

  def __str__(self):
    return self.name


class ProductParameters(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  product=models.ForeignKey(Product,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  data_choices=(('N','NUMERIC'),('T','TEXT'),)
  data_type=models.CharField(max_length=1,choices=data_choices)
  lastupdate=models.DateTimeField(auto_now=True)
  active=models.BooleanField(default=False)
  freeze=models.BooleanField(default=False)

  def __str__(self):
    return self.name+',prod:'+str(self.product.name)

class WorkOrder(models.Model):
  name=models.CharField(max_length=30,db_index=True,unique=True)
  ERP_ref=models.CharField(max_length=60,db_index=True,blank=True,null=True)
  product=models.ForeignKey(Product,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  lot_type_choices=(('P','Product'),('E','Engineer'),('D','Dummy'),('M','Monitor'))
  lot_type=models.CharField(max_length=1,choices=lot_type_choices,default='P')
  qty=models.IntegerField()
  qty_left=models.IntegerField()
  lot_priority=models.IntegerField(default=3,db_index=True,validators=[MaxValueValidator(5),MinValueValidator(1)],help_text="1-5 High-Low")
  start_date=models.DateTimeField(verbose_name='Start',default=timezone.now)
  target_date=models.DateTimeField(verbose_name='Target',)
  op=models.CharField(max_length=30,blank=True,null=True)
  owner=models.CharField(max_length=30,blank=True,null=True)
  owner_email=models.EmailField()
  owner_phone=models.CharField(max_length=30,blank=True,null=True)
  is_close=models.BooleanField(default=False)
  close_date=models.DateTimeField(null=True,blank=True)
  instruction=models.TextField(max_length=2048,null=True,blank=True)
  annotation=models.CharField(max_length=100,blank=True,null=True)
  active=models.BooleanField(verbose_name='Act')
  freeze=models.BooleanField(verbose_name='Frz')

  def get_absolute_url(self):
    return self.id

  def __str__(self):
    return self.name+',PRD:'+self.product.name

class WorkOrderHist(models.Model):
  name=models.CharField(max_length=30,db_index=True)
  ERP_ref=models.CharField(max_length=60,db_index=True,blank=True,null=True)
  product=models.ForeignKey(Product,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  lot_type_choices=(('P','Product'),('E','Engineer'),('D','Dummy'),('M','Monitor'))
  lot_type=models.CharField(max_length=1,choices=lot_type_choices,default='P')
  qty=models.IntegerField()
  qty_left=models.IntegerField()
  lot_priority=models.IntegerField(default=3,db_index=True,validators=[MaxValueValidator(5),MinValueValidator(1)],help_text="1-5 High-Low")
  start_date=models.DateTimeField(verbose_name='Start',default=timezone.now)
  target_date=models.DateTimeField(verbose_name='Target',)
  op=models.CharField(max_length=30,blank=True,null=True)
  owner=models.CharField(max_length=30,blank=True,null=True)
  owner_email=models.EmailField()
  owner_phone=models.CharField(max_length=30,blank=True,null=True)
  is_close=models.BooleanField(default=False)
  close_date=models.DateTimeField(null=True,blank=True)
  instruction=models.TextField(max_length=2048,null=True,blank=True)
  annotation=models.CharField(max_length=100,blank=True,null=True)
  active=models.BooleanField(verbose_name='Act')
  freeze=models.BooleanField(verbose_name='Frz')
  timestamp=models.DateTimeField(auto_now=True)

class EqGroup(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  description=models.CharField(max_length=30,null=True,blank=True)
  owner_mail=models.EmailField(null=True,blank=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',default=False)
  freeze=models.BooleanField(verbose_name='Frz',default=False)

  def __str__(self):
    return self.name

class EqRecord(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  description=models.CharField(max_length=30,null=True,blank=True)
  eq_group=models.ForeignKey(EqGroup,verbose_name='EQ GRP',on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  instruction=models.TextField(max_length=2000,null=True,blank=True)
  dcplan=models.ForeignKey(DcPlan,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',db_index=True,default=False)
  freeze=models.BooleanField(verbose_name='Frz',db_index=True,default=False)

  # class Meta:
  #   unique_together=('eq_group','active')

  def __str__(self):
    return self.name+',DCP:'+str(self.dcplan)

class Area(models.Model):
  name=models.CharField(db_index=True,max_length=10,unique=True)
  description=models.CharField(max_length=30,blank=True,null=True)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)
  active=models.BooleanField(verbose_name='Act',default=False)
  freeze=models.BooleanField(verbose_name='Frz',default=False)

  def __str__(self):
    return self.name

class Eq(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True)
  description=models.CharField(max_length=30,null=True,blank=True)
  type_choices=(('L','LINE'),('A','STANDALONE'),('S','SUB EQ'),('D','LD_UD'),('T',"TRANSPORTATION"))
  eq_type=models.CharField(max_length=1,choices=type_choices,default='A')
  parent=models.ForeignKey('self',on_delete=True,null=True,blank=True)
  area=models.ForeignKey(Area,db_index=True,null=True,on_delete=models.CASCADE,limit_choices_to={'freeze':True})
  group=models.ForeignKey(EqGroup,on_delete=True,limit_choices_to={'freeze':True})
  ctrl_state_choices=(('RA','Run Available'),('RN','Run Not Available'),('PM','Maintenance'),('ID','Idle'),('DM','Down'),('LN','Lend'),('SU','Setup'))
  ctrl_state=models.CharField(verbose_name='State',max_length=2,db_index=True,choices=ctrl_state_choices,default='ID')
  is_hold=models.BooleanField(verbose_name='Hold',default=False)
  hold_reason=models.CharField(max_length=256,null=True,blank=True)
  is_virtual=models.BooleanField(verbose_name='Virtual',default=False)
  last_product=models.ForeignKey('Product',on_delete=models.CASCADE,blank=True,null=True)
  last_recipe=models.CharField(max_length=30,blank=True,null=True)
  last_eq_record=models.ForeignKey('EqRecord',on_delete=models.CASCADE,blank=True,null=True)
  eq_record_time=models.DateTimeField(blank=True,null=True)
  active=models.BooleanField(verbose_name='Act',default=False)
  freeze=models.BooleanField(verbose_name='Frz',default=False)
  lastupdate=models.DateTimeField(verbose_name='Update',auto_now=True)

  def get_absolute_url(self):
    return self.id

  def __str__(self):
    return str(self.name)

class Lot(models.Model):
  name=models.CharField(db_index=True,max_length=30,unique=True,verbose_name='LotID')
  product=models.ForeignKey(Product,on_delete=models.CASCADE,null=True,blank=True)
  ctrl_state_choices=(('R','Run'),('I','Idle'),('F','Finish'),('S','Ship'),('T','Terminate'),('B','Bank'))
  ctrl_state=models.CharField(max_length=1,db_index=True,choices=ctrl_state_choices,default='I')
  is_active=models.BooleanField(db_index=True,default=True)
  is_hold=models.BooleanField(default=False)
  hold_reason=models.CharField(max_length=256,null=True,blank=True)
  is_finish=models.BooleanField(default=False,db_index=True)
  step_recipe=models.CharField(verbose_name='Recipe',max_length=30,null=True,blank=True)
  step_check=models.CharField(verbose_name='StepChk',max_length=30,null=True,blank=True)
  step_dcplan=models.CharField(verbose_name='DcPlan',max_length=30,null=True,blank=True)
  step_product=models.CharField(verbose_name='StepProduct',max_length=30,null=True,blank=True)
  step_binning=models.CharField(verbose_name='Bin',max_length=30,null=True,blank=True)
  step_breaking=models.CharField(verbose_name='Break',max_length=30,null=True,blank=True)
  workorder=models.CharField(verbose_name='WO',db_index=True,max_length=30)
  qty=models.IntegerField()
  operation_choices=(('SC','StepCheck'),('SI','StepIn'),('SO','StepOut'),('DC','DC'),('BK','Breaking'),('BI','Binning'),('NP','New Product'),('NO','None'))
  next_operation=models.CharField(verbose_name='Next OP',max_length=2,db_index=True,choices=operation_choices,blank=True)
  process=models.ForeignKey(Process,db_index=True,null=True,blank=True,default=None,on_delete=models.PROTECT)
  process_step=models.ForeignKey(ProcessStep,verbose_name='Step',db_index=True,null=True,blank=True,default=None,on_delete=models.PROTECT)
  location_choices=(('F','InFab'),('E','InEQ'),('O','OutSide'))
  curr_location=models.CharField(max_length=1,db_index=True,choices=location_choices)
  curr_area=models.ForeignKey(Area,db_index=True,null=True,blank=True,default=None,on_delete=models.PROTECT)
  curr_eq=models.ForeignKey(Eq,db_index=True,null=True,blank=True,on_delete=models.PROTECT)
  start_time=models.DateTimeField(db_index=True,default=timezone.now,null=True,blank=True)
  target_time=models.DateTimeField(null=True,blank=True,db_index=True)
  lot_priority=models.IntegerField(default=3,db_index=True,validators=[MaxValueValidator(5),MinValueValidator(1)])
  run_id=models.UUIDField(blank=True,null=True,db_index=True)
  owner=models.CharField(max_length=30,null=True,blank=True)
  component_map_uuid=models.UUIDField(null=True,blank=True)
  type_choices=(('P','Product'),('E','Engineer'),('D','Dummy'),('M','Monitor'))
  lot_type=models.CharField(max_length=1,choices=type_choices,default='P')
  lot_grade=models.CharField(max_length=30,blank=True,null=True)
  last_step_uuid=models.UUIDField(null=True,blank=True)
  last_step=models.CharField(max_length=2,blank=True,null=True)
  last_step_time=models.DateTimeField(blank=True,null=True)
  owner_mail=models.EmailField(null=True,blank=True)

  def get_absolute_url(self):
    return self.id

  def __str__(self):
    return self.name

# current component info
class Component(models.Model):
  comp_id=models.CharField(max_length=30,db_index=True,unique=True,verbose_name='ComponentID')
  lastupdate=models.DateTimeField(db_index=True,auto_now=True)
  product=models.CharField(max_length=30)
  lot=models.ForeignKey(Lot,db_index=True,on_delete=True,null=True,blank=True)
  alias=models.CharField(db_index=True,max_length=30,unique=True,null=True,blank=True)

class ComponentMapHist(models.Model):
  comp_id=models.CharField(max_length=30,db_index=True,unique=True,verbose_name='ComponentID')
  lastupdate=models.DateTimeField(db_index=True,auto_now=True)
  product=models.CharField(max_length=30)
  lot=models.CharField(max_length=30,db_index=True)
  alias=models.CharField(db_index=True,max_length=30,unique=True,null=True,blank=True)
  component_map_uuid=models.UUIDField(null=True,db_index=True)

class LotStepHist(models.Model):
  lot=models.CharField(max_length=30,db_index=True)
  eq=models.CharField(max_length=30,db_index=True,null=True,blank=True)
  qty=models.CharField(max_length=30,null=True,blank=True)
  op=models.CharField(max_length=30,null=True,blank=True)
  recipe=models.CharField(max_length=30,null=True,blank=True)
  product=models.CharField(max_length=30,null=True,blank=True)
  process=models.CharField(max_length=30,null=True,blank=True)
  process_step=models.CharField(max_length=30,null=True,blank=True)
  transaction=models.CharField(max_length=30,db_index=True,null=True,blank=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  trans_time=models.DateTimeField(auto_now=True)
  run_id=models.UUIDField(blank=True,null=True,db_index=True)
  annotation=models.CharField(max_length=100,null=True,blank=True)
  component_map_uuid=models.UUIDField(null=True,blank=True)

  def __str__(self):
    return str(self.id)+'-'+str(self.trans_time)+':'+str(self.lot)+','+str(self.eq)

class EqStateHist(models.Model):
  eq=models.CharField(max_length=30,db_index=True)
  op=models.CharField(max_length=30,null=True,blank=True)
  ctrl_state=models.CharField(max_length=2,null=True,blank=True)
  transaction=models.CharField(max_length=30,db_index=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  trans_time=models.DateTimeField(auto_now=True)
  annotation=models.CharField(max_length=100,null=True,blank=True)

  def __str__(self):
    return str(self.id)+','+str(self.eq)

class EqHoldHist(models.Model):
  eq=models.CharField(max_length=30,db_index=True)
  op=models.CharField(max_length=30,null=True,blank=True)
  hold_release_choices=(('H',"Hold"),('R','Release'))
  hold_release=models.CharField(max_length=1,choices=hold_release_choices)
  hold_code=models.CharField(max_length=30,null=True,blank=True)
  release_code=models.CharField(max_length=30,null=True,blank=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  annotation=models.CharField(max_length=100,null=True,blank=True)
  timestamp=models.DateTimeField(auto_now=True)


class DcPlanHist(models.Model):
  dcplan=models.CharField(max_length=30,db_index=True)
  transaction=models.CharField(max_length=30,db_index=True,null=True,blank=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  op=models.CharField(max_length=30,null=True,blank=True)
  #trans_type 'S':step dc, 'R':Lot record, 'E':EQ record
  trans_type=models.CharField(max_length=1,db_index=True,default="U",null=True,blank=True)
  lot=models.CharField(max_length=30,db_index=True,blank=True,null=True)
  eq=models.CharField(max_length=30,db_index=True,blank=True,null=True)
  trans_time=models.DateTimeField(auto_now=True)
  device_time=models.DateTimeField(blank=True,null=True)
  step=models.CharField(max_length=30,db_index=True,blank=True,null=True)
  #step_in_id=models.CharField(max_length=30,db_index=True,blank=True)
  run_id=models.UUIDField(blank=True,null=True,db_index=True)
  annotation=models.CharField(max_length=100,blank=True,null=True)

  def __str__(self):
    return self.dcplan

class DcValueHist(models.Model):
  dcplan_hist=models.ForeignKey(DcPlanHist,on_delete=models.CASCADE)
  dcitem=models.CharField(max_length=30,db_index=True)
  category=models.CharField(max_length=30,db_index=True)
  datatype=models.CharField(max_length=30)
  unit=models.CharField(max_length=30)
  value=models.CharField(max_length=30)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  trans_time=models.DateTimeField(auto_now=True)

  def __str__(self):
    return str(self.dcplan_hist)+','+str(self.dcitem)+','+str(self.value)

class CheckSpecHist(models.Model):
  dcitem_spec=models.CharField(max_length=30,db_index=True)
  dcplan=models.CharField(max_length=30)
  dcitem=models.CharField(max_length=30,db_index=True,)
  violation=models.CharField(max_length=30,blank=True,null=True)
  val=models.CharField(max_length=30,blank=True,null=True)
  lot=models.CharField(max_length=30,db_index=True,blank=True,null=True)
  eq=models.CharField(max_length=30,db_index=True,blank=True,null=True)
  exact_text=models.CharField(max_length=30,blank=True,null=True)
  spec_target=models.CharField(max_length=30,blank=True,null=True)
  spec_high=models.CharField(max_length=30,blank=True,null=True)
  spec_low=models.CharField(max_length=30,blank=True,null=True)
  OOS_hold_lot=models.BooleanField()
  OOS_hold_eq=models.BooleanField()
  OOS_mail=models.BooleanField()
  hold_lot=models.CharField(max_length=30,null=True,blank=True)
  hold_eq=models.CharField(max_length=30,null=True,blank=True)
  send_mail=models.CharField(max_length=60,null=True,blank=True)
  trans_time=models.DateTimeField(auto_now=True)
  step=models.CharField(max_length=30,db_index=True,blank=True,null=True)
  run_id=models.UUIDField(blank=True,null=True,db_index=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  op=models.CharField(max_length=30,null=True,blank=True)
  annotation=models.CharField(max_length=100,blank=True,null=True)

  def __str__(self):
    return self.dcitem_spec

class LotStartHist(models.Model):
  work_order=models.CharField(max_length=30,db_index=True)
  lot=models.CharField(max_length=30,db_index=True,unique=True)
  qty=models.IntegerField()
  op=models.CharField(max_length=30,null=True,blank=True)
  type=models.CharField(max_length=1,blank=True)
  start_date=models.DateTimeField(auto_now=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  annotation=models.CharField(max_length=100)
  component_map_uuid=models.UUIDField(null=True,blank=True)

  def __str__(self):
    return self.work_order+", "+self.lot+", "+str(self.qty)

class LotHoldHist(models.Model):
  lot=models.CharField(max_length=30,db_index=True)
  op=models.CharField(max_length=30)
  hold_release_choices=(('H',"Hold"),('R','Release'))
  hold_release=models.CharField(max_length=1,choices=hold_release_choices)
  hold_code=models.CharField(max_length=30,null=True,blank=True)
  release_code=models.CharField(max_length=30,null=True,blank=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  run_id=models.UUIDField(blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  annotation=models.CharField(max_length=100,null=True,blank=True)
  timestamp=models.DateTimeField(auto_now=True)

class LotCtrlStateHist(models.Model):
  lot=models.CharField(max_length=30,db_index=True)
  timestamp=models.DateTimeField(auto_now=True)
  ctrl_state=models.CharField(max_length=2,blank=True,null=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  run_id=models.UUIDField(blank=True,null=True)
  op=models.CharField(max_length=30)
  annotation=models.CharField(max_length=100)

class LotBinHist(models.Model):
  lot=models.CharField(max_length=30,db_index=True)
  binning=models.CharField(max_length=30)
  bin_grade=models.CharField(max_length=30)
  qty=models.IntegerField()
  run_id=models.UUIDField(blank=True,null=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  timestamp=models.DateTimeField(auto_now=True)
  op=models.CharField(max_length=30)
  annotation=models.CharField(max_length=100)

class BreakingHist(models.Model):
  lot=models.CharField(max_length=30,db_index=True)
  eq=models.CharField(max_length=30,db_index=True,blank=True,null=True)
  breaking=models.CharField(max_length=30)
  from_qty=models.IntegerField()
  to_qty=models.IntegerField()
  from_product=models.CharField(max_length=30)
  to_product=models.CharField(max_length=30)
  run_id=models.UUIDField(blank=True,null=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  timestamp=models.DateTimeField(auto_now=True)
  op=models.CharField(max_length=30)
  annotation=models.CharField(max_length=100)

class ProductChangeHist(models.Model):  # assign to new product in process
  from_product=models.CharField(max_length=30,db_index=True)
  from_process=models.CharField(max_length=30)
  from_process_step=models.CharField(max_length=30)
  from_lot=models.CharField(max_length=30,db_index=True)
  from_lot_ctrl_state=models.CharField(max_length=30)
  to_product=models.CharField(max_length=30,db_index=True)
  to_process=models.CharField(max_length=30,null=True,blank=True)
  to_process_step=models.CharField(max_length=30,null=True,blank=True)
  run_id=models.UUIDField(blank=True,null=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  op=models.CharField(max_length=30)
  annotation=models.CharField(max_length=100)
  trans_time=models.DateTimeField(auto_now=True)


# split/merge
class LotSplitMergeHist(models.Model):
  parent_lot=models.CharField(max_length=30)
  parent_qty=models.IntegerField()
  child_lot=models.CharField(max_length=30)
  child_qty=models.IntegerField()
  op=models.CharField(max_length=30)
  split_merge_choices=(('S','Split'),('M','Merge'))
  split_merge=models.CharField(max_length=1,choices=split_merge_choices)
  parent_step_uuid=models.UUIDField(null=True,blank=True)
  child_step_uuid=models.UUIDField(null=True,blank=True)
  run_id=models.UUIDField(blank=True,null=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  trans_time=models.DateTimeField(default=timezone.now)
  annotation=models.CharField(max_length=100)

class BonusScrapCode(models.Model):
  name=models.CharField(max_length=30,db_index=True,unique=True)
  bonus_scrap_choice=(('B','Bonus'),('S','Scrap'))
  bonus_scrap=models.CharField(max_length=1,choices=bonus_scrap_choice,db_index=True)
  description=models.CharField(max_length=100,null=True,blank=True)
  lastupdate=models.DateTimeField(auto_now=True)
  active=models.BooleanField(default=True)
  freeze=models.BooleanField()

  def __str__(self):
    return self.name+','+self.bonus_scrap

class LotHoldReleaseCode(models.Model):
  name=models.CharField(max_length=30,db_index=True,unique=True)
  hold_release_choice=(('H','Hold'),('R','Release'))
  hold_release=models.CharField(max_length=1,choices=hold_release_choice,db_index=True)
  description=models.CharField(max_length=100,null=True,blank=True)
  lastupdate=models.DateTimeField(auto_now=True)
  active=models.BooleanField(default=True)
  freeze=models.BooleanField()

  def __str__(self):
    return self.name+','+self.hold_release

class EqHoldReleaseCode(models.Model):
  name=models.CharField(max_length=30,db_index=True,unique=True)
  hold_release_choice=(('H','Hold'),('R','Release'))
  hold_release=models.CharField(max_length=1,choices=hold_release_choice,db_index=True)
  description=models.CharField(max_length=100,null=True,blank=True)
  lastupdate=models.DateTimeField(auto_now=True)
  active=models.BooleanField(default=True)
  freeze=models.BooleanField()

  def __str__(self):
    return self.name+','+self.hold_release

class BonusScrapHist(models.Model):
  lot=models.CharField(max_length=30,db_index=True)
  process_step=models.CharField(max_length=30,null=True,blank=True)
  lot_state=models.CharField(max_length=2,null=True,blank=True)
  eq=models.CharField(max_length=30,null=True,blank=True)
  bonus_scrap=models.CharField(max_length=10)
  lot_old_qty=models.IntegerField()
  bonus_scrap_qty=models.IntegerField()
  code=models.CharField(max_length=30)
  op=models.CharField(max_length=30)
  run_id=models.UUIDField(null=True,blank=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  annotation=models.CharField(max_length=100,null=True,blank=True)
  trans_time=models.DateTimeField(auto_now=True)

class LotTerminateHist(models.Model):
  lot=models.CharField(max_length=30,db_index=True)
  work_order=models.CharField(max_length=30,db_index=True)
  product=models.CharField(max_length=30)
  process=models.CharField(max_length=30)
  process_step=models.CharField(max_length=30)
  op=models.CharField(max_length=30)
  run_id=models.UUIDField(null=True,blank=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  annotation=models.CharField(max_length=100,null=True,blank=True)
  trans_time=models.DateTimeField(auto_now=True)

class MailQueue(models.Model):
  receiver=models.EmailField()
  level_choices=(('A','Alert'),('I','Info'),('W','Warning'))
  level=models.CharField(max_length=1,choices=level_choices)
  subject=models.CharField(max_length=100)
  contents=models.CharField(max_length=2048)
  record_timestamp=models.DateTimeField(auto_now=True)
  is_overdue=models.BooleanField(default=False,db_index=True)
  is_deliver=models.BooleanField(default=False,db_index=True)
  first_timestamp=models.DateTimeField(blank=True,null=True)
  deliver_timestamp=models.DateTimeField(blank=True,null=True)
  transaction=models.CharField(max_length=30,blank=True,null=True)
  tid=models.CharField(max_length=40,db_index=True,null=True,blank=True)
  annotation=models.CharField(max_length=100,blank=True)

class AlarmHist(models.Model):
  alarm_id=models.CharField(max_length=30,db_index=True)
  alarm_txt=models.CharField(max_length=300,blank=True)
  set_clear=models.BooleanField(blank=True)
  source=models.CharField(max_length=30,db_index=True,blank=True)
  category=models.CharField(max_length=30,db_index=True,blank=True)
  timestamp=models.DateTimeField(auto_now=True)
  device_time=models.DateTimeField(blank=True,null=True)
  annotation=models.CharField(max_length=300,blank=True)

class LotPriorityHist(models.Model):
  lot=models.CharField(max_length=30)
  new_priority=models.IntegerField()
  old_priority=models.IntegerField()
  op=models.CharField(max_length=30)
  annotation=models.CharField(max_length=100,blank=True)
  timestamp=models.DateTimeField(auto_now=True)

class ModelImportLog(models.Model):
  name=models.CharField(max_length=30)
  contents=models.TextField(max_length=2048)
  timestamp=models.DateTimeField(auto_now=True)

class TextTest(models.Model):
  name=models.CharField(max_length=30)
  instruction=models.TextField(max_length=2000,null=True,blank=True)
