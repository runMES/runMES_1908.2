from django.core.mail import send_mail
from runMES.models import MailQueue
from django.conf import settings
import time
from datetime import datetime
from django.core.validators import validate_email
from MQTT import log_runMES
import logging

mylog=logging.getLogger('runMES')
default_overdue=120
sleep_time=1

def mail_job():
  j_name='mail_job'
  log_runMES.to_info({'job':j_name,'status':'starting'})
  try:
    overdue=settings.EMAIL_OVERDUE_MIN
    if not isinstance(overdue,int) or overdue < 1:
      overdue=default_overdue

    sender=settings.EMAIL_HOST_USER
    if not sender:
      mylog.error({'job':j_name,'ERR':'No EMAIL_HOST_USER in setting.py'})
      exit()

    validate_email(sender)
    while True:
      time.sleep(sleep_time)
      mq=MailQueue.objects.filter(is_deliver=False,is_overdue=False).order_by('id')
      for obj in mq:
        log_runMES.to_info({'job':j_name,'status':'mail in q','mail_topic':obj.subject,'mail_receiver':obj.receiver})
        if obj.first_timestamp:
          sec_gap=(datetime.now-obj.first_timestamp).total_seconds()
          if (sec_gap/60)>overdue:
            obj.is_overdue=True
            obj.save()
        if not obj.is_overdue:
          if obj.receiver:
            send_mail(obj.subject,obj.contents,sender,[obj.receiver],fail_silently=False)
            log_runMES.to_info({'job':j_name,'status':'mail sent','mail_topic':obj.subject,'mail_receiver':obj.receiver})
          else:
            obj.annotation='No Receiver Mail Addr'
          obj.deliver_timestamp=datetime.now()
          obj.is_deliver=True
          obj.save()
        time.sleep(sleep_time)

  except Exception as e:
    mylog.exception(e)