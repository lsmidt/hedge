"""
Neural network for forward prediction of stock percent change based on twitter_sentiment, headline_sentiment 
"""
import random
import datetime
import torch
from torch.autograd import Variable
import torch.nn.functional as F

def daterange(start_date, end_date):
    """
    Produces a generator for dates, allowing for easy iteration over a range of dates.
    """
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


x_data = Variable(torch.Tensor([[1.0], [2.0], [3.0], [4.0]]))
y_data = Variable(torch.Tensor([[0.], [0.], [1.], [1.]]))

class Model(torch.nn.Module):

    def __init__(self):
        """
        In the constructor we instantiate nn.Linear module
        """
        super(Model, self).__init__()
        self.linear = torch.nn.Linear(2, 1)  # One in and one out

    def forward(self, x, y):
        """
        In the forward function we accept a Variable of input data and we must return
        a Variable of output data.
        """
        y_pred = F.sigmoid(self.linear(x))
        return y_pred

# our model
model = Model()


# Construct our loss function and an Optimizer. The call to model.parameters()
# in the SGD constructor will contain the learnable parameters of the two
# nn.Linear modules which are members of the model.
criterion = torch.nn.BCELoss(size_average=True)
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

# Training loop
for epoch in range(1000):
        # Forward pass: Compute predicted y by passing x to the model
    y_pred = model(x_data)

    # Compute and print loss
    loss = criterion(y_pred, y_data)
    print(epoch, loss.data[0])

    # Zero gradients, perform a backward pass, and update the weights.
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

# After training
hour_var = Variable(torch.Tensor([[1.0]]))
print("predict 1 hour ", 1.0, model(hour_var).data[0][0] > 0.5)
hour_var = Variable(torch.Tensor([[7.0]]))
print("predict 7 hours", 7.0, model(hour_var).data[0][0] > 0.5)

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