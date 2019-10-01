from django.apps import AppConfig

class MQTTConfig(AppConfig):
  name = 'MQTT'
#
# class myMQTTConfig(AppConfig):
#     name = "MQTT"
#     verbose_name = 'eap_if'
#     def statup(self):
#         from MQTT import dc_srv,step_in_srv,step_out_srv
#         import traceback
#         import logging
#         import time
#         mylog=logging.getLogger('EAP')
#         try:
#             Thread(target=step_in_srv.main, args=()).start()
#             mylog.info({'EAP_IF':'start step_in_srv'})
#             Thread(target=step_out_srv.main, args=()).start()
#             mylog.info({'EAP_IF':'start step_out_srv'})
#             Thread(target=dc_srv.main, args=()).start()
#             mylog.info({'EAP_IF':'start dc_srv'})
#             while True:
#                 time.sleep(0.2)
#
#         except:
#             mylog.error(traceback.format_exc())
