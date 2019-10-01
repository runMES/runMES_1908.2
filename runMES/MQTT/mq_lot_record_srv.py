import paho.mqtt.client as mqtt
import logging
import ast
import time
from runMES import trans
import threading
from MQTT import log_EAP_IF

mylog=logging.getLogger('EAP')

subscribe_topic="runMES/lot_record_srv"
srv_name='mq_lot_record_srv'


def synchronized(func):
  func.__lock__=threading.Lock()

  def synced_func(*args,**kws):
    with func.__lock__:
      return func(*args,**kws)

  return synced_func

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client,userdata,flags,rc):
  # print("Connected with result code "+str(rc))
  #log_EAP.to_debug({'MQTT':srv_name,'STATUS':'on_connect','RC':rc,'CLIENT':client,'USERDATA':userdata,'FLAGS':flags})

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  try:
    client.subscribe(subscribe_topic)
  except Exception as e:
    mylog.exception(e)
    mylog.error({'MQTT':srv_name,'STATUS':'subscribe','ERR':e})

# The callback for when a PUBLISH message is received from the server.
def on_message(client,userdata,msg):
  # print(msg.topic+" "+str(msg.payload))
  try:
    payload=bytes.decode(msg.payload)
    log_EAP_IF.to_info({'MQTT':srv_name,'STATUS':'on_message','TOPIC':msg.topic,'MSG':payload})
    # log_EAP.to_debug({'payload':payload})
    d=ast.literal_eval(payload)
    #log_EAP.to_debug({'d':d})
    tid=d['TID_TXT']
    rtn=d['RTN_TXT']
    lot=d['LOT_TXT']
    eq=d['EQ_TXT']
    step=d['STEP_TXT']
    dc_plan=d['DCPLAN_TXT']
    items=d['ITEM_SET']
    op=d['OP_TXT']
    anno=d['ANNO_TXT']
    log_EAP_IF.to_debug({'MQTT':srv_name,'STATUS':'parse on-message','TID':tid,'RTN':rtn,'LOT':lot,'EQ':eq,'STEP':step,'DCPLAN':dc_plan,'ITEM_SET':items,'OP':op,'ANNO':anno})

    # def tx_lot_record(lot_txt,eq_txt,step_txt,op_txt,dcplan_txt,item_set,anno_txt):
    reply=trans.tx_lot_record(lot,eq,step,op,dc_plan,items,anno)
    msg={'TID_TXT':tid,'RTN_TXT':rtn,'RPY_TXT':reply}
    log_EAP_IF.to_info({'MQTT':srv_name,'STATUS':'tns reply','msg':msg})
    client.publish(rtn,str(msg))
    time.sleep(0.1)
  except Exception as e:
    mylog.exception(e)
    mylog.error({'EAP':srv_name,'STATUS':'on_message','ERR':e})

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
    mylog.error({'EAP':srv_name,'STATUS':'loop','ERR':e})

if __name__=='__main__':
  main()
