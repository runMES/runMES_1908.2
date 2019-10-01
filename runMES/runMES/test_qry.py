from runMES.models import Lot
from datetime import datetime
import logging

mylog=logging.getLogger('runMES')

def test_redis():
  t1=datetime.now()
  mylog.debug({'test_redis-StartTime':t1})
  try:
    l_set=Lot.objects.all()
    q_list=[]
    for l in l_set:
      name=''
      if l.name:
        name=l.name
      product_name=''
      if l.product:
        product_name=l.product.name
      wo=''
      if l.workorder:
        wo=l.workorder
      state=''
      if l.ctrl_state:
        state=l.ctrl_state
      type=''
      if l.lot_type:
        type=l.lot_type
      eq=''
      if l.curr_eq:
        eq=l.curr_eq.name
      priority=''
      if l.lot_priority:
        priority=str(l.lot_priority)
      step=''
      if l.process_step:
        step=l.process_step.name
      recipe=''
      if l.step_recipe:
        recipe=l.step_recipe
      check=''
      if l.step_check:
        check=l.step_check
      dcplan=''
      if l.step_dcplan:
        dcplan=l.step_dcplan
      breaking=''
      if l.step_breaking:
        breaking=l.step_breaking
      bin=''
      if l.step_binning:
        bin=l.step_binning
      next=''
      if l.next_operation:
        next=l.next_operation

      q_list.append({'Lot':l.name,'Product':product_name,'WO':wo,'State':state,'is_Hold':l.is_hold,'type':type,'curr_eq':eq,'prority':priority,'step':step,'recipe':recipe,'check':l.step_check,'dc':dcplan,'breaking':breaking,'bin':bin,'next':next,'qty':str(l.qty)})

    t2=datetime.now()
    mylog.debug({'test_redis-EndTime':t2})

  except Exception as e:
    mylog.error(e)