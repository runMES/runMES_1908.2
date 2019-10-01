import paho.mqtt.client as paho
import logging

mylog=logging.getLogger('EAP')

broker="localhost"
port=1883
ap_name='MyLog'
pub_sub="mq_log_runMES_rec"

def on_publish(client,userdata,result):
  #mylog.debug({'app':'app_name','status':"data published"})
  pass

def to_debug(log):
  msg={'msg':str(log)}
  msg.update({'log_level':'debug'})
  #mylog.debug({'MyLog':'to_debug','msg':msg})
  client= paho.Client("mq_log_send_debug")
  client.on_publish = on_publish
  client.connect(broker,port)
  client.publish(pub_sub,str(msg))

def to_info(log):
  msg={'msg':str(log)}
  msg.update({'log_level':'info'})
  client= paho.Client("mq_log_send_info")
  client.on_publish = on_publish
  client.connect(broker,port)
  client.publish(pub_sub,str(msg))

def to_warning(log):
  msg={'msg':str(log)}
  msg.update({'log_level':'warning'})
  client= paho.Client("mq_log_send_warning")
  client.on_publish = on_publish
  client.connect(broker,port)
  client.publish(pub_sub,str(msg))
