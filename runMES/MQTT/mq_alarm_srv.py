import paho.mqtt.client as mqtt
import logging
import ast
import time
from runMES import trans
import threading
from MQTT import log_EAP_IF
from runMES import views
from MQTT import log_EAP_IF
from datetime import datetime

mylog=logging.getLogger('EAP')
subscribe_topic="runMES/alarm_srv"
srv_name='mq_alarm_srv'

def synchronized(func):
  func.__lock__=threading.Lock()

  def synced_func(*args,**kws):
    with func.__lock__:
      return func(*args,**kws)

  return synced_func

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client,userdata,flags,rc):
  # print("Connected with result code "+str(rc))
  #log_EAP.to_debug({'MQTT':'mq_qry_lot_info_srv on_connect','RC':rc,'CLIENT':client,'USERDATA':userdata,'FLAGS':flags})

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  try:
    client.subscribe(subscribe_topic)
  except Exception as e:
    mylog.exception(e)
    mylog.error({'MQTT':srv_name,'ERR':e})

# The callback for when a PUBLISH message is received from the server.
def on_message(client,userdata,msg):
  # print(msg.topic+" "+str(msg.payload))

  try:
    time.sleep(0.1)
    log_EAP_IF.to_debug({'MQTT':srv_name,'STATUS':'on_message','TOPIC':msg.topic,'MSG':msg.payload})
    payload=bytes.decode(msg.payload)
    #payload=msg.payload.decode('utf8')
    #log_EAP_IF.to_debug({'MQTT':srv_name,'payload bytes decode':payload})
    d=ast.literal_eval(payload)
    log_EAP_IF.to_debug({'d':d})
    tid=d['TID_TXT']
    rtn=d['RTN_TXT']
    alarm_id=''
    if d['ALARM_ID_TXT']:
      alarm_id=d['ALARM_ID_TXT']
    alarm_msg=''
    if d['ALARM_MSG_TXT']:
      alarm_msg=d['ALARM_MSG_TXT']
    set_clear=''
    if d['SET_CLEAR_TXT']:
      set_clear=d['SET_CLEAR_TXT']
    source=''
    if d['SOURCE_TXT']:
      source=d['SOURCE_TXT']
    device_time=''
    if d['DEVICE_TIME_TXT']:
      device_time=d['DEVICE_TIME_TXT']
    category=''
    if d['CATEGORY_TXT']:
      category=d['CATEGORY_TXT']
    anno=''
    if d['ANNO_TXT']:
      anno=d['ANNO_TXT']

    #def tx_alarm_msg(alarm_id_txt,alarm_msg_txt,set_reset_bin,source_txt,device_time_txt,category_txt,anno_txt)
    reply=trans.tx_alarm_msg(alarm_id,alarm_msg,set_clear,source,device_time,category,anno)
    msg={'TID_TXT':tid,'RTN_TXT':rtn,'RPY_TXT':reply}
    log_EAP_IF.to_debug({'MQTT':srv_name,'STATUS':'trans reply','msg':msg})
    client.publish(rtn,str(msg))

  except Exception as e:
    mylog.exception(e)
    mylog.error({'MQTT':srv_name,'STATUS':'on_message','ERR':e})

@synchronized
def main():
  log_EAP_IF.to_info({'MQTT':srv_name,'STATUS':'active'})
  try:
    client=mqtt.Client(client_id=srv_name)
    client.on_connect=on_connect
    client.on_message=on_message
    client.connect("localhost",1883,60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.

    client.loop_forever()
  except Exception as e:
    mylog.exception(e)
    mylog.error({'MQTT':srv_name,'STATUS':'loop','ERR':e})

if __name__=='__main__':
  main()
