from runMES import models
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import operator
import logging
from MQTT import log_runMES
import traceback
import uuid
from django.core.exceptions import ObjectDoesNotExist
from validators import slug,email
import shortuuid
from django.utils.translation import gettext as _


mylog=logging.getLogger('runMES')

def qry_lot_info(lot_txt,op_txt):
  tns='qry_lot_info'
  try:
    lot_set=models.Lot.objects.filter(name=lot_txt)
    if not lot_set:
      log_runMES.to_warning({'TNS':tns,'ECD':'L11','ETX':'Lot Not Exist','LOT':lot_txt,'OP':op_txt})
      return {'TNS':tns,'ECD':'L11','ETX':_('Lot Not Exist'),'LOT':lot_txt,'OP':op_txt}
    else:
      lot_obj=models.Lot.objects.get(name=lot_txt)
      if lot_obj.curr_eq:
        curr_eq=lot_obj.curr_eq.name
      else:
        curr_eq=''
      recipe=lot_obj.step_recipe
      work_order=lot_obj.workorder
      if lot_obj.product:
        product=lot_obj.product.name
      else:
        product=''
      if lot_obj.process:
        process=lot_obj.process.name
        if lot_obj.process_step:
          step=lot_obj.process_step.name
          if lot_obj.step_dcplan:
            dcplan=lot_obj.process_step.dcplan.name
          else:
            dcplan=''
          if lot_obj.process_step.breaking:
            breaking=lot_obj.process_step.breaking.name
          else:
            breaking=''
          if lot_obj.process_step.binning:
            binning=lot_obj.process_step.binning.name
          else:
            binning=''
        else:
          step=''
          dcplan=''
          breaking=''
          binning=''

      else:
        process=''
        step=''
        dcplan=''
        breaking=''
        binning=''

      state=lot_obj.ctrl_state
      hold=lot_obj.is_hold
      qty=lot_obj.qty
      grade=lot_obj.lot_grade
      lot_type=lot_obj.lot_type
      next_op=lot_obj.next_operation
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),"LOT":lot_txt,'OP':op_txt,'EQ':curr_eq,'RECIPE':recipe,'WORK_ORDER':work_order,'PRODUCT':product,'PROCESS':process,'STEP':step,'DC_PLAN':dcplan,'BREAKING':breaking,'BINNING':binning,'STATE':state,'HOLD':hold,'QTY':qty,'GRADE':grade,'TYPE':lot_type,'NEXT_OP':next_op}

  except Exception as e:
    mylog.exception(e)
    return {'TNS':tns,'ERR':e,'LOT':lot_txt,'OP':op_txt}

def qry_lot_record(step_txt,op_txt):
  tns='qry_lot_record'
  try:
    step_set=models.LotRecord.objects.filter(name=step_txt,active=True,freeze=True)
    if step_set:
      step_obj=models.LotRecord.objects.get(name=step_txt,active=True,freeze=True)
      dcplan=step_obj.dcplan.name
      log_runMES.to_debug({'TNS':tns,'ECD':'0','ETX':_('Succeed'),'DC_PLAN':dcplan,'STEP':step_txt,'OP':op_txt})
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'DC_PLAN':dcplan,'STEP':step_txt,'OP':op_txt}
    else:
      return {'TNS':tns,'ECD':'O01','ETX':_('Step Not Exist'),'STEP':step_txt,'OP':op_txt}
  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'STEP':step_txt,'OP':op_txt})
    return {'TNS':tns,'ERR':e,'STEP':step_txt,'OP':op_txt}

def qry_eq_record(eq_txt,op_txt):
  tns='qry_eq_record'
  try:
    eq_set=models.Eq.objects.filter(name=eq_txt,active=True,freeze=True)
    if eq_set:
      eq_rec_set=models.EqRecord.objects.filter(eq_group=eq_set[0].group,active=True,freeze=True)
      if eq_rec_set:
        reply_eq_rec_set={}
        for e in eq_rec_set:
          dcplan=e.dcplan.name
          eq_rec=e.name
          eq_rec_dcplan={eq_rec:dcplan}
          reply_eq_rec_set.update(eq_rec_dcplan)

        log_runMES.to_debug({'TNS':tns,'ECD':'0','ETX':_('Succeed'),'EQ_RECORD_PLANS':reply_eq_rec_set,'EQ':eq_txt,'OP':op_txt})
        return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'EQ':eq_txt,'EQ_RECORD_PLANS':reply_eq_rec_set,'OP':op_txt}
      else:
        log_runMES.to_debug({'TNS':tns,'ECD':'O01','ETX':_('EQ Record Not Exist'),'EQ':eq_txt,'OP':op_txt})
        return {'TNS':tns,'ECD':'O01','ETX':_('EQ Record Not Exist'),'EQ':eq_txt,'OP':op_txt}
    else:
      log_runMES.to_debug({'TNS':tns,'ECD':'O01','ETX':'EQ Not Exist','EQ':eq_txt,'OP':op_txt})
      return {'TNS':tns,'ECD':'O01','ETX':_('EQ Not Exist'),'EQ':eq_txt,'OP':op_txt}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'EQ':eq_txt,'OP':op_txt})
    return {'TNS':tns,'ERR':e,'EQ':eq_txt,'OP':op_txt}

def qry_lot_bin(lot_txt,eq_txt,op_txt):
  tns='qry_lot_bin'
  try:
    lot_set=models.Lot.objects.filter(name=lot_txt)
    if not lot_set:
      return {'TNS':tns,'ECD':'O01','ETX':_('Lot Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    eq_set=models.Eq.objects.filter(name=eq_txt)
    if not eq_set:
      return {'TNS':tns,'ECD':'O01','ETX':_('EQ Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    lot_obj=models.Lot.objects.get(name=lot_txt)
    if not lot_obj.curr_eq or lot_obj.curr_eq.name!=eq_txt:
      return {'TNS':tns,'ECD':'E02','ETX':_('EQ Not Match Lot'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    lot_qty=lot_obj.qty
    binning=lot_obj.step_binning
    if binning=='':
      mylog.error({"TNS":tns,'ECD':'O01','ETX':_('Lot No Binning'),'LOT':lot_txt,'OP':op_txt})
      return {"TNS":tns,'ECD':'O01','ETX':_('Lot No Binning'),'LOT':lot_txt,'OP':op_txt}
    bin_obj=models.Binning.objects.get(name=binning)
    bin_set=models.Binning_BinGrade.objects.filter(binning=bin_obj)
    grade_set=[]
    for b in bin_set:
      dic={}
      dic['grade']=b.bin_grades.name
      dic['description']=b.bin_grades.description
      grade_set.append(dic)

    log_runMES.to_debug({"TNS":tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'OP':op_txt,'GRADE_SET':grade_set,'LOT_QTY':lot_qty})
    return {"TNS":tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'OP':op_txt,'GRADE_SET':grade_set,'BINNING':binning,'LOT_QTY':lot_qty}
  except Exception as e:
    mylog.exception(e)
    mylog.error({"TNS":tns,'ERR':e,'LOT':lot_txt,'OP':op_txt})
    return {"TNS":tns,'ERR':e,'LOT':lot_txt,'OP':op_txt}

def tx_update_lot_next_op(lot,next_op):
  tns='tx_update_lot_next_op'
  try:
    lot_obj=models.Lot.objects.get(name=lot)
    lot_obj.next_operation=next_op
    lot_obj.save()
    log_runMES.to_debug({'TNS':tns,'ECD':'0','ETX':_('Succeed'),'lot':lot,'next':next_op})
    return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'lot':lot,'next':next_op}
  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'lot':lot,'next':next_op})
    return {'TNS':tns,'ERR':e,'lot':lot,'next':next_op}

#operation_choices=(('SC','StepCheck'),('SI','StepIn'),('SO','StepOut'),('DC','DC'),('BK','Breaking'),('BI','Binning'),('NP','New Product'),('NO','None'))
def qry_next_op(lot_txt):
  tns='qry_next_op'
  try:
    lot_obj=models.Lot.objects.get(name=lot_txt)
    curr_op=lot_obj.next_operation
    if curr_op=='SI':
      if lot_obj.process_step.dcplan:
        next_op='DC'
      elif lot_obj.process_step.breaking:
        next_op='BK'
      elif lot_obj.process_step.binning:
        next_op='BI'
      else:
        next_op='SO'
    elif curr_op=='DC':
      if lot_obj.process_step.breaking:
        next_op='BK'
      elif lot_obj.process_step.binning:
        next_op='BI'
      else:
        next_op='SO'
    elif curr_op=='BK':
      if lot_obj.process_step.binning:
        next_op='BI'
      else:
        next_op='SO'
    elif curr_op=='BI':
      next_op='SO'
    elif curr_op=='SO':
      # if process step is last one
      pp_obj=models.ProcessProcessStep.objects.filter(process=lot_obj.process)
      curr_pp_obj=models.ProcessProcessStep.objects.get(process=lot_obj.process,process_step=lot_obj.process_step)
      if curr_pp_obj==pp_obj.last():
        next_op='NO'
      else:
        next_op='SI'
    else:
      mylog.error({'TNS':tns,'ECD':'U01','ETX':_('next OP not exist'),'LOT':lot_txt})
      return {'TNS':tns,'ECD':'U01','ETX':_('next OP not exist'),'LOT':lot_txt}

    return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'NEXT_OP':next_op,'LOT':lot_txt}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':'e','LOT':lot_txt})
    return {'TNS':tns,'ERR':'e','LOT':lot_txt}

def qry_dcplan_item(dcplan_name_txt,op_txt):
  tns='qry_dcplan_item'
  try:
    dcplan_obj=models.DcPlan.objects.get(name=dcplan_name_txt)
    plan_items=models.DcPlanDcItem.objects.filter(dcplan=dcplan_obj)
    #log_runMES.to_debug({'tns':tns,'DC_PLAN':dcplan_name_txt,'plan_items':plan_items,'DCITEM_COUNT':len(plan_items)})
    item_set=[]
    for item in plan_items:
      dic={}
      dic['item_name']=item.dcitems.name
      dic['category']=item.dcitems.dcitem_category.name
      dic['unit']=item.dcitems.dcitem_category.unit
      dic['data_type']=item.dcitems.dcitem_category.data_type
      item_set.append(dic)
    item_set.sort(key=operator.itemgetter('item_name'))
    log_runMES.to_debug({'TNS':tns,'DC_PLAN':dcplan_name_txt,'DCITEM_SET':item_set,'DCITEM_COUNT':len(item_set),'OP':op_txt})
    return {'TNS':tns,"ECD":'0','ETX':'Succeed','DC_PLAN':dcplan_name_txt,'DCITEM_SET':item_set,'DCITEM_COUNT':len(item_set),'OP':op_txt}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'DC_PLAN':dcplan_name_txt,'OP':op_txt})
    return {'TNS':tns,'ERR':e,'DC_PLAN':dcplan_name_txt,'OP':op_txt}

@transaction.atomic
def tx_add_new_lot(lot_txt,work_order_obj,product_txt,process_step_obj,process_obj,qty_int,lot_type_txt,anno_txt):
  tns='tx_add_new_lot'
  curr_location='F'
  operation=''
  log_runMES.to_debug({'TNS':tns,'lot_txt':lot_txt,'product_txt':product_txt,'process_step':process_step_obj.name,'process':process_obj.name,'qty_int':qty_int,'anno_txt':anno_txt})
  try:
    product_obj=models.Product.objects.get(name=product_txt)
    if process_step_obj.step_check:
      step_check=process_step_obj.step_check.name
    else:
      step_check=None
    if process_step_obj.dcplan:
      step_dcplan=process_step_obj.dcplan.name
    else:
      step_dcplan=None
    if process_step_obj.binning:
      step_binning=process_step_obj.binning.name
    else:
      step_binning=None
    if process_step_obj.breaking:
      step_breaking=process_step_obj.breaking.name
    else:
      step_breaking=None

    #o#operation_choices=(('SC','StepCheck'),('SI','StepIn'),('SO','StepOut'),('DC','DC'),('BK','Breaking'),('BI','Binning'),('NP','New Product'),('NO','None'))
    operation='SI'
    # if step_check:
    #   operation='SC'

    lot_obj=models.Lot.objects.create(
      name=lot_txt,
      product=product_obj,
      step_recipe=process_step_obj.recipe,
      process_step=process_step_obj,
      process=process_obj,
      step_check=step_check,
      step_dcplan=step_dcplan,
      step_binning=step_binning,
      step_breaking=step_breaking,
      workorder=work_order_obj.name,
      qty=qty_int,
      lot_priority=work_order_obj.lot_priority,
      curr_location=curr_location,
      owner=work_order_obj.owner,
      target_time=work_order_obj.target_date,
      lot_type=lot_type_txt,
      next_operation=operation,
    )
    lot_obj.save()
    log_runMES.to_debug({'TNS':tns,'lot_obj':lot_obj})
    return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'lot_txt':lot_txt,'product_txt':product_txt,'process_step':process_step_obj.name,'process':process_obj.name,'qty_int':qty_int,'workorder_obj':work_order_obj,'anno_txt':anno_txt}

  except Exception as e:
    mylog.exception(e)
    return {'TNS':tns,'ERR':e,'lot_txt':lot_txt,'product_txt':product_txt,'process_step_obj':process_step_obj,'process_obj':process_obj,'qty_int':qty_int,'workorder_obj':work_order_obj,'anno_txt':anno_txt}

@transaction.atomic()
def tx_lot_terminate(lot_txt,transaction_txt,op_txt,anno_txt):
  tns='tx_lot_terminate'
  tid=str(shortuuid.uuid())
  try:
    lot_obj=models.Lot.objects.get(name=lot_txt)
    if lot_obj.qty is not 0:
      return {'TNS':tns,'ECD':'L14','ETX':_('Lot Qty Error'),'QTY':str(lot_obj.qty),'LOT':lot_txt}
    hist_obj=models.LotTerminateHist.objects.create(
      lot=lot_txt,
      work_order=lot_obj.workorder,
      product=lot_obj.product.name,
      process=lot_obj.process.name,
      process_step=lot_obj.process_step.name,
      transaction=transaction_txt,
      op=op_txt,
      run_id=lot_obj.run_id,
      tid=tid,
      annotation=anno_txt,
    )
    hist_obj.save()
    lot_obj.ctrl_state='T'
    lot_obj.next_operation="NO"
    lot_obj.step_recipe=None
    lot_obj.step_dcplan=None
    lot_obj.step_breaking=None
    lot_obj.step_binning=None
    lot_obj.curr_eq=None
    lot_obj.curr_location='F'
    lot_obj.process=None
    lot_obj.process_step=None
    lot_obj.save()

    # def tx_log_lot_step_hist(tid_txt,lot_txt,eq_txt,op_txt,anno_txt):
    tid=str(shortuuid.uuid())
    eq_txt=''
    reply=tx_log_lot_step_hist(tns,tid,lot_txt,eq_txt,op_txt,anno_txt)
    if reply['ECD']!=0:
      msg={'TNS':tns,'ECD':reply['ECD'],'ETX':reply['ETX'],'LOT':lot_txt,'TRANSACTION':transaction_txt}
      mylog.error(msg)
      return msg
    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'TRANSACTION':transaction_txt}
    log_runMES.to_info(msg)
    return msg

  except Exception as e:
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'LOT':lot_txt,'TRANSACTION':transaction_txt}
    mylog.error(msg)
    return msg

# rules for lot naming xxxx.xx .xx incremental
def tx_generate_child_lot(lot_txt):
  tns='tx_generate_child_lot'
  try:
    lot_pre=lot_txt+'.'
    lot_list=models.Lot.objects.filter(name__startswith=lot_pre)
    log_runMES.to_debug({'TNS':tns,'lot_list':lot_list})
    new_ext=[]
    if lot_list:
      for l in lot_list:
        pre,after=l.name.split(lot_txt+'.')
        if '.' in after:
          pass
        else:
          new_ext.append(int(after))
      new_ext.sort(reverse=True)
      log_runMES.to_debug({'TNS':tns,'new_ext':new_ext})
      new_lot=lot_txt+'.'+str(new_ext[0]+1)
    else:
      new_lot=lot_txt+'.1'
    if models.Lot.objects.filter(name=new_ext):
      return {'TNS':tns,'ECD':'L17','ETX':_('New Lot Duplication'),'LOT':lot_txt,'NEW_LOT':new_lot}
    return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'NEW_LOT':new_lot}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'LOT':lot_txt})
    return {'TNS':tns,'ERR':e,'LOT':lot_txt}

@transaction.atomic
def tx_split_lot(parent_lot_txt,op_txt,child_qty_int,anno_txt):
  tns='tx_split_lot'
  tid=str(shortuuid.uuid())
  sid=transaction.savepoint()
  try:
    if len(parent_lot_txt)>=30:
      msg={'TNS':tns,"ECD":'L15','ETX':_('Lot ID Exceed Max Length, Please Merge to a shorter Lot ID'),'PARENT LOT':parent_lot_txt,'OP':op_txt}
      mylog.error(msg)
      return msg
    lot_obj=models.Lot.objects.get(name=parent_lot_txt)
    if lot_obj.ctrl_state=='S':
      msg={'TNS':tns,"ECD":'L01','ETX':_('Lot State Mismatch'),'PARENT LOT':parent_lot_txt,'QTY':lot_obj.qty,'OP':op_txt}
      mylog.error(msg)
      return msg

    if lot_obj.is_hold is True:
      msg={'TNS':tns,"ECD":'L03','ETX':_('Lot In Hold'),'PARENT LOT':parent_lot_txt,'QTY':lot_obj.qty,'OP':op_txt}
      mylog.error(msg)
      return msg

    # tx_generate_child_lot(lot_txt)
    reply=tx_generate_child_lot(parent_lot_txt)
    child_lot=reply['NEW_LOT']
    if lot_obj.qty<child_qty_int:
      msg={'TNS':tns,"ECD":'L05','ETX':_('Lot Qty Error'),'PARENT LOT':parent_lot_txt,'QTY':lot_obj.qty,'OP':op_txt}
      mylog.error(msg)
      return msg

    child_lot_obj=models.Lot.objects.create(
      name=child_lot,
      product=lot_obj.product,
      ctrl_state=lot_obj.ctrl_state,
      is_active=lot_obj.is_active,
      is_hold=lot_obj.is_hold,
      hold_reason=lot_obj.hold_reason,
      is_finish=lot_obj.is_finish,
      step_recipe=lot_obj.step_recipe,
      step_check=lot_obj.step_check,
      step_dcplan=lot_obj.step_dcplan,
      step_binning=lot_obj.step_binning,
      workorder=lot_obj.workorder,
      qty=child_qty_int,
      next_operation=lot_obj.next_operation,
      process=lot_obj.process,
      process_step=lot_obj.process_step,
      curr_location=lot_obj.curr_location,
      curr_area=lot_obj.curr_area,
      curr_eq=lot_obj.curr_eq,
      start_time=lot_obj.start_time,
      target_time=lot_obj.target_time,
      lot_priority=lot_obj.lot_priority,
      run_id=lot_obj.run_id,
      owner=lot_obj.owner,
      component_map_uuid=lot_obj.component_map_uuid,
      lot_type=lot_obj.lot_type,
      lot_grade=lot_obj.lot_grade,
      last_step_uuid=lot_obj.last_step_uuid,
      last_step_time=lot_obj.last_step_uuid,
      owner_mail=lot_obj.owner_mail,
    )
    child_lot_obj.save()

    parent_qty=lot_obj.qty
    lot_obj.qty=parent_qty-child_qty_int
    lot_obj.save()
    if lot_obj.qty==0:
      # terminate lot
      # def tx_lot_terminate(lot_txt,transaction_txt,op_txt,anno_txt):
      reply=tx_lot_terminate(parent_lot_txt,tns,op_txt,anno_txt)
      if reply['ECD']!='0':
        msg={'TNS':tns,"ECD":reply['ECD'],'ETX':reply['ETX'],'PARENT LOT':parent_lot_txt,'QTY':parent_qty,'OP':op_txt}
        mylog.error(msg)
        return msg

    #split_merge_choices=(('S','Split'),('M','Merge'))
    choice='S'
    hist_obj=models.LotSplitMergeHist.objects.create(
      parent_lot=parent_lot_txt,
      parent_qty=parent_qty,
      child_lot=child_lot,
      child_qty=child_qty_int,
      split_merge=choice,
      parent_step_uuid=child_lot_obj.run_id,
      child_step_uuid=child_lot_obj.run_id,
      transaction=tns,
      tid=tid,
      annotation=anno_txt
    )
    hist_obj.save()
    # def tx_log_lot_step_hist(tid_txt,lot_txt,eq_txt,op_txt,anno_txt):

    reply=tx_log_lot_step_hist(tns,tid,child_lot,'',op_txt,anno_txt)
    if reply['ECD']!='0':
      transaction.savepoint_rollback(sid)
      msg={'TNS':tns,"ECD":reply['ECD'],'ETX':reply['ETX'],'PARENT LOT':parent_lot_txt,'OP':op_txt}
      mylog.error(msg)
      return msg

    msg={'TNS':tns,"ECD":'0','ETX':_('Succeed'),'PARENT LOT':parent_lot_txt,'PARENT QTY':lot_obj.qty,'NEW LOT':child_lot,'NEW LOT QTY':child_lot_obj.qty,'OP':op_txt}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'PARENT LOT':parent_lot_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_merge_lot(parent_lot_txt,child_lot_txt,op_txt,anno_txt):
  tns='tx_merge_lot'
  tid=str(shortuuid.uuid())
  sid=transaction.savepoint()
  try:
    ecd='0'
    etx=''
    if models.Lot.objects.filter(name=parent_lot_txt) and models.Lot.objects.filter(name=child_lot_txt):
      parent_obj=models.Lot.objects.get(name=parent_lot_txt)
      child_obj=models.Lot.objects.get(name=child_lot_txt)
      if parent_obj.product!=child_obj.product:
        ecd,etx='L06',_('Product Mismatch')
      elif parent_obj.ctrl_state=='S' or child_obj.ctrl_state=='S':
        ecd,etx='L01',_('Lot State Mismatch')
      elif parent_obj.process_step!=child_obj.process_step:
        ecd,etx='L07',_('Process Step Mismatch')
      elif parent_obj.next_operation!=child_obj.next_operation:
        ecd,etx='L08',_('Next Operation Mismatch')
      elif parent_obj.is_hold or child_obj.is_hold:
        ecd,etx='L03',_('Lot In Hold')
      elif parent_obj.lot_grade!=child_obj.lot_grade:
        ecd,etx='L10',_('Lot Grade Mismatch')
    else:
      ecd,etx='L12',_('Lot Not Exist')

    if ecd is not '0':
      mylog.error({'TNS':tns,'ECD':ecd,'ETX':etx,'PARENT LOT':parent_lot_txt,'CHILD LOT':child_lot_txt})
      return {'TNS':tns,'ECD':ecd,'ETX':etx,'PARENT LOT':parent_lot_txt,'CHILD LOT':child_lot_txt}
    else:
      parent_qty=parent_obj.qty
      child_qty=child_obj.qty
      parent_uuid=parent_obj.run_id
      child_uuid=child_obj.run_id
      parent_obj.qty=parent_qty+child_qty
      child_obj.qty=0
      child_obj.is_active=False
      child_obj.curr_eq=None
      #ctrl_state_choices=(('R','Run'),('I','Idle'),('F','Finish'),('S','Ship'),('T','Terminate'),('B','Bank'))
      child_obj.ctrl_state='T'
      parent_obj.save()
      child_obj.save()

      # terminate lot
      # def tx_lot_terminate(lot_txt,transaction_txt,op_txt,anno_txt):
      reply=tx_lot_terminate(child_lot_txt,tns,op_txt,anno_txt)
      if reply['ECD']!='0':
        transaction.savepoint_rollback(sid)
        mylog.error({'TNS':tns,"ECD":reply['ECD'],'ETX':reply['ETX'],'CHILD LOT':child_lot_txt,'OP':op_txt})
        return {'TNS':tns,"ECD":reply['ECD'],'ETX':reply['ETX'],'CHILD LOT':child_lot_txt,'OP':op_txt}

      #split_merge_choices=(('S','Split'),('M','Merge'))
      choice='M'
      hist_obj=models.LotSplitMergeHist.objects.create(
        parent_lot=parent_obj.name,
        parent_qty=parent_qty,
        child_lot=child_obj.name,
        child_qty=child_qty,
        split_merge=choice,
        parent_step_uuid=parent_uuid,
        child_step_uuid=child_uuid,
        transaction=tns,
        tid=tid,
        annotation=anno_txt
      )
      hist_obj.save()

      msg={'TNS':tns,"ECD":'0','ETX':_('Succeed'),'PARENT LOT':parent_lot_txt,'PARENT QTY':parent_qty,'CHILD LOT':child_lot_txt,'CHILD QTY':child_qty,
           'OP':op_txt}
      log_runMES.to_info(msg)
      transaction.savepoint_commit(sid)
      return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'PARENT LOT':parent_lot_txt,'CHILD LOT':child_lot_txt}
    mylog.error(msg)
    return msg

def tx_log_lot_step_hist(tns_txt,tid_txt,lot_txt,eq_txt,op_txt,anno_txt):
  tns="tx_log_lot_step_hist"
  log_runMES.to_info({'tns':tns,'tid':tid_txt,'lot':lot_txt,'eqt':eq_txt,'op':op_txt,'annotation':anno_txt})
  try:
    #trans_time=str(timezone.now())
    obj=models.Lot.objects.get(name=lot_txt)
    if obj.run_id:
      run_id=obj.run_id
    else:
      run_id=None
    if obj.process_step:
      process_step=obj.process_step.name
    else:
      process_step=''
    recipe=obj.step_recipe
    if obj.process:
      process=obj.process.name
    else:
      process=''
    if obj.product:
      product=obj.product.name
    else:
      product=''
    log_runMES.to_debug({'tns':tns,'tid':tid_txt,'lot':lot_txt,'eqt':eq_txt,'op':op_txt,'recipe':recipe,'process':process,"process_step":process_step,'product':product,'run_id':str(run_id),'annotation':anno_txt})

    l=models.LotStepHist(transaction=tns_txt,tid=tid_txt,lot=lot_txt,eq=eq_txt,op=op_txt,qty=str(obj.qty),recipe=recipe,product=product,process=process,process_step=process_step,run_id=run_id,annotation=anno_txt)
    l.save()
    # data={'tns':tns_txt,'tid':tid_txt,'lot':lot_txt,'eq':eq_txt,'op':op_txt,'qty':str(obj.qty),'recipe':recipe,'process':process,"process_step":process_step,'product':product,'trans_time':trans_time,'run_id':str(run_id),'annotation':anno_txt}
    # json_msg=json.dumps(data,ensure_ascii=False)
    # # log_runMES.to_debug({'tns_txt':tns_txt,'json':json_msg})
    # tracking_json.debug(json_msg)
    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'lot_txt':lot_txt,'eq_txt':eq_txt,'op_txt':op_txt,'annotation':anno_txt}
    log_runMES.to_info(msg)
    return msg

  except Exception as e:
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'lot_txt':lot_txt,'eq_txt':eq_txt,'op_txt':op_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_write_dcvalue_hist(dcplan_hist_obj,dcitem_txt,category_txt,datatype_txt,unit_txt,value_txt,tid_txt):
  tns='tx_write_dcvalue_hist'
  try:
    #log_runMES.to_debug({'TNS':'tx_write_dcvalue_hist','dcplan_hist_obj':dcplan_hist_obj,'dcitem':dcitem,'category':category_txt,'datatype':datatype_txt,'unit':unit_txt,'value':value_txt})
    trans_time=str(timezone.now())
    dcval_obj=models.DcValueHist(dcplan_hist=dcplan_hist_obj,dcitem=dcitem_txt,category=category_txt,datatype=datatype_txt,unit=unit_txt,value=value_txt,tid=tid_txt)
    dcval_obj.save()
    # data={'TNS':'write_dcvalue_hist','dcplan_hist_id':dcplan_hist_obj.pk,'dcitem':dcitem_txt,'category':category_txt,'datatype':datatype_txt,'unit':unit_txt,'value':value_txt,'tid':tid_txt,'trans_time':trans_time}
    # json_msg=json.dumps(data,ensure_ascii=False)
    # dcitem_json.debug(json_msg)
    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'dcplan_hist_id':str(dcplan_hist_obj),'dcitem':dcitem_txt,'unit':unit_txt,'value':value_txt}
    log_runMES.to_info(msg)
    return msg
  except Exception as e:
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'dcplan_hist_id':str(dcplan_hist_obj),'dcitem':dcitem_txt,'unit':unit_txt,'value':value_txt}
    mylog.error(msg)
    return msg

def qry_lot_query_eq(lot_txt):
  tns='qry_lot_query_eq'
  try:
    lot_set=models.Lot.objects.filter(name=lot_txt)
    if not lot_set:
      return {'TNS':tns,'ECD':'L02','ETX':_('Lot Not Exist'),'LOT':lot_txt}
    lot_obj=models.Lot.objects.get(name=lot_txt)
    if lot_obj.is_hold:
      return {'TNS':tns,"ECD":'L03','ETX':_('Lot In Hold'),'LOT':lot_txt}

    if lot_obj.process_step and lot_obj.process_step.eq_group:
      #log_runMES.to_debug({'TNS':tns,'EQ GROUP':lot_obj.process_step.eq_group.name})
      eq_list=models.Eq.objects.filter(group=lot_obj.process_step.eq_group,is_hold=False,active=True,freeze=True)
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'EQ_LIST':eq_list,'LOT':lot_txt}
    else:
      return {'TNS':tns,'ECD':'L11','ETX':_('No EQ Available'),'LOT':lot_txt}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'LOT':lot_txt})
    return {'TNS':tns,'ERR':e,'LOT':lot_txt}

def qry_eq_query_lot(eq_txt,op_txt):
  tns='qry_eq_query_lot'
  try:
    eq_set=models.Eq.objects.filter(name=eq_txt)
    if not eq_set:
      return {'TNS':tns,'ECD':'E05','ETX':_('EQ Not Exist'),'EQ':eq_txt,'OP':op_txt}
    eq_obj=models.Eq.objects.get(name=eq_txt)
    if eq_obj.is_hold:
      return {'TNS':tns,"ECD":'E03','ETX':_('EQ in Hold'),'EQ':eq_txt,'OP':op_txt}

    step_set=models.ProcessStep.objects.filter(eq_group=eq_obj.group)
    lot_list=[]
    for step in step_set:
      #log_runMES.to_debug({'TNS':tns,"STEP":step})
      lot_set=models.Lot.objects.filter(process_step=step,next_operation='SI').order_by('lot_priority')
      #log_runMES.to_debug({'TNS':tns,"LOT SET":lot_set})
      for l in lot_set:
        lot_list.append(l.name)

    if lot_list:
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT_LIST':lot_list,'EQ':eq_txt,'OP':op_txt}
    else:
      return {'TNS':tns,'ECD':'E06','ETX':_('No Lot Available'),'LOT':eq_txt,'OP':op_txt}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'EQ':eq_txt,'OP':op_txt})
    return {'TNS':tns,'ERR':e,'EQ':eq_txt,'OP':op_txt}

def qry_eq_product_query_lot(eq_txt,product_txt,op_txt):
  tns='qry_eq_product_query_lot'
  try:
    eq_set=models.Eq.objects.filter(name=eq_txt)
    if not eq_set:
      return {'TNS':tns,'ECD':'E05','ETX':_('EQ Not Exist'),'EQ':eq_txt,'PRODUCT':product_txt,'OP':op_txt}
    eq_obj=models.Eq.objects.get(name=eq_txt)
    if eq_obj.is_hold:
      return {'TNS':tns,"ECD":'E03','ETX':_('EQ in Hold'),'EQ':eq_txt,'PRODUCT':product_txt,'OP':op_txt}

    if not models.Product.objects.filter(name=product_txt):
      return {'TNS':tns,'ECD':'P01','ETX':_('Product Not Exist'),'EQ':eq_txt,'PRODUCT':product_txt,'OP':op_txt}
    product_obj=models.Product.objects.get(name=product_txt)
    step_set=models.ProcessStep.objects.filter(eq_group=eq_obj.group)
    lot_list=[]
    for step in step_set:
      lot_set=models.Lot.objects.filter(process_step=step,next_operation='SI',ctrl_state='I',product=product_obj).order_by('name')
      for l in lot_set:
        lot_list.append(l.name)

    if lot_list:
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT_LIST':lot_list,'EQ':eq_txt,'PRODUCT':product_txt,'OP':op_txt}
    else:
      return {'TNS':tns,'ECD':'E07','ETX':_('No Lot Available for EQ'),'EQ':eq_txt,'PRODUCT':product_txt,'OP':op_txt}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'EQ':eq_txt,'PRODUCT':product_txt,'OP':op_txt})
    return {'TNS':tns,'ERR':e,'EQ':eq_txt,'PRODUCT':product_txt,'OP':op_txt}

def query_lot_hist(lot):
  tns='query_lot_hist'
  try:
    reply=models.LotStepHist.objects.filter(lot=lot).values().order_by('trans_time')
    log_runMES.to_debug({'TNS':tns,'HIST_LIST':reply,'LOT':lot})
    if reply:
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'HIST_LIST':reply,'LOT':lot}
    else:
      reply=None
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'HIS_LIST':reply,'LOT':lot}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'lot':lot})
    return {'TNS':tns,'ERR':e,'LOT':lot}

# filter is used for search criteria, can not use for link field
# prepare data set for data table
def tx_query_tbl_by_fields_w_filter(table_obj,set_fields,txt_filter_field,any_filter_val):
  tns='tx_query_tbl_by_fields_w_filter'
  try:
    log_runMES.to_debug({'TNS':'query_tbl_by_fields','table_obj':table_obj,'txt_filter_field':txt_filter_field,'set_fields':set_fields})
    if (txt_filter_field and any_filter_val) is not None:
      criteria={txt_filter_field:any_filter_val}
      data_obj=table_obj.objects.filter(**criteria).values()
      is_filter=True
    else:
      data_obj=table_obj.objects.all()
      is_filter=False
    # data_obj = tbl_obj.objects.filter(**criteria)
    # log_runMES.to_debug({'TNS':'query_tbl_by_fields','data_obj':data_obj})
    data_set=[]
    for obj in data_obj:
      sub_set=[]
      for f in set_fields:
        # log_runMES.to_debug({'TNS':'query_tbl_by_fields','f in fields':f})
        if is_filter:
          data=obj.get(f)
          sub_set.append(data)
        else:
          data=getattr(obj,f)
          sub_set.append(data)

      data_set.append(sub_set)
    log_runMES.to_debug({'TNS':tns,'data_set':data_set})
    return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'DATA_SET':data_set,'table_obj':table_obj,'txt_filter_field':txt_filter_field}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'table_obj':table_obj,'txt_filter_field':txt_filter_field,'set_fields':set_fields})
    return {'TNS':tns,'ERR':e,'txt_filter_field':txt_filter_field}

def tx_workorder_find_lotstart(workorder_txt):
  tns='tx_workorder_find_lotstart'
  try:
    reply=models.LotStartHist.objects.filter(work_order=workorder_txt)
    # log_runMES.to_debug({'lots':reply.values()})
    log_runMES.to_debug({'TNS':tns,'workorder':workorder_txt,'lot_list':reply.values()})
    return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'workorder_txt':workorder_txt,
            'lot_list':reply.values()}
  except Exception as e:
    mylog.exception(e)
    return {'TNS':tns,'ERR':e,'workorder':workorder_txt}

def tx_process_find_step(pk):
  tns='tx_process_find_step'
  try:
    processObj=models.Process.objects.get(id=pk)
    step_list=models.ProcessProcessStep.objects.filter(process=processObj)

    if step_list:
      step_txt=step_list[0].process_step.name
      recipe_txt=step_list[0].process_step.recipe
      dcplan_obj=step_list[0].process_step.dcplan
      if dcplan_obj:
        dcplan_txt=dcplan_obj.name
      else:
        dcplan_txt=None

      step_pack=[]
      step_pack.append([step_txt,recipe_txt,dcplan_txt])

      log_runMES.to_debug({'TNS':tns,'ECD':'0','ETX':_('Succeed'),'step_pack':step_pack,'process':pk})
      return {'TNS':'tx_process_find_step','ECD':'0','ETX':_('Succeed'),'step_pack':step_pack,'process':pk}
    else:
      log_runMES.to_debug({'TNS':tns,'process':pk})
      return {'TNS':tns,'ECD':'S01','ETX':_('Process Step Not Exist'),'process':pk}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'process':pk})
    return {'TNS':tns,'ERR':e,'process':pk}

def tx_query_workorder(workorder_txt):
  tns='tx_query_workorder'
  log_runMES.to_debug({'TNS':tns,'order':workorder_txt})
  try:
    obj=models.WorkOrder.objects.filter(name=workorder_txt,active=True,freeze=True)
    if obj.exists():
      info=obj.values()
      log_runMES.to_debug({'TNS':'tx_query_workorder','info':info[0]})
      workorder_obj=obj[0]
      product_obj=workorder_obj.product
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'workorder_obj':workorder_obj,'product_obj':product_obj,'workorder_txt':workorder_txt}
    else:
      return {'TNS':tns,'ECD':'W01','ETX':'Work Order Not Exist','workorder_txt':workorder_txt}
  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'workorder_txt':workorder_txt})
    return {'TNS':tns,'ERR':e,'workorder_txt':workorder_txt}

@transaction.atomic
# lot start by input lot id, product then find related modeling for process flow, process step, recipe, change lot state
def tx_lot_start(lot_txt,qty_int,work_order_txt,lot_type_txt,op_txt,product_txt,annotation_txt):
  tns='tx_lot_start'
  # fill next process flow, step, recipe, start time to lot table
  try:
    # limited lot id length to 20, reserved for split lot
    if len(lot_txt)>16:
      return {'TNS':tns,'ECD':'L18','ETX':_('Lot Start ID Exceed Max Length'),'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    # validate slug
    if slug(lot_txt) is not True:
      return {'TNS':tns,'ECD':'L16','ETX':_('Lot ID Illegal'),'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    # check lot duplication
    obj=models.LotStartHist.objects.filter(lot=lot_txt)
    if obj:
      return {'TNS':tns,'ECD':'L02','ETX':_('Lot ID Duplicated'),'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    #find 1st process step
    work_order_obj=models.WorkOrder.objects.get(name=work_order_txt)
    process_obj=work_order_obj.product.process
    pp_step_set=models.ProcessProcessStep.objects.filter(process=process_obj)
    pp_step_obj=pp_step_set.first()
    process_step_obj=pp_step_obj.process_step
    qty_left=work_order_obj.qty_left
    if qty_left<qty_int:  # qty left not enough
      return {'TNS':tns,'ECD':'W02','ETX':_('Remaining Qty Not Sufficient'),'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    reply=tx_add_new_lot(lot_txt,work_order_obj,product_txt,process_step_obj,process_obj,qty_int,lot_type_txt,annotation_txt)
    if reply['ECD']!='0':
      return {'TNS':tns,'ECD':reply['ECD'],'ETX':reply['ETX'],'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}

    work_order_obj.qty_left=qty_left-qty_int
    work_order_obj.save()

    # def tx_log_lot_step_hist(tid_txt,lot_txt,eq_txt,op_txt,anno_txt):
    tid=str(uuid.uuid4())
    reply=tx_log_lot_step_hist(tns,tid,lot_txt,'',op_txt,'')
    if reply['ECD']!='0':
      return {'TNS':tns,'ECD':reply['ECD'],'ETX':reply['ETX'],'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}

    # lot start hist
    hist_obj=models.LotStartHist.objects.create(
      work_order=work_order_txt,
      lot=lot_txt,
      qty=qty_int,
      type=lot_type_txt,
      op=op_txt,
      annotation=annotation_txt
    )
    hist_obj.save()
    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    log_runMES.to_info(msg)
    return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}

  except Exception as e:
    mylog.exception(e)
    return {'TNS':tns,'ERR':e,'LOT':lot_txt,'Product':product_txt,'WORK ORDER':work_order_txt,'QTY':qty_int}

@transaction.atomic
# lot start by input lot id, product then find related modeling for process flow, process step, recipe, change lot state
def tx_batch_lot_start(pre_lot_txt,qty_int,work_order_txt,lot_type_txt,op_txt,product_txt,annotation_txt):
  tns='tx_batch_lot_start'
  tid=str(shortuuid.uuid())
  # fill next process flow, step, recipe, start time to lot table
  try:
    # limited batch lot id length to 16, reserved for sequence number and split lot
    if len(pre_lot_txt)>12:
      return {'TNS':tns,'ECD':'L18','ETX':_('Lot Start ID Exceed Max Length'),'lot':pre_lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    if slug(pre_lot_txt) is not True:
      return {'TNS':tns,'ECD':'L16','ETX':_('Lot ID Illegal'),'lot':pre_lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    work_order_obj=models.WorkOrder.objects.get(name=work_order_txt)
    process_obj=work_order_obj.product.process
    pp_step_set=models.ProcessProcessStep.objects.filter(process=process_obj)
    pp_step_obj=pp_step_set.first()
    process_step_obj=pp_step_obj.process_step
    qty_left=work_order_obj.qty_left
    total_qty=qty_left
    if qty_int<=0:
      return {'TNS':tns,'ECD':'L14','ETX':_('Lot Qty Error'),'lot':pre_lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    if qty_left/qty_int>9999:
      return {'TNS':tns,'ECD':'L19','ETX':_('Lot Batch Size Exceed'),'lot':pre_lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
    product_obj=models.Product.objects.get(name=product_txt)
    if process_step_obj.step_check:
      step_check=process_step_obj.step_check.name
    else:
      step_check=None
    if process_step_obj.dcplan:
      step_dcplan=process_step_obj.dcplan.name
    else:
      step_dcplan=None
    if process_step_obj.binning:
      step_binning=process_step_obj.binning.name
    else:
      step_binning=None
    if process_step_obj.breaking:
      step_breaking=process_step_obj.breaking.name
    else:
      step_breaking=None

    #ooperation_choices=(('SC','StepCheck'),('SI','StepIn'),('SO','StepOut'),('DC','DC'),('BK','Breaking'),('BI','Binning'),('NP','New Product'),('NO','None'))
    operation='SI'
    #location_choices=(('F','InFab'),('E','InEQ'),('O','OutSide'))
    curr_location="F"

    if qty_left<qty_int:  # qty left not enough
      msg={'TNS':tns,'ECD':'W02','ETX':_('Remaining Qty Not Sufficient'),'PRE LOT':pre_lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
      mylog.error(msg)
      return msg
    cnt=1
    lot_set=[]
    while qty_left>0:
      if qty_left<qty_int:
        qty_int=qty_left
      lot_txt=pre_lot_txt+'-'+str(cnt)
      # check lot duplication
      obj=models.LotStartHist.objects.filter(lot=lot_txt)
      if obj:
        msg={'TNS':tns,'ECD':'L02','ETX':_('Lot ID Duplicated'),'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
        mylog.error(msg)
        return msg

      models.Lot.objects.create(
        name=lot_txt,
        product=product_obj,
        step_recipe=process_step_obj.recipe,
        process_step=process_step_obj,
        process=process_obj,
        step_check=step_check,
        step_dcplan=step_dcplan,
        step_binning=step_binning,
        step_breaking=step_breaking,
        workorder=work_order_obj.name,
        qty=qty_int,
        lot_priority=work_order_obj.lot_priority,
        curr_location=curr_location,
        owner=work_order_obj.owner,
        target_time=work_order_obj.target_date,
        lot_type=lot_type_txt,
        next_operation=operation,
      )

      lot_set.append(lot_txt)
      # def tx_log_lot_step_hist(tid_txt,lot_txt,eq_txt,op_txt,anno_txt):
      reply=tx_log_lot_step_hist(tns,tid,lot_txt,'',op_txt,'')
      if reply['ECD']!='0':
        msg={'TNS':tns,'ECD':reply['ECD'],'ETX':reply['ETX'],'lot':lot_txt,'product':product_txt,'work_order_txt':work_order_txt,'qty':qty_int}
        mylog.error(msg)
        return msg

      # lot start hist
      hist_obj=models.LotStartHist.objects.create(
        work_order=work_order_txt,
        lot=lot_txt,
        qty=qty_int,
        type=lot_type_txt,
        op=op_txt,
        transaction=tns,
        tid=tid,
        annotation=annotation_txt
      )
      hist_obj.save()
      qty_left=qty_left-qty_int
      cnt=cnt+1

    work_order_obj.qty_left=qty_left
    work_order_obj.save()
    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT SET':lot_set,'PRODUCT':product_txt,'WORK ORDER':work_order_txt,'TOTAL QTY':total_qty}
    log_runMES.to_info(msg)
    return msg

  except Exception as e:
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'PRE LOT':pre_lot_txt,'PRODUCT':product_txt,'WORK ORDER':work_order_txt,'QTY':qty_int}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_step_in(lot_txt,eq_txt,op_txt,anno_txt):
  log_runMES.to_debug({'TNS':'step_in','Lot':lot_txt,'EQ':eq_txt,'OP':op_txt,'Annotation':anno_txt})
  tns='tx_step_in'
  tid=str(shortuuid.uuid())
  sid=transaction.savepoint()
  try:
    lot_set=models.Lot.objects.filter(name=lot_txt)
    if not lot_set:
      return {'TNS':tns,'ECD':'L12','ETX':_('Lot Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    eq_set=models.Eq.objects.filter(name=eq_txt)
    if not eq_set:
      return {'TNS':tns,'ECD':'E05','ETX':_('EQ Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    lot_obj=models.Lot.objects.get(name=lot_txt)

    if lot_obj.next_operation!='SI':
      return {'TNS':tns,'ECD':'L08','ETX':_('Next Operation Mismatch'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    #check lot hold
    if lot_obj.is_hold:
      return {'TNS':tns,'ECD':'L03','ETX':_('Lot In Hold'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    #check lot control state
    #ctrl_state_choices=(('R','Run'),('I','Idle'),('F','Finish'),('S','Ship'),('T','Terminate'),('B','Bank'))
    if lot_obj.ctrl_state is not "I":
      return {'TNS':tns,'ECD':'L01','ETX':_('Lot State Mismatch'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    eq_obj=models.Eq.objects.get(name=eq_txt)

    #check eq hold
    if eq_obj.is_hold:
      return {'TNS':tns,'ECD':'E03','ETX':_('EQ in Hold'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    #check eq state
    #ctrl_state_choices=(('RA','Run Available'),('RN','Run Not Available'),('PM','Maintenance'),('ID','Idle'),('DM','Down'),('LN','Lend'),('SU','Setup'))
    eq_state_change=False
    if eq_obj.ctrl_state not in ['RA','ID','LN']:
      return {'TNS':tns,'ECD':'E01','ETX':_('EQ Not Available'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
    if eq_obj.ctrl_state=='ID':
      eq_state_change=True
      eq_obj.ctrl_state='RA'

    #check lot step
    if not lot_obj.process_step:
      return {'TNS':tns,'ECD':'S01','ETX':_('Process Step Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    #check eq match step
    if lot_obj.process_step.eq_group!=eq_obj.group:
      return {'TNS':tns,'ECD':'E02','ETX':_('EQ Not Match Lot Process Step'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    #check step check compare lot recipe, product with eq last recipe, product and EQ last step check whether need step check
    if lot_obj.step_check:
      eq_last_product=''
      eq_last_recipe=''
      if eq_obj.last_product:
        eq_last_product=eq_obj.last_product.name
      if eq_obj.last_recipe:
        eq_last_recipe=eq_obj.last_recipe
      if lot_obj.step_recipe!=eq_last_recipe or lot_obj.product.name!=eq_last_product:
        eq_grp=eq_obj.group
        eq_rec=models.EqRecord.objects.filter(eq_group=eq_grp,active=True,freeze=True)
        if eq_rec: #if EQ Record exist
          if lot_obj.process_step.step_check != eq_obj.last_eq_record:
            log_runMES.to_debug({'TNS':tns,'eq_rec':eq_rec[0],'eq_last_rec':eq_obj.last_eq_record})
            return {'TNS':tns,'ECD':'E04','ETX':_('Require Step Check-EQ Record'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt,"New Recipe":lot_obj.step_recipe,'Old Recipe':eq_obj.last_recipe,'New Product':lot_obj.product.name,'Old Product':eq_obj.last_product}

    #update EQ last recipe and product
    eq_obj.last_product=lot_obj.product
    eq_obj.last_recipe=lot_obj.step_recipe
    if eq_obj.last_eq_record:
      eq_obj.last_eq_record=None #reset last eq record
    eq_obj.save()

    #update lot info
    #location_choices=(('F','InFab'),('E','InEQ'),('O','OutSide'))
    lot_obj.curr_location='E'
    lot_obj.curr_area=eq_obj.area
    lot_obj.curr_eq=eq_obj
    lot_obj.run_id=uuid.uuid4()
    lot_obj.ctrl_state='R'

    # query next OP
    # def qry_next_op(lot_txt):
    reply=qry_next_op(lot_txt)
    if reply['ECD']!='0':
      mylog.error({'TNS':tns,'reply':reply,'LOT':lot_txt})
      return {'TNS':tns,'reply':reply,'LOT':lot_txt}
    next_op=reply['NEXT_OP']
    lot_obj.next_operation=next_op
    lot_obj.last_step='SI'
    lot_obj.last_step_time=timezone.now()
    lot_obj.save()

    # def tx_log_lot_step_hist(tid_txt,lot_txt,eq_txt,op_txt,anno_txt):
    tid=str(shortuuid.uuid())
    reply=tx_log_lot_step_hist(tns,tid,lot_txt,eq_txt,op_txt,anno_txt)
    if reply['ECD']!='0':
      return {'TNS':tns,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt,'reply':reply}
    if eq_state_change:
      hist_obj=models.EqStateHist.objects.create(eq=eq_txt,op=op_txt,ctrl_state=eq_obj.ctrl_state,transaction=tns,tid=tid,annotation=anno_txt)
      hist_obj.save()

    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'RECIPE':lot_obj.step_recipe,'QTY':lot_obj.qty,'EQ':eq_txt,'NEXT_OP':next_op,'OP':op_txt}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,"ERR":e,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
    mylog.error(msg)
    return msg

# input paramenters: lot, eq, op, annotation
@transaction.atomic
def tx_step_out(lot_txt,eq_txt,op_txt,anno_txt):
  OK='0'
  tns='tx_step_out'
  tid=str(shortuuid.uuid())
  #log_runMES.to_debug({'TNS':tns,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt})
  sid=transaction.savepoint()
  try:
    lot_set=models.Lot.objects.filter(name=lot_txt)
    if not lot_set:
      return {'TNS':tns,'ECD':'L12','ETX':_('Lot Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
    lot_obj=models.Lot.objects.get(name=lot_txt)
    if lot_obj.next_operation!='SO':
      return {'TNS':tns,'ECD':'L08','ETX':_('Next Operation Mismatch'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
    if lot_obj.curr_eq.name!=eq_txt:
      return {'TNS':tns,'ECD':'E02','ETX':_('EQ Not Match Lot'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
    eq_set=models.Eq.objects.filter(name=eq_txt)
    if not eq_set:
      return {'TNS':tns,'ECD':'E05','ETX':_('EQ Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    #ctrl_state_choices=(('R','Run'),('I','Idle'),('F','Finish'),('S','Ship'),('T','Terminate'),('B','Bank'))
    if lot_obj.ctrl_state!='R':
      return {'TNS':tns,'ECD':'L01','ETC':_('Lot State Mismatch'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}

    eq_obj=models.Eq.objects.get(name=eq_txt)
    if lot_obj.curr_eq!=eq_obj:
      return {'TNS':tns,'LOT':lot_txt,'ECD':'E01','ETX':_('EQ Not Match Lot'),'EQ':eq_txt,'OP':op_txt}

    # def tx_log_lot_step_hist(tid_txt,lot_txt,eq_txt,op_txt,anno_txt):
    reply=tx_log_lot_step_hist(tns,tid,lot_txt,eq_txt,op_txt,anno_txt)
    if reply['ECD']!=OK:
      msg={'TNS':tns,'LOT':lot_txt,'reply':reply}
      mylog.error(msg)
      return msg

    #query next OP
    #def qry_next_op(lot_txt):
    reply=qry_next_op(lot_txt)
    if reply['ECD']!='0':
      msg={'TNS':tns,'LOT':lot_txt,'reply':reply}
      mylog.error(msg)
      return msg
    next_op=reply['NEXT_OP']
    lot_obj.next_operation=next_op

    # breaking step assign new product, process, step
    if lot_obj.process_step.breaking:
      # break with new product
      prod_obj=lot_obj.process_step.breaking.new_product
      log_runMES.to_debug({'TNS':tns,'New Product':prod_obj.name,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt})
      lot_obj.product=prod_obj
      # new product with process
      if prod_obj.process:
        lot_obj.process=prod_obj.process
        pp_obj=models.ProcessProcessStep.objects.filter(process=lot_obj.process)
        next_step_obj=pp_obj.first().process_step
        lot_obj.process_step=next_step_obj
        if next_step_obj.dcplan:
          lot_obj.step_dcplan=next_step_obj.dcplan.name
        else:
          lot_obj.step_dcplan=None
        if next_step_obj.binning:
          lot_obj.step_binning=next_step_obj.binning.name
        else:
          lot_obj.step_binning=None
        if next_step_obj.step_check:
          lot_obj.step_check=next_step_obj.step_check.name
        else:
          lot_obj.step_check=None
        if next_step_obj.breaking:
          lot_obj.step_breaking=next_step_obj.breaking.name
        else:
          lot_obj.step_breaking=None

        lot_obj.next_operation="SI"
        lot_obj.ctrl_state='I'
        lot_obj.step_recipe=next_step_obj.recipe
      else:  #new product no process, no other step after change product
        lot_obj.process=None
        lot_obj.process_step=None
        lot_obj.step_dcplan=None
        lot_obj.step_binning=None
        lot_obj.step_check=False
        lot_obj.step_breaking=None
        lot_obj.ctrl_state='F'
        lot_obj.next_operation="NO"

      lot_obj.curr_location='F'
      lot_obj.curr_eq=None
      lot_obj.run_id=None

    else:  # non breaking step
      #log_runMES.to_debug({'TNS':tns,'no Breaking':lot_obj.next_operation,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt})
      #operation_choices=(('SC','StepCheck'),('SI','StepIn'),('SO','StepOut'),('DC','DC'),('BK','Breaking'),('BI','Binning'),('NP','New Product'),('NO','None'))
      if next_op=='NO':
        # Lot ctrl_state_choices=(('R','Run'),('I','Idle'),('F','Finish'),('S','Ship'),('T','Terminate'),('B','Bank'))
        lot_obj.ctrl_state='F'
        #lo_obj.process=None
        lot_obj.process_step=None
        lot_obj.step_dcplan=''
        lot_obj.step_binning=''
        lot_obj.step_recipe=''
        # Lot location_choices=(('F','InFab'),('E','InEQ'),('O','OutSide'))
        lot_obj.curr_location='F'
        #lot_obj.curr_area=''
        lot_obj.curr_eq=None
        lot_obj.run_id=None

      # find next process_step
      else:
        found=False
        pp_obj=models.ProcessProcessStep.objects.filter(process=lot_obj.process)
        for p in pp_obj:
          if found is True:
            next_step_obj=p.process_step
            lot_obj.process_step=next_step_obj
            if next_step_obj.dcplan:
              lot_obj.step_dcplan=next_step_obj.dcplan.name
            else:
              lot_obj.step_dcplan=''
            if next_step_obj.breaking:
              lot_obj.step_breaking=next_step_obj.breaking.name
            else:
              lot_obj.step_breaking=''
            if next_step_obj.binning:
              lot_obj.step_binning=next_step_obj.binning.name
            else:
              lot_obj.step_binning=''
            if next_step_obj.step_check:
              lot_obj.step_check=next_step_obj.step_check.name
            else:
              lot_obj.step_check=False

            lot_obj.step_recipe=next_step_obj.recipe
            lot_obj.curr_location='F'
            lot_obj.curr_eq=None
            lot_obj.run_id=None
            lot_obj.ctrl_state='I'
            break
          if p.process_step==lot_obj.process_step:
            found=True

    lot_obj.last_step='SO'
    lot_obj.last_step_time=timezone.now()

    # if lot_obj.process_step:
    #   step=lot_obj.process_step
    # else:
    #   step=None
    next_operation=''
    if lot_obj.next_operation:
      next_operation=lot_obj.next_operation
    else:
      lot_obj.is_finish=True

    lot_obj.save()

    #check eq remaining lot, eq become idle if current lot is last one
    lot_count=models.Lot.objects.filter(curr_eq=eq_obj).count()
    eq_state_change=False
    if lot_count==0:
      #Eq ctrl_state_choices=(('RA','Run Available'),('RN','Run Not Available'),('PM','Maintenance'),('ID','Idle'),('DM','Down'),('LN','Lend'),('SU','Setup'))
      if eq_obj.ctrl_state=='RA':
        eq_obj.ctrl_state='ID'
        eq_state_change=True
    if eq_obj.ctrl_state=='RN':
      eq_obj.ctrl_state='RA'
      eq_state_change=True

    eq_obj.save()

    # log eq state hist
    if eq_state_change:
      hist_obj=models.EqStateHist.objects.create(eq=eq_txt,op=op_txt,ctrl_state=eq_obj.ctrl_state,transaction=tns,tid=tid,annotation=anno_txt)
      hist_obj.save()

    product=''
    if lot_obj.product:
      product=lot_obj.product.name

    msg={'TNS':tns,'LOT':lot_txt,'ECD':'0','ETX':_('Succeed'),"EQ":eq_txt,'QTY':lot_obj.qty,'OP':op_txt,'NEXT_OP':next_operation,'PRODUCT':product}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_dc_spec(dc_type_txt,dcplan_dcitem_obj,dcitem_spec_obj,val_txt,lot_txt,eq_txt,op_txt):
  log_runMES.to_info({'TNS':'tx_dc_spec','dc_type_txt':dc_type_txt,'dcplan_dcitem_obj':dcplan_dcitem_obj,'dcplan':dcplan_dcitem_obj.dcplan,'val':val_txt,'lot':lot_txt,'eq':eq_txt,'op':op_txt})
  tns='tx_dc_spec'
  tid=str(shortuuid.uuid())
  try:
    violation=''
    spec=''
    contents_txt={'OOS':violation,'ITEM':dcitem_spec_obj.dcitem.name,'VAL':val_txt}
    step=''
    run_id=None
    send_mail=None
    hold_eq=None
    hold_lot=None
    lot_obj=None

    #if check text
    if dcitem_spec_obj.exact_text:
      spec=dcitem_spec_obj.exact_text
      if val_txt==spec:
        contents_txt={'OOS':violation,'ITEM':dcitem_spec_obj.dcitem.name,'VAL':val_txt,'SPEC':spec,'ITEM_SPEC':dcitem_spec_obj.name,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
        #log_runMES.to_debug({'TNS':tns,'point':'No err reply','contents':contents_txt})
      else:
        violation='Exact_Text'
        contents_txt={'OOS':violation,'ITEM':dcitem_spec_obj.dcitem.name,'VAL':val_txt,'SPEC':spec}

    #check numerical value
    elif dcitem_spec_obj.spec_low:
      val_float=float(val_txt)
      spec_low=dcitem_spec_obj.spec_low
      if val_float<spec_low:
        violation='SPEC LOW'
        spec=str(dcitem_spec_obj.spec_low)
        contents_txt={'OOS':violation,'ITEM':dcitem_spec_obj.dcitem.name,'VAL':val_txt,'SPEC LOW':spec}
      if dcitem_spec_obj.spec_high:
        val_float=float(val_txt)
        spec_high=dcitem_spec_obj.spec_high
        if val_float>spec_high:
          violation='SPEC HIGH'
          spec=str(dcitem_spec_obj.spec_high)
          contents_txt={'OOS':violation,'ITEM':dcitem_spec_obj.dcitem.name,'VAL':val_txt,'SPEC HIGH':spec}
    #log_runMES.to_debug({'TNS':tns,'point':'after spec check','contents':contents_txt})

    #send mail, hold lot, hold EQ
    if violation is not '':
      if dcitem_spec_obj.OOS_hold_lot:
        if lot_txt:
          if not models.Lot.objects.filter(name=lot_txt):
            msg={'TNS':tns,'ECD':'L12','ETX':_('Lot Not Exist'),'ITEM_SPEC':dcitem_spec_obj.name,'DC PLAN':dcplan_dcitem_obj.dcplan.name,'VAL':val_txt,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
            mylog.error(msg)
            return msg
          lot_obj=models.Lot.objects.get(name=lot_txt)
          if lot_obj.process_step:
            step=lot_obj.process_step.name
          if lot_obj.run_id:
            run_id=lot_obj.run_id

          lot_obj.is_hold=True
          lot_obj.hold_reason=contents_txt
          lot_obj.save()
          log_runMES.to_debug({'TNS':tns,'lot_obj.is_hold':lot_obj.is_hold,'lot_obj.hold_reason':lot_obj.hold_reason})
          hold_lot=lot_txt
          hist_obj=models.LotHoldHist(lot=lot_txt,op=op_txt,hold_release='H',hold_code='OOS',run_id=run_id,transaction=tns,tid=tid)
          hist_obj.save()
          action={'Hold Lot':hold_lot}
          contents_txt.update(action)
      if dcitem_spec_obj.OOS_mail:
        if lot_txt:
          lot_obj=models.Lot.objects.get(name=lot_txt)
          if lot_obj.owner_mail:
            mail_addr=lot_obj.owner_mail
            # level='W'(Warning)
            sub_txt='Lot:'+lot_txt+' - OOS notice'
            m_obj=models.MailQueue(receiver=mail_addr,level='W',subject=sub_txt,contents=contents_txt,transaction=tns,tid=tid)
            m_obj.save()
            send_mail=mail_addr
      if eq_txt:
        if not models.Eq.objects.filter(name=eq_txt):
          msg={'TNS':tns,'ECD':'E05','ETX':_('EQ Not Exist'),'ITEM_SPEC':dcitem_spec_obj.name,'DC PLAN':dcplan_dcitem_obj.dcplan.name,'VAL':val_txt,'LOT':lot_txt,
               'EQ':eq_txt,'OP':op_txt}
          mylog.error(msg)
          return msg
        if dcitem_spec_obj.OOS_hold_eq:
          eq_obj=models.Eq.objects.get(name=eq_txt)
          eq_obj.is_hold=True
          eq_obj.hold_reason=contents_txt
          eq_obj.save()
          hist_obj=models.EqHoldHist(eq=eq_txt,op=op_txt,hold_release='H',hold_code='OOS',transaction=tns,tid=tid)
          hist_obj.save()
          hold_eq=eq_txt
          action={'Hold EQ':hold_eq}
          contents_txt.update(action)
        if dcitem_spec_obj.OOS_mail:
          eq_obj=models.Eq.objects.get(name=eq_txt)
          if eq_obj.group.owner_mail:
            mail_addr=eq_obj.group.owner_mail
            # level='W'(Warning)
            sub_txt='EQ:'+eq_txt+' - OOS notice'
            m_obj=models.MailQueue(receiver=mail_addr,level='W',subject=sub_txt,contents=contents_txt,transaction=tns,tid=tid)
            m_obj.save()
            send_mail=mail_addr

    #write to check_spec_hist
    o_hist=models.CheckSpecHist(lot=lot_txt,eq=eq_txt,dcitem_spec=dcitem_spec_obj.name,dcplan=dcplan_dcitem_obj.dcplan.name, dcitem=dcplan_dcitem_obj.dcitems.name,val=val_txt,violation=violation,exact_text=dcitem_spec_obj.exact_text,spec_target=dcitem_spec_obj.spec_target,spec_high=dcitem_spec_obj.spec_high,spec_low=dcitem_spec_obj.spec_low,OOS_hold_lot=dcitem_spec_obj.OOS_hold_lot,OOS_hold_eq=dcitem_spec_obj.OOS_hold_eq,OOS_mail=dcitem_spec_obj.OOS_mail,hold_lot=hold_lot,hold_eq=hold_eq,send_mail=send_mail,step=step,run_id=run_id,tid=tid)
    o_hist.save()
    #log_runMES.to_info(contents_txt)
    return contents_txt

  except Exception as e:
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'ITEM_SPEC':dcitem_spec_obj.name,'DC PLAN':dcplan_dcitem_obj.dcplan.name,'VAL':val_txt,'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
# item_set {'item_name':'item1','val':100}
def tx_dc(lot_txt,eq_txt,dcplan_txt,item_set,op_txt,anno_txt):
  tns='tx_dc'
  tid=str(shortuuid.uuid())
  log_runMES.to_info({'TNS':tns,'LOT':lot_txt,'EQ':eq_txt,'DC_PLAN':dcplan_txt,'ITEM_SET':item_set,'OP':op_txt,'ANNO':anno_txt})
  sid=transaction.savepoint()
  try:
    trans_time=str(datetime.now())
    lot_set=models.Lot.objects.filter(name=lot_txt)
    if not lot_set:
      return {'TNS':tns,'ECD':'L12','ETX':_('Lot Not Exist'),'LOT':lot_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set,'OP':op_txt}
    lot_obj=models.Lot.objects.get(name=lot_txt)
    eq_set=models.Eq.objects.filter(name=eq_txt)
    if not eq_set:
      return {'TNS':tns,'ECD':'E05','ETX':_('EQ Not Exist'),'LOT':lot_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set,'OP':op_txt}
    if lot_obj.curr_eq:
      if lot_obj.curr_eq.name!=eq_txt:
        return {'TNS':tns,'ECD':'E02','ETX':_('EQ Not Match Lot'),'LOT':lot_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set,'OP':op_txt}
    if lot_obj.process_step:
      if not lot_obj.process_step.dcplan:
        return {'TNS':tns,'ECD':'D01','ETX':_('Data Collection Not Exist'),'LOT':lot_txt,'OP':op_txt}
    # allow repeat DC (lot not in idle or after binning split)
    if lot_obj.ctrl_state=='I':
      return {'TNS':tns,'ECD':'L01','ETX':_('Lot State Mismatch'),'LOT':lot_txt,'OP':op_txt}
    dcplan_set=models.DcPlan.objects.filter(name=dcplan_txt)
    if not dcplan_set:
      return {'TNS':tns,'ECD':'D01','ETX':_('Data Collection Not Exist'),'LOT':lot_txt,'OP':op_txt,'DC_PLAN':dcplan_txt}

    run_id=lot_obj.run_id
    # log_runMES.to_debug({'TNS':tns,'run_id':run_id})
    step=''
    if lot_obj.process_step:
      step=lot_obj.process_step.name

    trans_type='S'
    dcplan_hist_obj=models.DcPlanHist(dcplan=dcplan_txt,transaction=tns,trans_type=trans_type,op=op_txt,lot=lot_txt,eq=eq_txt,step=step,run_id=run_id,tid=tid,annotation=anno_txt)
    dcplan_hist_obj.save()

    log_runMES.to_debug({'TNS':tns,'dcplan':dcplan_txt,'lot':lot_txt,'eq':eq_txt,'step':step,'trans_time':trans_time,'run_id':str(run_id),'annotation':anno_txt})

    dcplan_obj=models.DcPlan.objects.get(name=dcplan_txt)
    oos={}
    for item in item_set:
      #log_runMES.to_debug({'TNS':tns,'item':item})
      item_name=item['item_name']
      dcitem_obj=models.DcItem.objects.get(name=item_name)
      dcplan_dcitem_obj=models.DcPlanDcItem.objects.filter(dcplan=dcplan_obj,dcitems=dcitem_obj)
      if not dcplan_dcitem_obj:
        msg={'TNS':tns,'ECD':'D02','ETX':_('DC Item Not Exist'),'LOT':lot_txt,'OP':op_txt,'DC_PLAN':dcplan_txt,'ITEM_SET':item_set,'Item':item_name}
        mylog.error(msg)
        return msg

      item_category=dcplan_dcitem_obj[0].dcitems.dcitem_category.name
      item_type=dcplan_dcitem_obj[0].dcitems.dcitem_category.data_type
      item_unit=dcplan_dcitem_obj[0].dcitems.dcitem_category.unit
      item_val=item['val']
      log_runMES.to_debug({'TNS':tns,'item_name':item_name,'val':item_val,'category':item_category,'type':item_type,'unit':item_unit})
      #tx_write_dcvalue_hist(dcplan_hist_obj,dcitem,category,datatype,unit,value,tid):
      reply=tx_write_dcvalue_hist(dcplan_hist_obj,item_name,item_category,item_type,item_unit,item_val,tid)
      if reply['ECD']!='0':
        return {'TNS':tns,'LOT':lot_txt,'reply':reply}

      #check item_spec
      if dcplan_dcitem_obj[0].dcitem_spec:
        dcitem_spec_obj=dcplan_dcitem_obj[0].dcitem_spec
        dc_type='LOT'
        #def tx_dc_spec(dc_type_txt,dcplan_dcitem_obj,dcitem_spec_obj,val_txt,lot_txt,eq_txt,op_txt):
        spec_reply=tx_dc_spec(dc_type,dcplan_dcitem_obj[0],dcitem_spec_obj,str(item_val),lot_txt,eq_txt,op_txt)
        if spec_reply['OOS']!='':
          oos.update(spec_reply)

    # query next OP, if repeat DC will not request next OP
    # def qry_next_op(lot_txt):
    lot_obj=models.Lot.objects.get(name=lot_txt)
    if lot_obj.next_operation=='DC':
      reply=qry_next_op(lot_txt)
      if reply['ECD']!='0':
        msg={'TNS':tns,'LOT':lot_txt,'reply':reply}
        mylog.error(msg)
        return msg
      next_op=reply['NEXT_OP']
      lot_obj.next_operation=next_op
    lot_obj.save()

    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set,'OOS':oos,'NEXT_OP':lot_obj.next_operation}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'LOT':lot_txt,'DC_PLAN':dcplan_txt,'ITEM_SET':item_set,'EQ':eq_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_lot_record(lot_txt,eq_txt,step_txt,op_txt,dcplan_txt,item_set,anno_txt):
  tns='tx_lot_record'
  tid=str(shortuuid.uuid())
  log_runMES.to_debug({'TNS':tns,'lot':lot_txt,'eq':eq_txt,'step_txt':step_txt,'op_txt':op_txt,'dcplan':dcplan_txt,'item_set':item_set})
  sid=transaction.savepoint()
  try:
    step_set=models.LotRecord.objects.filter(name=step_txt)
    if not step_set:
      return {'TNS':tns,'ECD':'L20','ETX':_('Lot Record Not Exist'),'LOT':lot_txt,'STEP':step_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set}
    plan_set=models.DcPlan.objects.filter(name=dcplan_txt)
    if not plan_set:
      return {'TNS':tns,'ECD':'D01','ETX':_('Data Collection Not Exist'),'LOT':lot_txt,'STEP':step_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set}
    trans_time=str(timezone.now())
    process_step=step_txt
    recipe=''
    process=''
    product=''
    qty=''
    run_id=None
    l=models.LotStepHist(transaction=tns,tid=tid,lot=lot_txt,eq=eq_txt,op=op_txt,qty=qty,recipe=recipe,product=product,process=process,process_step=process_step,run_id=run_id,annotation=anno_txt)
    l.save()

    if dcplan_txt:  # with DC
      trans_type='R'
      dcplan_hist_obj=models.DcPlanHist(dcplan=dcplan_txt,transaction=tns,trans_type=trans_type,op=op_txt,lot=lot_txt,eq=eq_txt,step=step_txt,tid=tid,annotation=anno_txt)
      dcplan_hist_obj.save()

      dcplan_obj=models.DcPlan.objects.get(name=dcplan_txt)
      #spec_err={}
      for item in item_set:
        # log_runMES.to_debug({'item':item})
        item_name=item['item_name']
        dcitem_obj=models.DcItem.objects.get(name=item_name)
        dcplan_dcitem_obj=models.DcPlanDcItem.objects.filter(dcplan=dcplan_obj,dcitems=dcitem_obj)
        if not dcplan_dcitem_obj:
          msg={'TNS':tns,'ECD':'D02','ETX':_('DC Item Not Exist'),'LOT':lot_txt,'OP':op_txt,'DC_PLAN':dcplan_txt,'ITEM_SET':item_set,'Item':item_name}
          mylog.error(msg)
          return msg
        item_category=dcplan_dcitem_obj[0].dcitems.dcitem_category.name
        item_type=dcplan_dcitem_obj[0].dcitems.dcitem_category.data_type
        item_unit=dcplan_dcitem_obj[0].dcitems.dcitem_category.unit
        item_val=item['val']
        #log_runMES.to_debug({'name':item_name,'val':item_val,'category':item_category,'type':item_type,'unit':item_unit})
        reply=tx_write_dcvalue_hist(dcplan_hist_obj,item_name,item_category,item_type,item_unit,item_val,tid)
        if reply['ECD']!='0':
          msg={'TNS':tns,'LOT':lot_txt,'reply':reply}
          mylog.error(msg)
          return msg

    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':'tx_lot_record','ERR':e,'LOT':lot_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_eq_record(eq_txt,eq_record_txt,op_txt,dcplan_txt,item_set,anno_txt):
  tns='tx_eq_record'
  tid=str(shortuuid.uuid())
  log_runMES.to_debug({'TNS':tns,'op_txt':op_txt,'dcplan':dcplan_txt,'item_set':item_set})
  sid=transaction.savepoint()
  try:
    eq_record_set=models.EqRecord.objects.filter(name=eq_record_txt)
    if not eq_record_set:
      return {'TNS':tns,'ECD':'E06','ETX':_('EQ Record Not Exist'),'EQ RECORD':eq_record_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set}

    plan_set=models.DcPlan.objects.filter(name=dcplan_txt)
    if not plan_set:
      return {'TNS':tns,'ECD':'D01','ETX':_('Data Collection Not Exist'),'EQ RECORD':eq_record_txt,'DC_PLAN':dcplan_txt,'EQ':eq_txt,'ITEM_SET':item_set}

    trans_time=str(timezone.now())
    eq_obj=models.Eq.objects.get(name=eq_txt)
    eq_record_obj=models.EqRecord.objects.get(name=eq_record_txt)
    eq_obj.last_eq_record=eq_record_obj
    eq_obj.eq_record_time=timezone.now()
    eq_obj.save()
    trans_type='E'
    dcplan_hist_obj=models.DcPlanHist(dcplan=dcplan_txt,transaction=tns,trans_type=trans_type,op=op_txt,lot='',eq=eq_txt,step='',run_id=None,tid=tid,annotation=anno_txt)
    dcplan_hist_obj.save()

    # data={'tns':tns,'dcplan_hist_id':dcplan_hist_obj.pk,'dcplan':dcplan_txt,'trans_type':trans_type,'lot':'','eq':eq_txt,'step':'','trans_time':trans_time,'run_id':'','annotation':anno_txt}
    # json_msg=json.dumps(data,ensure_ascii=False)
    # dcplan_json.debug(json_msg)
    dcplan_obj=models.DcPlan.objects.get(name=dcplan_txt)
    oos={}
    for item in item_set:
      # log_runMES.to_debug({'item':item})
      item_name=item['item_name']
      dcitem_obj=models.DcItem.objects.get(name=item_name)
      dcplan_dcitem_obj=models.DcPlanDcItem.objects.filter(dcplan=dcplan_obj,dcitems=dcitem_obj)
      if not dcplan_dcitem_obj:
        return {'TNS':tns,'ECD':'D02','ETX':_('DC Item Not Exist'),'EQ':eq_txt,'OP':op_txt,'DC_PLAN':dcplan_txt,'ITEM_SET':item_set,'Item':item_name}
      item_category=dcplan_dcitem_obj[0].dcitems.dcitem_category.name
      item_type=dcplan_dcitem_obj[0].dcitems.dcitem_category.data_type
      item_unit=dcplan_dcitem_obj[0].dcitems.dcitem_category.unit
      item_val=item['val']
      log_runMES.to_debug({'TNS':tns,'name':item_name,'val':item_val,'category':item_category,'type':item_type,'unit':item_unit})
      reply=tx_write_dcvalue_hist(dcplan_hist_obj,item_name,item_category,item_type,item_unit,item_val,tid)
      if reply['ECD']!='0':
        return {'TNS':tns,'reply':reply}

      #check item_spec
      if dcplan_dcitem_obj[0].dcitem_spec:
        dcitem_spec_obj=dcplan_dcitem_obj[0].dcitem_spec
        dc_type='EQ'
        # def tx_dc_spec(dc_type_txt,dcplan_dcitem_obj,dcitem_spec_obj,val_txt,lot_txt,eq_txt,op_txt):
        spec_reply=tx_dc_spec(dc_type,dcplan_dcitem_obj[0],dcitem_spec_obj,str(item_val),'',eq_txt,op_txt)
        log_runMES.to_debug({'TNS':'tx_eq_record','spec_reply':spec_reply})
        #if 'OOS' in spec_reply:
        if spec_reply['OOS']!='':
          oos.update(spec_reply)

    msg={'TNS':tns,'ECD':'0','ETX':'OK','EQ':eq_txt,'ITEM_SET':item_set,'OOS':oos}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'DC_PLAN':dcplan_txt,'EQ':eq_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_work_order(order_txt,erp_ref_txt,product_txt,lot_type_txt,qty_int,lot_priority_int,target_date_txt,op_txt,owner_txt,owner_email_txt,owner_phone_txt,instruction_txt,annotation_txt):
  tns='tx_work_order'
  sid=transaction.savepoint()
  try:
    log_runMES.to_debug({'tns':tns,'work order':order_txt,'ERP_ref':erp_ref_txt,'product':product_txt,'lot_type':lot_type_txt,'qty':str(qty_int),'lot_priority':str(lot_priority_int),'target_date':target_date_txt,'op':op_txt,'owner':owner_txt,'owner_mail':owner_email_txt,'owner_phone':owner_phone_txt,'instruction':instruction_txt,'annotation':annotation_txt})
    # check product exist
    product_set=models.Product.objects.filter(name=product_txt)
    if product_set:
      product_obj=product_set[0]
    else:
      return {'TNS':tns,'ECD':'P01','ETX':_('Product Not Exist'),'WORK_ORDER':order_txt,'PRODUCT':product_set}

    wo_set=models.WorkOrder.objects.filter(name=order_txt)
    if wo_set:
      return {'TNS':tns,'ECD':'W03','ETX':_('Work Order Duplicated'),'WORK_ORDER':order_txt}

    if qty_int < 1:
      return {'TNS':tns,'ECD':'W04','ETX':_('Work Order Qty Error'),'WORK_ORDER':order_txt,'Qty':str(qty_int)}

    if lot_priority_int < 1 or lot_priority_int > 5:
      return {'TNS':tns,'ECD':'W05','ETX':_('Work Order Priority Error'),'WORK_ORDER':order_txt,'Priority':str(qty_int)}

    #lot_type_choices=(('P','Product'),('E','Engineer'),('D','Dummy'),('M','Monitor'))
    if lot_type_txt not in 'PEDM':
      return {'TNS':tns,'ECD':'W06','ETX':_('Work Order Lot Type Error'),'WORK_ORDER':order_txt,'LOT TYPE':lot_type_txt}

    #check target date time
    # if datetime.strptime(target_date_txt,'%Y-%m-%d') < datetime.now():
    #   return {'TNS':tns,'ECD':'W07','ETX':_('Work Order Target DateTime Error'),'WORK_ORDER':order_txt,'TARGET DATETIME':target_date_txt}

    #validate email addr
    if not email(owner_email_txt):
      return {'TNS':tns,'ECD':'M01','ETX':_('Mail Format Error'),'WORK_ORDER':order_txt,'OWNER EMAIL':owner_email_txt}

    d=datetime.strptime(target_date_txt,"%Y-%m-%d")
    local_time=timezone.get_current_timezone()
    target_date=local_time.localize(d)

    models.WorkOrder.objects.create(name=order_txt,ERP_ref=erp_ref_txt,product=product_obj,lot_type=lot_type_txt,qty=qty_int,qty_left=qty_int,lot_priority=lot_priority_int,target_date=target_date,op=op_txt,owner=owner_txt,owner_email=owner_email_txt,owner_phone=owner_phone_txt,instruction=instruction_txt,active=True,freeze=True)
    models.WorkOrderHist.objects.create(name=order_txt,ERP_ref=erp_ref_txt,product=product_obj,lot_type=lot_type_txt,qty=qty_int,qty_left=qty_int,lot_priority=lot_priority_int,target_date=target_date,op=op_txt,owner=owner_txt,owner_email=owner_email_txt,owner_phone=owner_phone_txt,instruction=instruction_txt,active=True,freeze=True)
    transaction.savepoint_commit(sid)
    return {'TNS':tns,'ECD':'0','ETX':'Succeed','ORDER':order_txt,'ERP_ref':erp_ref_txt,'PRODUCT':product_txt,'qty':qty_int,'op':op_txt,'target_date':target_date_txt,'owner':owner_txt,'annotation':annotation_txt}

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    return {'TNS':tns,'ECD':'U01','ERR':e,'WORKORDER':order_txt}

@transaction.atomic
def tx_batch_work_order(work_order_list):
  tns='tx_batch_work_order'
  sid=transaction.savepoint()
  try:
    for wo in work_order_list:
      reply=tx_work_order(wo)
      if reply['ECD']!='0':
        return reply

    transaction.savepoint_commit(sid)
    return {'TNS':'tx_work_order','ECD':'0','ETX':'Succeed','WORKORDER LIST':work_order_list}

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    return {'TNS':tns,'ERR':e,'WORKORDER LIST':work_order_list}

def tx_work_order_change(order_txt,op_txt,is_close_bol,close_date_txt,active_bol):
  tns='tx_work_order_change'
  try:
    log_runMES.to_debug({'tns':tns,'work order':order_txt,'op':op_txt,'is_close':str(is_close_bol),'close_date':close_date_txt,'active':active_bol})

    # check product exist
    wo_set=models.WorkOrder.objects.filter(name=order_txt)
    if wo_set:
      wo_obj=wo_set[0]
    else:
      return {'TNS':tns,'ECD':'W01','ETX':_('Work Order Not Exist'),'WORK_ORDER':order_txt}
    erp_ref_txt=wo_obj.ERP_ref
    product_obj=wo_obj.product
    qty_int=wo_obj.qty
    lot_priority_int=wo_obj.lot_priority
    lot_type_txt=wo_obj.lot_type
    target_date_txt=wo_obj.target_date
    # check target date time
    if close_date_txt:
      if datetime.date(datetime.strptime(close_date_txt,'%Y-%m-%d'))< datetime.date(wo_obj.start_date):
        return {'TNS':tns,'ECD':'W07','ETX':_('Work Order Close DateTime Error'),'WORK_ORDER':order_txt,'CLOSE DATETIME':close_date_txt}
      wo_obj.close_date=datetime.strptime(close_date_txt,'%Y-%m-%d')
    owner_txt=wo_obj.owner
    owner_email_txt=wo_obj.owner_email
    owner_phone_txt=wo_obj.owner_phone
    instruction_txt=wo_obj.instruction
    active=active_bol
    wo_obj.active=active
    wo_obj.is_close=is_close_bol
    wo_obj.save()
    #
    models.WorkOrderHist.objects.create(name=order_txt,ERP_ref=erp_ref_txt,product=product_obj,lot_type=lot_type_txt,qty=qty_int,qty_left=qty_int,lot_priority=lot_priority_int,target_date=target_date_txt,op=op_txt,owner=owner_txt,owner_email=owner_email_txt,owner_phone=owner_phone_txt,instruction=instruction_txt,active=active,freeze=True)

    return {'TNS':tns,'ECD':'0','ETX':'Succeed','ORDER':order_txt,'ERP_ref':erp_ref_txt,'op':op_txt,'is_close':str(is_close_bol),'close_date':close_date_txt,'active':active_bol}

  except Exception as e:
    mylog.exception(e)
    return {'TNS':tns,'ECD':'U01','ERR':e,'WORKORDER':order_txt}

@transaction.atomic()
def tx_lot_bin(lot_txt,eq_txt,bin_txt,grade_set,op_txt,anno_txt):
  tns='tx_lot_bin'
  tid=str(shortuuid.uuid())
  log_runMES.to_info({'TNS':tns,'LOT':lot_txt,'EQ':eq_txt,'BIN':bin_txt,'GRADE_SET':grade_set,'OP':op_txt,'ANNO':anno_txt})
  sid=transaction.savepoint()
  try:
    lot_set=models.Lot.objects.filter(name=lot_txt)
    if not lot_set:
      msg={'TNS':tns,'ECD':'L12','ETX':_('Lot Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'BIN':bin_txt,'GRADE_SET':grade_set,'OP':op_txt}
      mylog.error(msg)
      return msg
    lot_obj=models.Lot.objects.get(name=lot_txt)
    eq_set=models.Eq.objects.filter(name=eq_txt)
    if not eq_set:
      msg={'TNS':tns,'ECD':'E05','ETX':_('EQ Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'BIN':bin_txt,'GRADE_SET':grade_set,'OP':op_txt}
      mylog.error(msg)
      return msg
    if lot_obj.curr_eq:
      if lot_obj.curr_eq.name!=eq_txt:
        msg={'TNS':tns,'ECD':'E02','ETX':_('EQ Not Match Lot'),'LOT':lot_txt,'EQ':eq_txt,'BIN':bin_txt,'GRADE_SET':grade_set,'OP':op_txt}
        mylog.error(msg)
        return msg
    if lot_obj.next_operation!='BI':
      msg={'TNS':tns,'ECD':'L08','ETX':_('Next Operation Mismatch'),'LOT':lot_txt,'EQ':eq_txt,'BIN':bin_txt,'GRADE_SET':grade_set,'OP':op_txt}
      mylog.error(msg)
      return msg

    #check child qty
    child_qty=0
    for g in grade_set:
      child_qty=child_qty+int(g['qty'])

    if lot_obj.qty!=child_qty:
      msg={'TNS':'tx_lot_bin','ECD':'L05','ETX':_('Lot Qty Error'),'LOT':lot_txt,'LOT_QTY':lot_obj.qty,'BIN':bin_txt,'GRADE SET':grade_set}
      mylog.error(msg)
      return msg

    lot_run_id=lot_obj.run_id
    child_lot_set=[]
    for g in grade_set:
      #lot_qty=lot_obj.qty
      child_qty=int(g['qty'])
      if child_qty>0:
        grade=g['grade']
        reply=tx_split_lot(lot_txt,op_txt,child_qty,anno_txt)
        if reply['ECD']!='0':
          msg={'TNS':'tx_lot_bin/tx_split_lot','ECD':reply['ECD'],'ETX':reply['ETX'],'ERR':reply['ERR']}
          mylog.error(msg)
          return msg
        child_lot=reply['NEW LOT']
        hist_obj=models.LotBinHist.objects.create(
          lot=child_lot,
          binning=bin_txt,
          bin_grade=grade,
          qty=child_qty,
          run_id=lot_run_id,
          transaction=tns,
          tid=tid,
          op=op_txt,
          annotation=anno_txt,
        )
        hist_obj.save()
        child_lot_obj=models.Lot.objects.get(name=child_lot)
        child_lot_obj.lot_grade=grade
        #operation_choices=(('SC','StepCheck'),('SI','StepIn'),('SO','StepOut'),('DC','DC'),('BK','Breaking'),('BI','Binning'),('NP','New Product'),('NO','None'))
        child_lot_obj.next_operation='SO'
        child_lot_obj.save()
        child_lot_set.append({'CHILD LOT':child_lot,'QTY':str(child_qty),'GRADE':grade})
      else:
        msg={'TNS':'tx_lot_bin','ECD':'L05','ETX':_('Lot Qty Error'),'LOT':lot_txt,'BIN':bin_txt,'GRADE SET':grade_set}
        mylog.error(msg)
        return msg

    msg={'TNS':'tx_lot_bin','ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'BIN':bin_txt,'CHILD LOT SET':child_lot_set,'NEXT_OP':'SO'}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg
  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':'tx_lot_bin','ERR':e,'LOT':lot_txt,'BIN':bin_txt,'GRADE SET':grade_set}
    mylog.error(msg)
    return msg

@transaction.atomic()
def tx_lot_breaking(lot_txt,eq_txt,op_txt,anno_txt):
  tns='tx_lot_breaking'
  tid=str(shortuuid.uuid())
  sid=transaction.savepoint()
  try:
    lot_set=models.Lot.objects.filter(name=lot_txt)
    if not lot_set:
      msg={'TNS':tns,'ECD':'E12','ETX':_('Lot Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
      mylog.error(msg)
      return msg

    eq_set=models.Eq.objects.filter(name=eq_txt)
    if not eq_set:
      msg={'TNS':tns,'ECD':'E05','ETX':_('EQ Not Exist'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
      mylog.error(msg)
      return msg

    lot_obj=models.Lot.objects.get(name=lot_txt)

    if lot_obj.next_operation!='BK':
      msg={'TNS':tns,'ECD':'L08','ETX':_('Lot Operation Not Match'),'LOT':lot_txt,'EQ':eq_txt,'OP':op_txt}
      mylog.error(msg)
      return msg

    if (lot_obj.curr_eq is None) or (lot_obj.curr_eq.name!=eq_txt):
      msg={'TNS':tns,'ECD':'E02','ETX':_('EQ Not Match Lot Process Step'),'LOT':lot_txt,'EQ':eq_txt}
      mylog.error(msg)
      return msg
    prod_obj=lot_obj.product
    if lot_obj.process_step.breaking is None:
      msg={'TNS':tns,'ECD':'L21','ETX':_('Lot No Break OP'),'LOT':lot_txt}
      mylog.error(msg)
      return msg
    break_obj=lot_obj.process_step.breaking
    new_prod_obj=break_obj.new_product
    break_qty=break_obj.break_qty*lot_obj.qty
    hist_obj=models.BreakingHist.objects.create(
      lot=lot_txt,
      eq=eq_txt,
      breaking=break_obj.name,
      from_qty=lot_obj.qty,
      to_qty=break_qty,
      from_product=prod_obj.name,
      to_product=new_prod_obj.name,
      run_id=lot_obj.run_id,
      transaction=tns,
      tid=tid,
      op=op_txt,
      annotation=anno_txt,
    )
    hist_obj.save()

    # update lot
    reply=qry_next_op(lot_txt)
    if reply['ECD']!='0':
      msg={'TNS':tns,'LOT':lot_txt,'reply':reply}
      mylog.error(msg)
      return msg
    lot_obj.next_operation=reply['NEXT_OP']
    lot_obj.qty=break_qty
    lot_obj.save()

    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'NEW QTY':str(break_qty),'NEXT_OP':lot_obj.next_operation}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'LOT':lot_txt}
    mylog.error(msg)
    return msg

@transaction.atomic()
def tx_change_product(lot_txt,to_product_txt,to_process_step_txt,op_txt,anno_txt):
  tns='tx_change_product'
  tid=str(shortuuid.uuid())
  sid=transaction.savepoint()
  try:
    lot_obj=models.Lot.objects.get(name=lot_txt)
    from_product=lot_obj.product.name
    from_process=lot_obj.process.name
    from_process_step=lot_obj.process_step.name
    lot_state=lot_obj.ctrl_state
    to_prod_set=models.Product.objects.filter(name=to_product_txt,freeze=True,active=True)
    if not to_prod_set:
      msg={'TNS':tns,'ECD':'P01','ETX':_('Product Not Exist'),'LOT':lot_txt,'FROM PRODUCT':from_product,'TO_PRODUCT':to_product_txt,'TO_PROCESS_STEP':to_process_step_txt,'OP':op_txt}
      mylog.error(msg)
      return msg
    to_prod_obj=to_prod_set[0]
    to_prod=to_prod_obj.name

    if to_prod_obj.process:
      to_process_obj=to_prod_obj.process
      to_process=to_process_obj.name
      to_step_set=models.ProcessStep.objects.filter(name=to_process_step_txt,freeze=True,active=True)
      if not to_step_set:
        msg={'TNS':tns,'ECD':'S01','ETX':_('Process Step Not Exist'),'LOT':lot_txt,'FROM PRODUCT':from_product,'TO PRODUCT':to_product_txt,'TO_PROCESS_STEP':to_process_step_txt,'OP':op_txt}
        mylog.error(msg)
        return msg
      to_step_obj=to_step_set[0]
      to_step=to_step_obj.name
      to_recipe=to_step_obj.recipe
      if to_step_obj.dcplan:
        to_dcplan=to_step_obj.dcplan.name
      else:
        to_dcplan=None
      if to_step_obj.step_check:
        to_step_check=to_step_obj.step_check.name
      else:
        to_step_check=None
      if to_step_obj.binning:
        to_binning=to_step_obj.binning.name
      else:
        to_binning=None
      if to_step_obj.breaking:
        to_breaking=to_step_obj.breaking.name
      else:
        to_breaking=None
      # check process, process_step integrity by find in ProcessProcessStep
      #pp_step_obj=models.ProcessProcessStep(process=to_process_obj,process_step=to_step_obj)

    else:
      to_process_obj=None
      to_step_obj=None
      to_process=None
      to_step=None
      to_recipe=None
      to_dcplan=None
      to_step_check=None
      to_binning=None
      to_breaking=None

    #log_runMES.to_info({'tns':tns,'statue':'before lot_obj assignment'})
    lot_obj.product=to_prod_obj
    lot_obj.process=to_process_obj
    lot_obj.process_step=to_step_obj
    lot_obj.step_recipe=to_recipe
    lot_obj.step_check=to_step_check
    lot_obj.step_dcplan=to_dcplan
    lot_obj.dcplan=to_dcplan
    lot_obj.step_binning=to_binning
    lot_obj.breaking=to_breaking
    lot_obj.next_operation='SI'
    lot_obj.save()

    #log_runMES.to_info({'tns':tns,'statue':'before change hist'})
    models.ProductChangeHist.objects.create(
      from_product=from_product,
      from_process=from_process,
      from_process_step=from_process_step,
      from_lot=lot_txt,
      from_lot_ctrl_state=lot_state,
      to_product=to_prod,
      to_process=to_process,
      to_process_step=to_step,
      op=op_txt,
      transaction=tns,
      tid=tid,
      annotation=anno_txt)

    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'FROM PRODUCT':from_product,'FROM PROCESS':from_process,'FROM STEP':from_process_step,'TO_PRODUCT':to_product_txt,'TO_PROCESS_STEP':to_process_step_txt,'OP':op_txt}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'LOT':lot_txt,'TO_PRODUCT':to_product_txt,'TO_PROCESS_STEP':to_process_step_txt,'OP':op_txt}
    mylog.error(msg)
    return msg

@transaction.atomic()
def tx_bonus_scrap(lot_txt,qty_int,bonus_scrap_txt,code_txt,op_txt,annotation_txt):
  tns='tx_bonus_scrap'
  tid=str(shortuuid.uuid())
  log_runMES.to_info({'TNS':tns,'LOT':lot_txt,'QTY':qty_int,'BONUS_SCRAP':bonus_scrap_txt,'CODE':code_txt,'OP':op_txt,'ANNOTATION':annotation_txt})
  sid=transaction.savepoint()
  try:
    lot_obj=models.Lot.objects.get(name=lot_txt)
    if lot_obj.ctrl_state in ['T','S']:
      return {'TNS':tns,'ECD':'L01','ETX':_('Lot State Mismatch'),'LOT':lot_txt,'LOT STATE':lot_obj.ctrl_state,'QTY':qty_int,'BONUS_SCRAP':bonus_scrap_txt,'CODE':code_txt,'OP':op_txt,'ANNOTATION':annotation_txt}
    if bonus_scrap_txt is 'S' and (qty_int>lot_obj.qty):
      return {'TNS':tns,'ECD':'BS1','SCRAP QTY OVER':qty_int,'LOT':lot_txt,'QTY':qty_int,'BONUS_SCRAP':bonus_scrap_txt,'CODE':code_txt,'OP':op_txt,'ANNOTATION':annotation_txt}
    hist_obj=models.BonusScrapHist(lot=lot_txt,process_step=lot_obj.process_step.name,lot_state=lot_obj.ctrl_state,bonus_scrap=bonus_scrap_txt,lot_old_qty=lot_obj.qty,bonus_scrap_qty=qty_int,code=code_txt,op=op_txt,run_id=lot_obj.run_id,transaction=tns,tid=tid,annotation=annotation_txt)
    hist_obj.save()
    if bonus_scrap_txt=='S':
      lot_obj.qty=lot_obj.qty-qty_int
    else:
      lot_obj.qty=lot_obj.qty+qty_int
    lot_obj.save()
    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'NEW QTY':lot_obj.qty,'LOT':lot_txt,'QTY':qty_int,'BONUS_SCRAP':bonus_scrap_txt,'CODE':code_txt,'OP':op_txt,'ANNOTATION':annotation_txt}
    log_runMES.to_info(msg)
    transaction.savepoint_commit(sid)
    return msg

  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    msg={'TNS':tns,'ERR':e,'qty':qty_int,'LOT':lot_txt,'QTY':qty_int,'BONUS_SCRAP':bonus_scrap_txt,'CODE':code_txt,'OP':op_txt,'ANNOTATION':annotation_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_lot_hold(lot_txt,op_txt,is_hold_bool,hold_code_txt,release_code_txt,annotation_txt):
  log_runMES.to_info({'TNS':'tx_lot_hold','LOT':lot_txt,'IS_HOLD':is_hold_bool,'op_txt':op_txt,'HOLD CODE':hold_code_txt,'RELEASE CODE':release_code_txt,'annotation_txt':annotation_txt})
  tns='tx_lot_hold'
  tid=str(shortuuid.uuid())
  try:
    obj=models.Lot.objects.get(name=lot_txt)
    obj.is_hold=is_hold_bool
    if is_hold_bool:
      if obj.ctrl_state in ['T','S']:
        return {'TNS':tns,'ECD':'L01','ETX':_('Lot State Mismatch'),'LOT':lot_txt,'LOT STATE':obj.ctrl_state,'OP':op_txt,'ANNOTATION':annotation_txt}
      hold_release='H'
      obj.hold_reason=hold_code_txt
    else:
      hold_release='R'
      obj.hold_reason=''
    obj.save()
    run_id=None
    if obj.run_id:
      run_id=obj.run_id
    hist_obj=models.LotHoldHist(lot=lot_txt,op=op_txt,hold_release=hold_release,hold_code=hold_code_txt,release_code=release_code_txt,transaction=tns,run_id=run_id,tid=tid)
    hist_obj.save()
    #tx_lot_hold_hist(lot_txt,op_txt,is_hold_bool,annotation_txt)
    msg={'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'IS_HOLD':is_hold_bool,'op_txt':op_txt,'HOLD CODE':hold_code_txt,'RELEASE CODE':release_code_txt,
         'annotation_txt':annotation_txt}
    log_runMES.to_info(msg)
    return msg

  except Exception as e:
    mylog.exception(e)
    msg={'TNS':'tx_lot_hold','ERR':e,'LOT':lot_txt,'IS_HOLD':is_hold_bool,'op_txt':op_txt,'HOLD CODE':hold_code_txt,'RELEASE CODE':release_code_txt,'annotation_txt':annotation_txt}
    mylog.error(msg)
    return msg

@transaction.atomic
def tx_lot_ctrl_state_change(lot_txt,state_txt,op_txt,annotation_txt):
  tns='tx_lot_ctrl_state_change'
  try:
    if not models.Lot.objects.filter(name=lot_txt):
      return {'TNS':tns,'ECD':'L12','ETX':_('Lot Not Exist'),'lot_txt':lot_txt,'op_txt':op_txt,'state_state':state_txt,'annotation_txt':annotation_txt}
    obj=models.Lot.objects.get(name=lot_txt)
    old_state=obj.ctrl_state
    obj.ctrl_state=state_txt
    if old_state==state_txt:
      return {'TNS':tns,'ECD':'L13','ETX':_('State No Change'),'lot_txt':lot_txt,'op_txt':op_txt,'state_state':state_txt,'annotation_txt':annotation_txt}
    obj.save()
    hist_obj=models.LotCtrlStateHist(lot=lot_txt,op=op_txt,ctrl_state=state_txt,transaction=tns,run_id=obj.run_id,annotation=annotation_txt)
    hist_obj.save()
    return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'lot_txt':lot_txt,'op_txt':op_txt,'old_state':old_state,'new_state':state_txt,'annotation_txt':annotation_txt}
  except Exception as e:
    mylog.exception(e)
    log_runMES.to_debug({'TNS':tns,'ERR':e,'lot_txt':lot_txt,'op_txt':op_txt,'state_state':state_txt,'annotation_txt':annotation_txt})
    return {'TNS':tns,'ERR':e,'lot_txt':lot_txt,'op_txt':op_txt,'state_state':state_txt,'annotation_txt':annotation_txt}

@transaction.atomic
def tx_eq_hold(eq_txt,op_txt,is_hold_bool,hold_code_txt,release_code_txt,annotation_txt):
  log_runMES.to_info({'TNS':'tx_eq_hold','EQ':eq_txt,'IS_HOLD':is_hold_bool,'op_txt':op_txt,'HOLD CODE':hold_code_txt,'RELEASE CODE':release_code_txt,'annotation_txt':annotation_txt})
  with transaction.atomic():
    try:
      obj=models.Eq.objects.get(name=eq_txt)
      obj.is_hold=is_hold_bool
      if is_hold_bool:
        hold_release='H'
        obj.hold_reason=hold_code_txt
      else:
        hold_release='R'
        obj.hold_reason=''
      obj.save()

      hist_obj=models.EqHoldHist(eq=eq_txt,op=op_txt,hold_release=hold_release,hold_code=hold_code_txt,release_code=release_code_txt,transaction='tx_eq_hold')
      hist_obj.save()
      return {'TNS':'tx_eq_hold','ECD':'0','ETX':_('Succeed'),'EQ':eq_txt,'IS_HOLD':is_hold_bool,'op_txt':op_txt,'HOLD CODE':hold_code_txt,'RELEASE CODE':release_code_txt,'annotation_txt':annotation_txt}

    except Exception as e:
      mylog.exception(e)
      mylog.error({'TNS':'tx_eq_hold','ERR':e,'EQ':eq_txt,'IS_HOLD':is_hold_bool,'op_txt':op_txt,'HOLD CODE':hold_code_txt,'RELEASE CODE':release_code_txt,'annotation_txt':annotation_txt})
      return {'TNS':'tx_eq_hold','ERR':e,'EQ':eq_txt,'IS_HOLD':is_hold_bool,'op_txt':op_txt,'HOLD CODE':hold_code_txt,'RELEASE CODE':release_code_txt,'annotation_txt':annotation_txt}

@transaction.atomic
def tx_eq_change_state(eq_txt,state_txt,op_txt,anno_txt):
  tns='tx_eq_change_state'
  tid=str(shortuuid.uuid())
  try:
    eqObj=models.Eq.objects.get(name=eq_txt)
    eqObj.ctrl_state=state_txt
    eqObj.save()

    hist_obj=models.EqStateHist.objects.create(eq=eq_txt,op=op_txt,ctrl_state=state_txt,transaction=tns,tid=tid,annotation=anno_txt)
    hist_obj.save()

    msg={'TNS':'tx_eq_change_state','ECD':'0','ETX':_('Succeed'),'EQ':eq_txt,'OP':op_txt,'STATE':state_txt,'ANNOTATION':anno_txt}
    log_runMES.to_info(msg)
    return msg

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'EQ':eq_txt,'OP':op_txt,'STATE':state_txt,'ANNOTATION':anno_txt})
    return {'TNS':tns,'ERR':e,'EQ':eq_txt,'OP':op_txt,'STATE':state_txt,'ANNOTATION':anno_txt}

@transaction.atomic
def tx_lot_ship(lot_txt,op_txt,anno_txt):
  tns='tx_lot_ship'
  try:
    lot_obj=models.Lot.objects.get(name=lot_txt)
    if lot_obj.is_hold is True:
      return {'TNS':tns,'ECD':'L03','ETX':_('Lot In Hold'),'LOT':lot_txt,'STATE':lot_obj.ctrl_state}
    if lot_obj.ctrl_state is 'F':
      lot_obj.ctrl_state='S'
      lot_obj.save()
      ship_obj=models.LotShipHist(lot=lot_txt,workorder=lot_obj.workorder,owner=lot_obj.owner,grade=lot_obj.lot_grade,qty=lot_obj.qty,annotation=anno_txt)
      ship_obj.save()
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'STATE':lot_obj.ctrl_state}
    else:
      return {'TNS':tns,'ECD':'L01','ETX':_('Lot State Mismatch'),'LOT':lot_txt,'STATE':lot_obj.ctrl_state}

  except Exception as e:
    mylog.exception(e)
    mylog.error({'TNS':tns,'ERR':e,'LOT':lot_txt,'OP':op_txt})
    return {'TNS':tns,'ERR':e,'LOT':lot_txt,'OP':op_txt}


def tx_query_process_steps(process_txt):
  tns='tx_query_process_step'
  try:
    p_obj=models.Process.objects.get(name=process_txt,active=True,freeze=True)
    steps=models.ProcessProcessStep.objects.filter(process=p_obj)
    #i=1
    #for s in steps:
      #log_runMES.to_debug({'TNS':'tx_query_process_steps','step:'+str(i):s.process_step.name})
      #i=i+1
    return {'TNS':tns,'ECD':'0','ETX':'Succeed','Process_Step_set':steps}

  except ObjectDoesNotExist:
    mylog.error({'TNS':tns,'ECD':'S01','ETX':'Process Step Not Exist'})
    return {'TNS':tns,'ECD':'S01','ETX':_('Process Step Not Exist'),'process_txt':process_txt}
  except Exception as e:
    mylog.exception(e)
    return {'TNS':tns,'ERR':e,'process_txt':process_txt}

def tx_alarm_msg(alarm_id_txt,alarm_msg_txt,set_clear_txt,source_txt,device_time_txt,category_txt,anno_txt):
  tns='tx_alarm_msg'
  try:
    log_runMES.to_info({'TNS':tns,'alarm_id':alarm_id_txt,'alarm_msg':alarm_msg_txt,'set_clear':set_clear_txt,'source':source_txt,'category':category_txt})
    if alarm_id_txt=='' or alarm_msg_txt=='' or source_txt=='' or set_clear_txt=='':
      return {'TNS':tns,'ECD':'A01','ETX':_('Required Field Empty'),'ALARM_ID':alarm_id_txt,'ALARM_MSG':alarm_msg_txt,'SET_CLEAR':str(set_clear_txt),'SOURCE_TXT':source_txt}
    else:
      if set_clear_txt=='1':
        set_clear=True
      elif set_clear_txt=='0':
        set_clear=False
      else:
        return {'TNS':tns,'ECD':'A01','ETX':_('SET_CLEAR_FIELD ERR'),'ALARM_ID':alarm_id_txt,'ALARM_MSG':alarm_msg_txt,'SET_CLEAR':str(set_clear_txt),'SOURCE_TXT':source_txt}
      if device_time_txt:
        device_time=datetime.strptime(device_time_txt,'%Y-%m-%d %H:%M:%S')
      else:
        device_time=None
      models.AlarmHist.objects.create(alarm_id=alarm_id_txt,alarm_txt=alarm_msg_txt,set_clear=set_clear,source=source_txt,device_time=device_time,category=category_txt,annotation=anno_txt)
      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'ALARM_ID':alarm_id_txt,'ALARM_MSG':alarm_msg_txt,'SOURCE_TXT':source_txt,'SET_CLEAR':str(set_clear_txt),}
  except Exception as e:
    mylog.exception(e)
    return {'TNS':tns,'ERR':e}

@transaction.atomic
def tx_change_lot_priority(lot_txt,priority_txt,op_txt,anno_txt):
  tns='tx_change_lot_priority'
  log_runMES.to_info({'TNS':tns,'LOT':lot_txt,'PRIORITY':priority_txt,'op_txt':op_txt,'ANNOTATION':anno_txt})
  sid=transaction.savepoint()
  try:
    if lot_txt=='' or priority_txt=='' or op_txt=='':
      return {'TNS':tns,'ECD':'A01','ETX':_('Required Field Empty'),'LOT':lot_txt,'PRIORITY':priority_txt,'OP':op_txt}
    else:
      lot_obj=models.Lot.objects.get(name=lot_txt)
      if int(priority_txt)==lot_obj.lot_priority:
        return {'TNS':tns,'ECD':'L21','ETX':_('Lot Priority No Change'),'LOT':lot_txt,'NEW PRIORITY':priority_txt,'OLD PRIORITY':str(lot_obj.lot_priority),'OP':op_txt}

      models.LotPriorityHist.objects.create(lot=lot_txt,new_priority=int(priority_txt),old_priority=lot_obj.lot_priority,annotation=anno_txt,op=op_txt)
      lot_obj.lot_priority=int(priority_txt)
      lot_obj.save()
      transaction.savepoint_commit(sid)

      return {'TNS':tns,'ECD':'0','ETX':_('Succeed'),'LOT':lot_txt,'PRIORITY':priority_txt}
  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)
    return {'TNS':tns,'ERR':e}
