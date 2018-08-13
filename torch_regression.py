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


input_size = 3 # twitter_sent, headline_sent, wiki_views
output_size = 1 # composite output
num_epochs = 300
learning_rate = 0.02


#Data and shit 
x_train = np.array([[450.,80.,14752.],[300.,88.,11000.],[260.,91.,9000.],[496.,98.,1000.],[200.,63.,2000.]],dtype=np.float32)
y_train = np.array([[3.2],[1.8],[0.2],[1.0],[-1.0]],dtype=np.float32)
print('x_train:\n',x_train)
print('y_train:\n',y_train)

class LinearRegression(nn.Module):
    def __init__(self,input_size,output_size):
        super(LinearRegression,self).__init__()
        self.linear = nn.Linear(input_size,output_size, bias=True)

    def forward(self,x):
        out = self.linear(x) #Forward propogation using linear model
        return out

model = LinearRegression(input_size,output_size)

print (*(model.parameters()))

#Lost and Optimizer
criterion = nn.MSELoss() # using Mean Squared Error loss
optimizer = torch.optim.SGD(model.parameters(),lr=learning_rate) # using Stochastic Gradient Descent


# train the Model
for epoch in range(num_epochs):

    #convert numpy arrays for training and results to torch tensor Variable class
    inputs = Variable(torch.from_numpy(x_train))
    targets = Variable(torch.from_numpy(y_train)) 

    #forward, backward, optimize
    outputs = model(inputs) # generate output from model with all input vectors
    loss = criterion(outputs,targets) #loss function
    loss.backward()
    
    if(epoch+1) %5 ==0:
        print('epoch [%d/%d], Loss: %.4f' % (epoch +1, num_epochs, loss.data[0]))
        print (model.linear.weight.data.numpy())
        predicted = model(Variable(torch.from_numpy(x_train))).data.numpy()
        plt.plot(x_train,y_train,'ro',label='Original Data')
        plt.plot(x_train,predicted,label='Fitted Line')
        plt.legend()
        plt.show()

    optimizer.zero_grad() # zero the gradients
    optimizer.step() #1-step optimization(gradient descent)

        