
from MQTT import mq_log_EAP_IF_rec,mq_dc_srv,mq_step_in_srv,mq_step_out_srv,mq_eq_record_srv,mq_lot_bin_srv,mq_lot_break_srv,mq_lot_record_srv,mq_qry_dcplan_item_srv,mq_qry_eq_record_srv,mq_qry_lot_bin_srv,mq_qry_lot_srv,mq_qry_lot_record_srv,mq_qry_eq_lot_srv,mq_qry_eq_product_lot_srv,mq_S1F1_srv,mq_alarm_srv
#import dc_srv,step_in_srv,step_out_srv
import logging
#import timezone
import time
import threading

mylog=logging.getLogger('EAP')

def main():
  try:
    threads=[]

    t0=threading.Thread(target=mq_log_EAP_IF_rec.main)
    t0.daemon=True
    threads.append(t0)
    t0.start()
    mylog.info({'EAP_IF':'start mq_log_EAP_srv'})

    t1=threading.Thread(target=mq_step_in_srv.main)
    t1.daemon=True
    threads.append(t1)
    t1.start()
    mylog.info({'EAP_IF':'start step_in_srv'})

    t2=threading.Thread(target=mq_step_out_srv.main)
    t2.daemon=True
    threads.append(t2)
    t2.start()
    mylog.info({'EAP_IF':'start step_out_srv'})

    t3=threading.Thread(target=mq_dc_srv.main)
    t3.daemon=True
    threads.append(t3)
    t3.start()
    mylog.info({'EAP_IF':'start dc_srv'})

    t4=threading.Thread(target=mq_lot_break_srv.main)
    t4.daemon=True
    threads.append(t4)
    t4.start()
    mylog.info({'EAP_IF':'start lot_break_srv'})

    t5=threading.Thread(target=mq_lot_bin_srv.main)
    t5.daemon=True
    threads.append(t5)
    t5.start()
    mylog.info({'EAP_IF':'start lot_bin_srv'})

    t6=threading.Thread(target=mq_eq_record_srv.main)
    t6.daemon=True
    threads.append(t6)
    t6.start()
    mylog.info({'EAP_IF':'start eq_record_srv'})

    t7=threading.Thread(target=mq_lot_record_srv.main)
    t7.daemon=True
    threads.append(t7)
    t7.start()
    mylog.info({'EAP_IF':'start lot_record_srv'})

    t8=threading.Thread(target=mq_qry_dcplan_item_srv.main)
    t8.daemon=True
    threads.append(t8)
    t8.start()
    mylog.info({'EAP_IF':'start qry_dcplan_item_srv'})

    t9=threading.Thread(target=mq_qry_eq_record_srv.main)
    t9.daemon=True
    threads.append(t9)
    t9.start()
    mylog.info({'EAP_IF':'start qry_eq_record_srv'})

    t10=threading.Thread(target=mq_qry_lot_record_srv.main)
    t10.daemon=True
    threads.append(t10)
    t10.start()
    mylog.info({'EAP_IF':'start qry_lot_record_srv'})

    t11=threading.Thread(target=mq_qry_lot_srv.main)
    t11.daemon=True
    threads.append(t11)
    t11.start()
    mylog.info({'EAP_IF':'start qry_lot_srv'})

    t12=threading.Thread(target=mq_qry_lot_bin_srv.main)
    t12.daemon=True
    threads.append(t12)
    t12.start()
    mylog.info({'EAP_IF':'start qry_lot_bin_srv'})

    t13=threading.Thread(target=mq_qry_eq_lot_srv.main)
    t13.daemon=True
    threads.append(t13)
    t13.start()
    mylog.info({'EAP_IF':'start qry_eq_lot_srv'})

    t14=threading.Thread(target=mq_qry_eq_product_lot_srv.main)
    t14.daemon=True
    threads.append(t13)
    t14.start()
    mylog.info({'EAP_IF':'start qry_eq_product_lot_srv'})

    t15=threading.Thread(target=mq_S1F1_srv.main)
    t15.daemon=True
    threads.append(t15)
    t15.start()
    mylog.info({'EAP_IF':'start S1F1_srv'})

    t16=threading.Thread(target=mq_alarm_srv.main)
    t16.daemon=True
    threads.append(t16)
    t16.start()
    mylog.info({'EAP_IF':'start alarm_srv'})

    for th in threads:
      th.join()

    mylog.info({'EAP_IF threads':threads})
    

  except Exception as e:
    mylog.exception(e)
    mylog.error({'MQTT':'eap_if','ERR':e})

if __name__=='__main__':
  main()
