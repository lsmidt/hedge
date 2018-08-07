"""
Neural network for forward prediction of stock percent change based on twitter_sentiment, headline_sentiment 
"""

import torch
from torch.autograd import Variable
import random
import datetime

def daterange(start_date, end_date):
    """
    Produces a generator for dates, allowing for easy iteration over a range of dates.
    """
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


#  n by 2 matrix of inputs -> n days, 2 data points per day

tw = Variable(torch.Tensor())
hl = Variable(torch.Tensor())

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


# generate random test data
outer = {}
inner = {}
for i in daterange(datetime.date(year=2018, month=7, day=1) , datetime.date.today()):
    fake_tw_score = random.randrange(200, 800)
    fake_hl_score = random.randrange(200, 800)
    fake_result = random.uniform(-5, 5)

    inner["tw"] = fake_tw_score
    inner["hl"] = fake_hl_score
    inner["rslt"] = fake_result

    outer[i] = inner


# training loop
for date, inner_dict in outer.items():
    # forward pass completed by passing tw_sent and headline_sent into Model obj
    pred = model.forward(inner_dict["tw"], inner_dict["hl"])

    difference = loss(pred, inner_dict["rslt"])
    print (str(date), difference)

    # zero gradients, do backwards pass
    optimizer.zero_grad()
    pred.backward()
    optimizer.step()