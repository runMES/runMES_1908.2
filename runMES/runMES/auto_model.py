# *** this program is use for the empty modeling creation or for testing purpose, it sould avoid to use on a production environment ***

from runMES.models import *
from django.db import transaction
import logging

mylog=logging.getLogger('runMES')

#DcItemCatetory [[name,description,data_type,unit],..]
DcItemCategorySet=[['DEMO-AOI-Line','','F','MIL'],['DEMO-Reflow-Temp','','F','Degree C'],['DEMO-Etch-S.G.','','F','S.G.'],['DEMO-Etch-Temp','','F','Degree C'],['DEMO-Etch-Air Pressure','','I','PSI'],['DEMO-PH','','F','PH'],['DEMO-PN','','T','PN'],['DEMO-SN','','T','SN']]

#DcItem [[name,description,dcitem_catecatory],..]
DcItemSet=[['DEMO-AOI-Width','','DEMO-AOI-Line'],['DEMO-AOI-Offset','','DEMO-AOI-Line'],['DEMO-Reflow-1','','DEMO-Reflow-Temp'],['DEMO-Reflow-2','','DEMO-Reflow-Temp'],['DEMO-Etch-S.G.','','DEMO-Etch-S.G.'],['DEMO-Etch-Temp-1','','DEMO-Etch-Temp'],['DEMO-Etch-Temp-2','','DEMO-Etch-Temp'],['DEMO-Etch-Air Pressure-1','','DEMO-Etch-Air Pressure'],['DEMO-Etch-Air Pressure-2','','DEMO-Etch-Air Pressure'],['DEMO-Base-PN','','DEMO-PN'],['DEMO-Copper-PN','','DEMO-PN'],['DEMO-Base-SN','','DEMO-SN'],['DEMO-Copper-SN','','DEMO-SN']]


#DcItemSpec [[name,dc_item,exact_text,spec_high,spec_low,OOS_hold_lot,OOS_hold_eq,OOS_mail],..]
DcItemSpecSet=[['DEMO-AOI-Width','DEMO-AOI-Width','','20','15','TRUE','FALSE','TRUE'],['DEMO-AOI-Offset','DEMO-AOI-Offset','','15','10','FALSE','FALSE','FALSE'],['DEMO-Reflow-1','DEMO-Reflow-1','','120','100','FALSE','TRUE','TRUE'],['DEMO-Reflow-2','DEMO-Reflow-2','','120','100','FALSE','FALSE','FALSE'],['DEMO-Etch-S.G.','DEMO-Etch-S.G.','','1.2','1.3','FALSE','TRUE','TRUE'],['DEMO-Base-PN','DEMO-Base-PN','BASE-PN-001','','','FALSE','TRUE','TRUE']]

#DcPlan [[name	description	[dc_item	dc_spec],..],..]
DcPlanSet=[['DEMO-AOI','',['DEMO-AOI-Width','DEMO-AOI-Width'],['DEMO-AOI-Offset','DEMO-AOI-Offset']],['DEMO-Reflow','',['DEMO-Reflow-1','DEMO-Reflow-1'],['DEMO-Reflow-2','DEMO-Reflow-2']],['DEMO-Etch','',['DEMO-Etch-S.G.','DEMO-Etch-S.G.'],['DEMO-Etch-Temp-1',''],['DEMO-Etch-Temp-2',''],['DEMO-Etch-Air Pressure-1',''],['DEMO-Etch-Air Pressure-2','']],['DEMO-Kitting','',['DEMO-Base-PN',''],['DEMO-Copper-PN',''],['DEMO-Base-SN',''],['DEMO-Copper-SN','']]]

#for Stress test
ST_DcPlanSet=[['ST-AOI','',['DEMO-AOI-Width',''],['DEMO-AOI-Offset','']],['ST-Reflow','',['DEMO-Reflow-1',''],['DEMO-Reflow-2','']],['ST-Etch','',['DEMO-Etch-S.G.',''],['DEMO-Etch-Temp-1',''],['DEMO-Etch-Temp-2',''],['DEMO-Etch-Air Pressure-1',''],['DEMO-Etch-Air Pressure-2','']],['ST-Kitting','',['DEMO-Base-PN',''],['DEMO-Copper-PN','']]]

#Area [[name,description],..]
AreaSet=[['F1',''],['F2','']]

#EqGroup [[name,description,owner_mail],..]
EqGroupSet=[['DEMO-AOI','',''],['DEMO-Reflow','',''],['DEMO-Etch','',''],['DEMO-Kitting','',''],['DEMO-Break','','test@steptech.io'],['DEMO-Bin','','test@steptech.io']]

#for Stress test
ST_EqGroupSet=[['ST-AOI','','test@steptech.io'],['ST-Reflow','','test@steptech.io'],['ST-Etch','','test@steptech.io'],['ST-Kitting','','test@steptech.io'],['ST-Break','','test@steptech.io'],['ST-Bin','','test@steptech.io'],['ST-Plating','','test@steptech.io']]


#Eq [[name,description,eq_type,parent,area,eq_group],..]
EqSet=[['DEMO-AOI-01','','A','','F1','DEMO-AOI'],['DEMO-AOI-02','','A','','F1','DEMO-AOI'],['DEMO-Reflow-01','','A','','F1','DEMO-Reflow'],['DEMO-Reflow-02','','A','','F1','DEMO-Reflow'],['DEMO-Etch-01','','A','','F1','DEMO-Etch'],['DEMO-Etch-02','','A','','F1','DEMO-Etch'],['DEMO-Kitting-01','','A','','F1','DEMO-Kitting'],['DEMO-Kitting-02','','A','','F1','DEMO-Kitting'],['DEMO-Break-01','','A','','F2','DEMO-Break'],['DEMO-Break-02','','A','','F2','DEMO-Break'],['DEMO-Bin-01','','A','','F1','DEMO-Bin'],['DEMO-Bin-02','','A','','F1','DEMO-Bin']]

#for stress
ST_EqSet=[['ST-AOI-01','','A','','F1','ST-AOI'],['ST-Reflow-01','','A','','F1','ST-Reflow'],['ST-Etch-01','','A','','F1','ST-Etch'],['ST-Kitting-01','','A','','F1','ST-Kitting'],['ST-Break-01','','A','','F2','ST-Break'],['ST-Bin-01','','A','','F1','ST-Bin'],['ST-Plating-01','','A','','F1','ST-Plating']]

#LotRecord [[name,description,dcplan],..]
LotRecordSet=[['DEMO-AOI','','DEMO-AOI']]

#for Stress test
ST_LotRecordSet=[['ST-AOI','','ST-AOI']]

#EqRecord [[name,description,instruction,eq_group,dcplan],..]
EqRecordSet=[['DEMO-Etch','','Daily check instruction','DEMO-Etch','DEMO-Etch']]

#for stress test
ST_EqRecordSet=[['ST-Reflow','','Daily check instruction','ST-Reflow','ST-Reflow']]

#BinGrade [[name,description],..]
BinGradeSet=[['DEMO-Grade-A',''],['DEMO-Grade-B',''],['DEMO-Grade-C',''],['DEMO-Grade-NG','']]

#for stress test
ST_BinGradeSet=[['ST-Grade-A',''],['ST-Grade-B',''],['ST-Grade-C',''],['ST-Grade-NG','']]

#Binning [[name,description,[bin_grade,..]],..]
BinningSet=[['DEMO-Bin','',['DEMO-Grade-A','DEMO-Grade-B','DEMO-Grade-C','DEMO-Grade-NG']]]

#for stress test
ST_BinningSet=[['ST-Bin','',['ST-Grade-A','ST-Grade-B','ST-Grade-C','ST-Grade-NG']]]

#Breaking [[name,description,break_qty,new_product],..]
BreakingSet=[['DEMO-Break','','1000','DEMO-LED-Chip']]

#for stress test
ST_BreakingSet=[['ST-Break','','1000','ST-LED-Chip']]

#StepCategory [[name,description],..]
StepCategorySet=[['DEMO-AOI',''],['DEMO-Reflow',''],['DEMO-Etch',''],['DEMO-Kitting',''],['DEMO-Break',''],['DEMO-Bin','']]

#for stress test
ST_StepCategorySet=[['ST-AOI',''],['ST-Reflow',''],['ST-Etch',''],['ST-Kitting',''],['ST-Break',''],['ST-Bin',''],['ST-Plating','']]

#ProcessStep [[name,description,recipe,instruction,eq_group,category,step_check,dcplan,breaking,binning],..]
ProcessStepSet=[['DEMO-AOI','','DEMO-AOI','AOI instruction','DEMO-AOI','DEMO-AOI','','DEMO-AOI','',''],['DEMO-Reflow','','DEMO-Reflow','Reflow instruction','DEMO-Reflow','DEMO-Reflow','','DEMO-Reflow','',''],['DEMO-Etch','','DEMO-Etch','Etch instruction','DEMO-Etch','DEMO-Etch','DEMO-Etch','','',''],['DEMO-Kitting','','DEMO-Kitting','Kitting instruction','DEMO-Kitting','DEMO-Kitting','','DEMO-Kitting','',''],['DEMO-Break','','DEMO-Break','Break instruction','DEMO-Break','DEMO-Break','','','DEMO-Break','']]
ProcessStepBinSet=[['DEMO-Bin','','DEMO-Bin','Binning instruction','DEMO-Bin','DEMO-Bin','','','','DEMO-Bin']]

#for stress test
ST_ProcessStepSet=[['ST-AOI','','ST-AOI','AOI instruction','ST-AOI','ST-AOI','','ST-AOI','',''],['ST-Reflow','','ST-Reflow','Reflow instruction','ST-Reflow','ST-Reflow','','ST-Reflow','',''],['ST-Etch','','ST-Etch','Etch instruction','ST-Etch','ST-Etch','','','',''],['ST-Kitting','','ST-Kitting','Kitting instruction','ST-Kitting','ST-Kitting','','ST-Kitting','',''],['ST-Break','','ST-Break','Break instruction','ST-Break','ST-Break','','','ST-Break',''],['ST-Plating','','ST-Plating','Plating instruction','ST-Plating','ST-Plating','','','','']]
ST_ProcessStepBinSet=[['ST-Bin','','ST-Bin','Binning instruction','ST-Bin','ST-Bin','','','','ST-Bin']]


#Process [[name,description,[process_step,..]],..]
ProcessSet=[['DEMO-PCB','',['DEMO-Kitting','DEMO-Etch','DEMO-Reflow','DEMO-AOI']],['DEMO-LED-WF','',['DEMO-Break']]]
ProcessLEDChipSet=[['DEMO-LED-Chip','',['DEMO-Bin']]]

#for stress test
ST_ProcessSet=[['ST-LED-WF','',['ST-Kitting','ST-Plating','ST-Etch','ST-AOI','ST-Break']]]
ST_ProcessLEDChipSet=[['ST-LED-Chip','',['ST-Bin']]]

#Product [[name,description,unit,process],..]
ProductSet=[['DEMO-PCB','','Panel','DEMO-PCB'],['DEMO-LED-WF','','Wafer','DEMO-LED-WF']]
ProductBreakSet=[['DEMO-LED-Chip','','Chip','DEMO-LED-Chip']]

#for stress test
ST_ProductSet=[['ST-LED-WF','','Wafer','ST-LED-WF']]
ST_ProductBreakSet=[['ST-LED-Chip','','Chip','ST-LED-Chip']]


#BunusScrap [[name,description,bonus_scrap],..]
BonusScrapCodeSet=[['B1-Found','','B'],['B2-Repaired','','B'],['B3-Re-Test-OK','','B'],['S1-OOS','','S'],['S2-Broken','','S'],['S3-Lost','','S']]

#LotHoldRelease [[name,description,hold_release],..]
LotHoldReleaseCodeSet=[['LH1-OOS','','H'],['LH2-Engineer-Hold','','H'],['LH3-Customer-Hold','','H'],['LR1-Re-Test-OK','','R'],['LR2-Engineer-Release','','R'],['LR3-Customer-Release','','R']]

#EqHoldRelease [[name,description,hold_release],..]
EqHoldReleaseCodeSet=[['EH1-EQ-Check','','H'],['EH2-EQ-Down','','H'],['EH3-EQ-OOS','','H'],['EH4-Engineer-Hold','','H'],['ER1-EQ-Recovered','','R'],['ER2-Engineer-Release','','R']]

def imp_dcitem_cat(dcitem_cat_set):
  imp='imp_dcitem_cat'
  mylog.debug({'IMP':imp,'input':dcitem_cat_set})
  for rec in dcitem_cat_set:
    mylog.debug({'IMP':imp,'rec':rec})
    name=rec[0]
    description=rec[1]
    if description=='':
      description=None
    data_type=rec[2]
    unit=rec[3]
    obj=DcItemCategory.objects.create(name=name,description=description,data_type=data_type,unit=unit,active=True,freeze=True)
    #obj.save()
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_dcitem(dcitem_set):
  imp='imp_dcitem'
  mylog.debug({'IMP':imp,'input':dcitem_set})

  for item in dcitem_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    dcitem_category=item[2]
    cat_obj=DcItemCategory.objects.get(name=dcitem_category)
    obj=DcItem.objects.create(name=name,description=description,dcitem_category=cat_obj,active=True,freeze=True)
    #obj.save()
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})


def imp_dcitem_spec(dcitem_spec_set):
  imp='imp_dcitem_spec'
  mylog.debug({'IMP':imp,'input':dcitem_spec_set})
  for item in dcitem_spec_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    dcitem=item[1]
    dcitem_obj=DcItem.objects.get(name=dcitem)
    exact_text=item[2]
    if exact_text=='':
      exact_text=None
    data_type=dcitem_obj.dcitem_category.data_type
    s_high=item[3]
    s_low=item[4]
    spec_high=None
    spec_low=None
    if data_type=='F':
      spec_high=float(s_high)
      spec_low=float(s_low)
    elif data_type=='I':
      spec_h=int(s_high)
      spec_l=int(s_low)
      spec_high=float(spec_h)
      spec_low=float(spec_l)

    OOS_hold_lot=item[5]
    if OOS_hold_lot=='':
      OOS_hold_lot=None
    elif OOS_hold_lot=='TRUE':
      OOS_hold_lot=True
    elif OOS_hold_lot=='FALSE':
      OOS_hold_lot=False
    else:
      raise Exception('data type Err - OOS_hold_lot')

    OOS_hold_eq=item[6]
    if OOS_hold_eq=='':
      OOS_hold_eq=None
    elif OOS_hold_eq=='TRUE':
      OOS_hold_eq=True
    elif OOS_hold_eq=='FALSE':
      OOS_hold_eq=False
    else:
      raise Exception('data type Err - OOS_hold_eq')

    OOS_mail=item[7]
    if OOS_mail=='':
      OOS_mail=None
    elif OOS_mail=='TRUE':
      OOS_mail=True
    elif OOS_mail=='FALSE':
      OOS_mail=False
    else:
      raise Exception('data type Err - OOS_mail')

    obj=DcItemSpec.objects.create(name=name,dcitem=dcitem_obj,exact_text=exact_text,spec_high=spec_high,spec_low=spec_low,OOS_hold_lot=OOS_hold_lot,OOS_hold_eq=OOS_hold_eq,OOS_mail=OOS_mail,active=True,freeze=True)
    #obj.save()

  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_dcplan(dcplan_set):
  imp='imp_dcplan'
  mylog.debug({'IMP':imp,'input':dcplan_set})
  for rec in dcplan_set:
    mylog.debug({'IMP':imp,'rec':rec})
    name=rec[0]
    description=rec[1]
    if description=='':
      description=None
    plan_obj=DcPlan.objects.create(name=name,description=description,active=True,freeze=True)
    #plan_obj.save()
    count=len(rec)
    inx=2
    while inx<count:
      dc_item=rec[inx][0]
      dc_item_obj=DcItem.objects.get(name=dc_item)
      dc_spec=rec[inx][1]
      if dc_spec=='':
        dc_spec_obj=None
      else:
        dc_spec_obj=DcItemSpec.objects.get(name=dc_spec)
      plan_item_obj=DcPlanDcItem.objects.create(dcplan=plan_obj,dcitems=dc_item_obj,dcitem_spec=dc_spec_obj)
      #plan_item_obj.save()
      inx=inx+1

    mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_area(area_set):
  imp='imp_area'
  mylog.debug({'IMP':imp,'input':area_set})
  for rec in area_set:
    mylog.debug({'IMP':imp,'rec':rec})
    name=rec[0]
    description=rec[1]
    if description=='':
      description=None

    obj=Area.objects.create(name=name,description=description,active=True,freeze=True)
    obj.save()
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_eq_group(eq_group_set):
  imp='eq_group'
  mylog.debug({'IMP':imp,'input':eq_group_set})
  for rec in eq_group_set:
    mylog.debug({'IMP':imp,'rec':rec})
    name=rec[0]
    description=rec[1]
    owner_mail=rec[2]
    if description=='':
      description=None
    if owner_mail=='':
      owner_mail=None

    EqGroup.objects.create(name=name,description=description,owner_mail=owner_mail,active=True,freeze=True)

  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_eq(eq_set):
  imp='imp_eq'
  mylog.debug({'IMP':imp,'input':eq_set})

  for item in eq_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    eq_type=item[2]
    parent=item[3]
    if parent=='':
      parent_obj=None
    else:
      parent_obj=Eq.objects.get(name=parent)
    area=item[4]
    area_obj=Area.objects.get(name=area)
    eq_group=item[5]
    eq_group_obj=EqGroup.objects.get(name=eq_group)

    obj=Eq.objects.create(name=name,description=description,eq_type=eq_type,parent=parent_obj,area=area_obj,group=eq_group_obj,active=True,freeze=True)
    #obj.save()
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_lot_record(lot_record_set):
  imp='imp_lot_record'
  mylog.debug({'IMP':imp,'input':lot_record_set})

  for item in lot_record_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    dcplan=item[2]
    dcplan_obj=DcPlan.objects.get(name=dcplan)
    obj=LotRecord.objects.create(name=name,description=description,dcplan=dcplan_obj,active=True,freeze=True)
    obj.save()
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_eq_record(eq_record_set):
  imp='imp_eq_record'
  mylog.debug({'IMP':imp,'input':eq_record_set})

  for item in eq_record_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    instruction=item[2]
    if instruction=='':
      instruction=None
    eq_group=item[3]
    eq_group_obj=EqGroup.objects.get(name=eq_group)
    dcplan=item[4]
    dcplan_obj=DcPlan.objects.get(name=dcplan)
    EqRecord.objects.create(name=name,description=description,instruction=instruction,eq_group=eq_group_obj,dcplan=dcplan_obj,active=True,freeze=True)
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_bin_grade(bin_grade_set):
  imp='imp_bin_grade'
  mylog.debug({'IMP':imp,'input':bin_grade_set})

  for item in bin_grade_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    obj=BinGrade.objects.create(name=name,description=description,active=True,freeze=True)
    obj.save()
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})


def imp_binning(bin_set):
  imp='imp_binning'
  mylog.debug({'IMP':imp,'input':bin_set})

  for item in bin_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    bin_obj=Binning.objects.create(name=name,description=description,active=True,freeze=True)
    #bin_obj=Binning.objects.get(name=name)
    grades=item[2]
    for grade in grades:
      bin_grade_obj=BinGrade.objects.get(name=grade)
      Binning_BinGrade.objects.create(binning=bin_obj,bin_grades=bin_grade_obj)

  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_breaking(breaking_set):
  imp='imp_breaking'
  mylog.debug({'IMP':imp,'input':breaking_set})

  for item in breaking_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None

    break_qty=item[2]
    break_qty=int(break_qty)
    new_product=item[3]
    new_product_obj=Product.objects.get(name=new_product)
    obj=Breaking.objects.create(name=name,description=description,break_qty=break_qty,new_product=new_product_obj,active=True,freeze=True)
    obj.save()
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_step_cat(step_cat_set):
  imp='imp_step_cat'
  mylog.debug({'IMP':imp,'input':step_cat_set})

  for item in step_cat_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    obj=StepCategory.objects.create(name=name,description=description,active=True,freeze=True)
    obj.save()
  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_step(step_set):
  imp='imp_step'
  mylog.debug({'IMP':imp,'input':step_set})

  for item in step_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None

    recipe=item[2]
    instruction=item[3]
    if instruction=='':
      instruction=None

    eq_group=item[4]
    eq_group_obj=EqGroup.objects.get(name=eq_group)

    category=item[5]
    cat_obj=StepCategory.objects.get(name=category)

    step_chk=item[6]
    if step_chk=='':
      step_chk_obj=None
    else:
      step_chk_obj=EqRecord.objects.get(name=step_chk)

    dcplan=item[7]
    if dcplan=='':
      dcplan_obj=None
    else:
      dcplan_obj=DcPlan.objects.get(name=dcplan)

    breaking=item[8]
    if breaking=='':
      breaking_obj=None
    else:
      breaking_obj=Breaking.objects.get(name=breaking)

    binning=item[9]
    if binning=='':
      binning_obj=None
    else:
      binning_obj=Binning.objects.get(name=binning)

    ProcessStep.objects.create(name=name,description=description,recipe=recipe,instruction=instruction,eq_group=eq_group_obj,category=cat_obj,step_check=step_chk_obj,dcplan=dcplan_obj,breaking=breaking_obj,binning=binning_obj,active=True,freeze=True)

  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})


def imp_process(process_set):
  imp='imp_process'
  mylog.debug({'IMP':imp,'input':process_set})
  for rec in process_set:
    mylog.debug({'IMP':imp,'rec':rec})
    name=rec[0]
    description=rec[1]
    if description=='':
      description=None
    process_obj=Process.objects.create(name=name,description=description,active=True,freeze=True)
    steps=rec[2]
    for step in steps:
      mylog.debug({'IMP':imp,'step':step})
      step_obj=ProcessStep.objects.get(name=step)
      ProcessProcessStep.objects.create(process=process_obj,process_step=step_obj)

    mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_product(product_set):
  imp='imp_product'
  mylog.debug({'IMP':imp,'input':product_set})

  for item in product_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    unit=item[2]
    process=item[3]
    if process=='':
      process_obj=None
    else:
      process_obj=Process.objects.get(name=process)
    Product.objects.create(name=name,description=description,unit=unit,process=process_obj,active=True,freeze=True)

  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_bonus_scrap(bonus_scrap_set):
  imp='imp_bonus_scrap'
  mylog.debug({'IMP':imp,'input':bonus_scrap_set})

  for item in bonus_scrap_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    bonus_scrap=item[2]
    BonusScrapCode.objects.create(name=name,description=description,bonus_scrap=bonus_scrap,active=True,freeze=True)

  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})

def imp_lot_hold_release(lot_hold_release_set):
  imp='imp_lot_hold_release'
  mylog.debug({'IMP':imp,'input':lot_hold_release_set})

  for item in lot_hold_release_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    hold_release=item[2]
    LotHoldReleaseCode.objects.create(name=name,description=description,hold_release=hold_release,active=True,freeze=True)

  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})


def imp_eq_hold_release(eq_hold_release_set):
  imp='imp_eq_hold_release'
  mylog.debug({'IMP':imp,'input':eq_hold_release_set})

  for item in eq_hold_release_set:
    mylog.debug({'IMP':imp,'item':item})
    name=item[0]
    description=item[1]
    if description=='':
      description=None
    hold_release=item[2]
    EqHoldReleaseCode.objects.create(name=name,description=description,hold_release=hold_release,active=True,freeze=True)

  mylog.debug({'IMP':imp,'ECD':'0','ETX':'Succeed'})


@transaction.atomic
def main():
  v_name='auto_modeling'
  sid=transaction.savepoint()
  try:
    imp_dcitem_cat(DcItemCategorySet)
    imp_dcitem(DcItemSet)
    imp_dcitem_spec(DcItemSpecSet)
    imp_dcplan(DcPlanSet)
    imp_area(AreaSet)
    imp_eq_group(EqGroupSet)
    imp_eq(EqSet)
    imp_lot_record(LotRecordSet)
    imp_eq_record(EqRecordSet)
    imp_bin_grade(BinGradeSet)
    imp_binning(BinningSet)

    #breaking's new product > product > process > step > category
    imp_step_cat(StepCategorySet)
    imp_step(ProcessStepBinSet)
    imp_process(ProcessLEDChipSet)
    imp_product(ProductBreakSet)
    imp_breaking(BreakingSet)
    imp_step(ProcessStepSet)
    imp_process(ProcessSet)
    imp_product(ProductSet)

    imp_bonus_scrap(BonusScrapCodeSet)
    imp_lot_hold_release(LotHoldReleaseCodeSet)
    imp_eq_hold_release(EqHoldReleaseCodeSet)

    # for stress test (share dcitem category, dcitem, area, bonus_scrap, lot_hold_release, eq_hold_release)
    imp_dcplan(ST_DcPlanSet)
    imp_eq_group(ST_EqGroupSet)
    imp_eq(ST_EqSet)
    imp_lot_record(ST_LotRecordSet)
    imp_eq_record(ST_EqRecordSet)
    imp_bin_grade(ST_BinGradeSet)
    imp_binning(ST_BinningSet)

    imp_step_cat(ST_StepCategorySet)
    imp_step(ST_ProcessStepBinSet)
    imp_process(ST_ProcessLEDChipSet)
    imp_product(ST_ProductBreakSet)
    imp_breaking(ST_BreakingSet)
    imp_step(ST_ProcessStepSet)
    imp_process(ST_ProcessSet)
    imp_product(ST_ProductSet)

    transaction.savepoint_commit(sid)
    mylog.info({'Function':v_name,'Auto Modeling':'Success'})
  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
  pass

if __name__=='__main__':
  main()
