import paho.mqtt.client as mqtt
import logging
import ast
import time
from runMES import trans
import threading
from MQTT import log_EAP_IF

mylog=logging.getLogger('EAP')
subscribe_topic="runMES/qry_lot_srv"
srv_name='mq_qry_lot_srv'

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
    log_EAP_IF.to_info({'MQTT':srv_name,'STATUS':'on_message','TOPIC':msg.topic,'MSG':msg.payload})
    payload=bytes.decode(msg.payload)
    #payload=msg.payload.decode('utf8')
    #log_EAP.to_debug({'MQTT':srv_name,'payload bytes decode':payload})
    d=ast.literal_eval(payload)
    #log_EAP.to_debug({'d':d})
    tid=d['TID_TXT']
    rtn=d['RTN_TXT']
    lot=d['LOT_TXT']
    op=d['OP_TXT']
    log_EAP_IF.to_debug({'MQTT':srv_name,'STATUS':'on message','TID':tid,'RTN':rtn,'LOT':lot,'OP':op})

    # qry_lot_info(lot_txt,op_txt)
    reply=trans.qry_lot_info(lot,op)
    msg={'TID_TXT':tid,'RTN_TXT':rtn,'RPY_TXT':reply}
    log_EAP_IF.to_info({'MQTT':srv_name,'STATUS':'tns reply','msg':msg})
    client.publish(rtn,str(msg))
    time.sleep(0.1)

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
