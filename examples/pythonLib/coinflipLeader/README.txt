# Coin Flip Leader Election

## How to run

First make sure that simulaqron is started with the nodes you'd want to include.
This can be done with for example `simulaqron start` which by default starts a network
with the nodes Alice, Bob, Charlie, David and Eve.
Note that you need to be using either the qutip or projectq backend, since single-qubit
rotations are used which are not supported in stabilizer formalism.
To change the backend do `simulaqron set backend projectq`, which of course requires projectq
to be installed (`pip install projectq`).

In this folder there is both an example with the four nodes Alice, Bob, Charlie and David
and one where you can dynamically choose the nodes that the example uses.

To start either of the examples do
```
python3 fourPartyCoinFlip.py
```
or
```
python3 nPartyCoinFlip.py
```

When running `nPartyCoinFlip.py` fill in the names you want to use (note that these needs to 
be in the current running network) and press enter when you're finished.

## Explanation

It is possible to elect a leader from a collection of N nodes by performing a
series of coin flips as explained in [this
paper](https://arxiv.org/abs/0910.4952v2).
