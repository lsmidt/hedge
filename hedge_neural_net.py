"""
Neural network for forward prediction of stock percent change based on twitter_sentiment, headline_sentiment 
"""

import torch
from torch.autograd import Variable

#  n by 2 matrix of inputs -> n days, 2 data points per day

tw = Variable()
hl = Variable()

class Model(torch.nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = torch.nn.Linear(2, 1) # output is value of percent change

    def forward(self, tw_sent, hl_sent):
        """
        accept inputs, generate outputs
        """

        change_pred = self.linear(tw_sent, hl_sent)
        return change_pred


# our model
model = Model()


# define loss function and optimizer
loss = torch.nn.MSELoss(size_average=False)
optimizer = torch.optim.SGD(model.parameters(), lr=0.01) # test value for lr
