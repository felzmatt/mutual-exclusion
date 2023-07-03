# Introduction
This is the project for the course Dependable and Distributed Systems held at Sapienza University of Rome, Engineering in Computer Science 2022/23.

The purpose is the implementation of Ricart-Agrawala and Maekawa protocols for mutual exclusion and an evaluation of performance under different settings. 

## Architecture
The systems is composed by N + 2 docker containers:
1) Processes node: N containers that run a protocol to obtaine accesses to a critical section.
2) CS node: A node that represent the critical section. It offers a browser GUI for demo.
1) Master node: it is a special node which routes messages among processes, and keep track of events.

The communication happens at a logic level though Perfect Point-to-Point links between each pair of nodes. The actual implementation is implemented by the master node who communicate with each process though TCP channel to guarantee reliable delivery, no duplication and also FIFO delivery. Each socket is read by a dedicated thread in the master node that poll messages, store events and put the messages to route in a shared queue that is popped by the routing node, that writes the message on the receiver socket.
Messages have all the structure: sender, receiver, msg, ts each one represented as a network integer of 4 bytes. So each message is only 16 bytes.

## Deploy
The system is configurable by writing parameters in a .env file that is stored in the same folder as docker-compose-yml file. The file as the structure reported in example-env. Each field can assume the following values:
1) NUM_PROC is a natural number representing the number of desired processes that want critical section, the system was tested with 100 processes and it work on a host machine with Ubuntu 22.04 with 8G RAM and Intel i7 10thgen. Please note that for Maekawa algorithms this number must be a perfect square because of the voting set policy.
2) PROTOCOL is M or RA, respectively Maekawa or Ricart-Agrawala
3) AUTOMODE is 0 or 1, it changes the experiment mode, look at the next section.
4) LOAD is a float between 0 and 1, it is considered when AUTOMODE is 0.
5) CS_TIME is a natural number representing the time in seconds each process spends in critical section.
6) EXP_TIME is a natural number representing the maximum time the experiment run, after this the master node sends order to stop to each process.


In project base folder run `docker-compose up --build --remove-orphans` to deploy under the given settings.

## Experiments
The master node keep tracks of each message it receives and at the end of the experiment it dumps data on a CSV file. This file can be used to conduct analysys with tools as Python pandas. Project data for report are stored in data/automatic folder.
To run an experiment it is necessary to select the desired mode:
### Automode is True
When AUTOMODE is 1 the processes decide at random when they want to access the critical section by making a call to a function that return True with a given probability at each mainloop iteration. Each process can become interested in CS more than once. The experiment stops after EXP_TIME.
### Automode is False
When AUTOMODE is 0 the master node select at random a percentage of processes, determined by LOAD parameter, and at start send them the command to request a critical section. A process will send REQUEST for CS if and only if the master node told it, and then a process cannot access the CS more than once. The experiment stops when all elected processes accessed the CS or when the EXP_TIME expires, this can happen if DEADLOCK occurs, and Maekawa algorithm is not deadlock free.
