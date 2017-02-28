#!/usr/bin/python

import sys
from comsim import *
import math


#   	[Flight 1]	ClientHello     ---> 
#
#		[Flight 2]					        <--- ServerHello 
#									        <--- ServerCertificate
#									        <--- ServerKeyExchange
#									        <--- CertificateRequest
#									        <--- ServerHelloDone
#
#		[Flight 3]  ClientCertificate --->
#					ClientKeyExchange --->
#					CertificateVerify --->
#					ChangeCipherSpec  --->
#					Finished	      --->
#
#		[Flight 4]					        <--- ServerChangeCipherSpec
#									        <--- ServerFinished
#
#       [Flight4 Ack] Flight4Ack      --->


#
# _____________________________________________________________________________
#

class DTLSClient(ProtocolAgent):

    msgListFlight2 = ['ServerHello', 'ServerCertificate', 'ServerKeyExchange', \
            'CertificateRequest', 'ServerHelloDone']
    msgListFlight4 = ['ServerChangeCipherSpec','ServerFinished']

    def __init__(self, name, scheduler, **params):
        ProtocolAgent.__init__(self, name, scheduler, **params)
        self.receivedFlight2 = {}
        self.receivedFlight4 = {}
        self.flight1_Retransmission_Count=-1
        self.flight3_Retransmission_Count=-1

    def trigger(self):
        self.transmitFlight1()
        
    def transmitFlight1(self):
        self.transmit(ProtocolMessage('ClientHello', 87))
        self.flight1_Retransmission_Count+=1        

#       Retransmission Timeout (doubles every timeout)
        self.scheduler.registerEventRel(Callback(self.checkFlight1), \
                 10.0 * math.pow(2,self.flight1_Retransmission_Count))


    def transmitFlight3(self):
        
        self.transmit(ProtocolMessage('ClientCertificate', 834))
        self.transmit(ProtocolMessage('ClientKeyExchange', 91))
        self.transmit(ProtocolMessage('CertificateVerify', 97))
        self.transmit(ProtocolMessage('ChangeCipherSpec', 13))
        self.transmit(ProtocolMessage('Finished', 37))

    
		
        self.flight3_Retransmission_Count+=1
    	self.scheduler.registerEventRel(Callback(self.checkFlight3),\
                 10.0 * math.pow(2,self.flight3_Retransmission_Count))
	
	
    def checkFlight1(self):
        if [self.receivedFlight2.get(msg, False) \
                    for msg in DTLSClient.msgListFlight2].count(True) > 0:
            print('Flight 1 complete')
        else:
            self.transmitFlight1()


    def checkFlight3(self):
        if [self.receivedFlight4.get(msg, False) \
                    for msg in DTLSClient.msgListFlight4].count(True) > 0:
            print('Flight 3 complete')
        else:
            self.transmitFlight3()
    def checkFlight4Ack(self):
        self.transmit(Message('Flight4Ack'))

    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        # client received ServerHello message
    
        if message.getName() in DTLSClient.msgListFlight2 and \
                message.getName() not in self.receivedFlight2:
            self.receivedFlight2[message.getName()] = True            
            if [self.receivedFlight2.get(msg, False) \
                    for msg in DTLSClient.msgListFlight2].count(False) == 0:
                self.transmitFlight3()

        elif message.getName() in DTLSClient.msgListFlight4 and \
                message.getName() not in self.receivedFlight4:
            self.receivedFlight4[message.getName()] = True
           
 
        elif message.getName() in self.receivedFlight2 or \
                message.getName() in self.receivedFlight4:
            print("Dropping message")

#   Retransmission for Ack of Flight 4 (Retransmit Ack4 if any duplicate msg of Flight4  
#   is received, after all of them have been received already )
        if [self.receivedFlight4.get(msg, False) \
                for msg in DTLSClient.msgListFlight4].count(False) == 0 and \
                        message.getName() in DTLSClient.msgListFlight4:
            self.transmit(Message('Flight4Ack'))
                            
#
# _____________________________________________________________________________
#

class DTLSServer(ProtocolAgent):
    
    msgListFlight4Ack = ['Flight4Ack']
    msgListFlight3 = ['ClientCertificate', 'ClientKeyExchange', 'CertificateVerify', \
            'ChangeCipherSpec', 'Finished']


    def __init__(self, name, scheduler, **params):
        
        ProtocolAgent.__init__(self, name, scheduler, **params)
        self.receivedFlight3 = {}
        self.receivedFlight4Ack ={}
        self.flight2_Retransmission_Count=-1
        self.flight4_Retransmission_Count=-1

    def transmitFlight4(self):

        self.transmit(ProtocolMessage('ServerChangeCipherSpec', 13))
        self.transmit(ProtocolMessage('ServerFinished', 37))
        self.flight4_Retransmission_Count+=1      
        self.scheduler.registerEventRel(Callback(self.checkFlight4Ack),\
                10.0 * math.pow(2,self.flight4_Retransmission_Count) )
        
    def transmitFlight2(self):
        self.transmit(ProtocolMessage('ServerHello', 107))
        self.transmit(ProtocolMessage('ServerCertificate', 834))
        self.transmit(ProtocolMessage('ServerKeyExchange', 165))
        self.transmit(ProtocolMessage('CertificateRequest', 71))
        self.transmit(ProtocolMessage('ServerHelloDone', 25))
        self.flight2_Retransmission_Count+=1        
        self.scheduler.registerEventRel(Callback(self.checkFlight2),\
                10.0 * math.pow(2,self.flight2_Retransmission_Count)) 

    def checkFlight2(self):
        if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(True) > 0:
            print('Flight 2 complete')
        else:
            
            self.transmitFlight2()
        
    def checkFlight4Ack(self):
        if len(self.receivedFlight4Ack) > 0:
            print('Flight 4 complete')
        else:
            
              
            self.transmitFlight4()
    

        
    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        # server received ClientHello message
        if message.getName() == 'ClientHello':
            self.transmitFlight2()
            
            
        elif message.getName() in DTLSServer.msgListFlight3 and \
                message.getName() not in self.receivedFlight3:
            self.receivedFlight3[message.getName()] = True            
            if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(False) == 0:
                self.transmitFlight4()                
        
        elif message.getName() in DTLSServer.msgListFlight4Ack and \
                message.getName() not in self.receivedFlight4Ack:
            self.receivedFlight4Ack[message.getName()] = True 
            print ('Handshake Completed')
            self.Handshake_Time=self.scheduler.getTime()
            

        elif message.getName() in self.receivedFlight3 or \
                message.getName() in self.receivedFlight4Ack:
            print ("Dropping message")

#
# _____________________________________________________________________________
#
class Logger(object):

    def log(self, header, text):
        lText = text.split('\n')
        lHeader = [header] + [''] * (len(lText) - 1)
        print('\n'.join(['{0:10} {1}'.format(h, t) \
                for h, t in zip(lHeader, lText)]))


#
# _____________________________________________________________________________
#


def Handshake_HS1(noOfTimes,listOfTimes):
    
    while(noOfTimes):
        noOfTimes-=1

        logger = Logger()

        scheduler = Scheduler()

        server = DTLSServer('server1', scheduler, logger=logger)
        client = DTLSClient('client', scheduler, logger=logger)

        medium = Medium(scheduler, data_rate=2400./8, msg_loss_rate=0.1, inter_msg_time = 0.001, logger=logger)
        medium.registerAgent(server)
        medium.registerAgent(client)

        client.trigger()
    
        while not scheduler.empty():
            scheduler.run()

        print server.Handshake_Time,' is handshake duration'
        listOfTimes.append(server.Handshake_Time)
#
#______________________________________________________________________________
#



def main(argv):
    HandshakeList=[]

    Handshake_HS1(10,HandshakeList)

    print HandshakeList

    pass


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);


