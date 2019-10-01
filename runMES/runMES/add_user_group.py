from django.contrib.auth.models import Group
from django.db import transaction
import logging

mylog=logging.getLogger('runMES')
groups=['OP','Super','Manager','Admin']

def main():
  v_name='add_user_group'
  sid=transaction.savepoint()
  try:
    for g in groups:
      Group.objects.create(name=g)

    transaction.savepoint_commit(sid)
    mylog.info({'Function':v_name,'Create Initial User Group':'Success'})
  except Exception as e:
    transaction.savepoint_rollback(sid)
    mylog.exception(e)

if __name__=='__main__':
  main()