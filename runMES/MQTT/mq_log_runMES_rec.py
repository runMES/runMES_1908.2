import paho.mqtt.client as mqtt
import logging
import ast
import time
import threading

mylog=logging.getLogger('runMES')
subscribe_topic="mq_log_runMES_rec"
srv_name='mq_log_runMES_srv'

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client,userdata,flags,rc):
  # print("Connected with result code "+str(rc))
  #mylog.debug({'MQTT':'mq_qry_lot_info_srv on_connect','RC':rc,'CLIENT':client,'USERDATA':userdata,'FLAGS':flags})

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  try:
    client.subscribe(subscribe_topic)
  except Exception as e:
    mylog.exception(e)
    mylog.error({'MQTT':srv_name,'ERR':e})

# The callback for when a PUBLISH message is received from the server.
def on_message(client,userdata,msg):
  #mylog.debug({'msg':str(msg.payload),'topic':msg.topic})
  try:
    #mylog.debug({'MQTT':srv_name,'STATUS':'on_message','TOPIC':msg.topic,'MSG':msg.payload})
    payload=bytes.decode(msg.payload)
    payload=msg.payload.decode('utf8')
    #mylog.debug({'MQTT':srv_name,'MSG':payload})
    d=ast.literal_eval(str(payload))
    #mylog.debug({'MQTT':srv_name,'d':d})
    if d['log_level']=='debug':
      mylog.debug(d['msg'])
    if d['log_level']=='info':
      mylog.info(d['msg'])
    if d['log_level']=='warning':
      mylog.warning(d['msg'])
    time.sleep(0.1)

  except Exception as e:
    mylog.exception(e)
    mylog.error({'MQTT':srv_name,'STATUS':'on_message','ERR':e})

def main():
  mylog.info({'MQTT':srv_name,'STATUS':'active'})
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
