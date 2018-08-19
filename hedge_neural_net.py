import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from torch.autograd import Variable

import dataset
import dbapi
import sqlalchemy
import pymysql


# AWS CREDENTIALS
HOST = "hedgedb.c288vca6ravj.us-east-2.rds.amazonaws.com"
PORT = 3306
DB_NAME = "scores_timeseries"
DB_USER = "hedgeADMIN"
DB_PW = "bluefootedboobie123"

# connect to Dataset and AWS to pull data 
scores_db = dataset.connect("sqlite:///scorebase.db")
AWS_RDS =  dataset.connect("mysql+pymysql://{}:{}@{}/{}".format\
(DB_USER, DB_PW, HOST, DB_NAME), engine_kwargs = {'pool_recycle': 3600})


in_size = 3 # twitter_sent, headline_sent, wiki_views
out_size = 1 # composite output
num_epochs = 800
learning_rate = 0.002


#Data set

#x_train = np.array([[1.564],[2.11],[3.3],[5.4]], dtype=np.float32)
x_train = np.array([[450.,80.,14752.],[300.,88.,11000.],[260.,91.,9000.],[496.,98.,11000.],[200.,63.,12000.]],dtype=np.float32)

#y_train = np.array([[8.0],[19.0],[25.0],[34.45]], dtype= np.float32)
y_train = np.array([[3.2],[1.8],[0.2],[1.0],[0.5]],dtype=np.float32)

print('x_train:\n',x_train)
print('y_train:\n',y_train)

x_train = torch.from_numpy(x_train)
y_train = torch.from_numpy(y_train)



class LinearRegression(nn.Module):

    def __init__(self):
        super(LinearRegression,self).__init__()
        self.linear = nn.Linear(3, 1)

    def forward(self,x):
        out = self.linear(x) #Forward propogation using linear model
        return out

model = LinearRegression()

#Lost and Optimizer
criterion = nn.SmoothL1Loss() # using Mean Squared Error loss
optimizer = torch.optim.SGD(model.parameters(),lr=learning_rate, weight_decay=1) # using Stochastic Gradient Descent

# train the Model
for epoch in range(num_epochs):

    #convert numpy arrays for training and results to torch tensor Variable class
    inputs = Variable(x_train)
    target = Variable(y_train)

    #forward
    outputs = model(inputs) # generate output from model with all input vectors
    loss = criterion(outputs,target) #loss function
    
    #backwards
    optimizer.zero_grad() # zero the gradients
    loss.backward() #backward propogation
    optimizer.step() #1-step optimization(gradient descent)
    
    if(epoch+1) % 1 ==0:
        print('epoch [%d/%d], Loss: %.4f' % (epoch +1, num_epochs, loss.data[0]))
        
       
model.eval()
predicted = model(Variable(x_train)).data.numpy()
      
plt.plot(x_train.numpy(), y_train.numpy(),'ro',label='Original Data')
plt.plot(x_train.numpy(), predicted,label='Fitted Line')
plt.legend()
plt.show()