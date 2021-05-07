# scoreboarding_simulator
# Author: Daniel Taylor
# Date: 05/09/2021
# CMSC 411 Computer Architecture

How to Run:
1. Copy the taylor_daniel_project.zip file into either gl.umbc.edu 
   or your own computer if you have Python 3

2. Unzip the taylor_daniel_project.zip file

3. Go to the unzipped folder directory and type "python3 scoreboard.py" 
   into the Linux terminal

4. The program should now prompt you for a program file to run. 
   You can enter either a relative ("example.txt") or absolute
   ("/dtaylor6/home/411/scoreboarding_simulator/example.txt") path
   
5. If the file path is valid, then it will prompt you for how many
   of each functional unit type you want. It will only accept 1 or 
   more of each functional unit type
   
6. scoreboard.py should now display the final scoreboard along with
   a printout of register and memory values
   
Example Run:
[dtaylor6@linux4 scoreboarding_simulator] python3 scoreboard.py
Please enter the file path of your program: example.txt
How many FP adders? 1
How many FP multipliers? 1
How many FP dividers? 1
How many integer units? 1

Instruction               Issue    Read     Exec     Write
L.D F2, 0(10)             1        2        3        4
L.D F0, 0(13)             5        6        7        8
ADD.D F4, F2, F0          6        9        11       12
L.D F6, 0(17)             9        10       11       12
ADDI $3, $3, 30           13       14       15       16
MUL.D F4, F4, F2          14       15       25       26
DIV.D F5, F6, F4          15       27       67       68
ADD.D F6, F6, F2          16       17       19       28
S.D F3, 0(10              17       18       19       20

------Register Values------
#        $            F
0        0            98
1        0            0
2        0            55
3        30           0
4        0            8415.0
5        0            0.018775995246583483
6        0            213
7        0            0
8        0            0
9        0            0
10       0            0
11       0            0
12       0            0
13       0            0
14       0            0
15       0            0
16       0            0
17       0            0
18       0            0
19       0            0
20       0            0
21       0            0
22       0            0
23       0            0
24       0            0
25       0            0
26       0            0
27       0            0
28       0            0
29       0            0
30       0            0
31       0            0

---Memory Values---
#        Value
0        45
1        12
2        0
3        0
4        10
5        135
6        254
7        127
8        18
9        4
10       0
11       8
12       2
13       98
14       13
15       5
16       233
17       158
18       167
   
