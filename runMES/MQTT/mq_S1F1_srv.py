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
subscribe_topic="runMES/S1F1_srv"
srv_name='mq_S1F1_srv'

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
  arrive_time=str(datetime.now())
  try:
    time.sleep(0.1)
    log_EAP_IF.to_debug({'MQTT':srv_name,'STATUS':'on_message','TOPIC':msg.topic,'MSG':msg.payload})
    payload=bytes.decode(msg.payload)
    #payload=msg.payload.decode('utf8')
    #log_EAP_IF.to_debug({'MQTT':srv_name,'payload bytes decode':payload})
    d=ast.literal_eval(payload)
    tid=d['TID_TXT']
    rtn=d['RTN_TXT']
    #log_EAP_IF.to_debug({'d':d})

    reply={'S1F1':'S1F2','Ver':views.version,'Arrive_Time':arrive_time,'Reply_Time':str(datetime.now())}
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
