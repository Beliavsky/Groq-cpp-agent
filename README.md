# Groq-cpp-agent
Python script that uses Groq to create C++ programs, iterating with compiler error messages until they compile

Sample output:
```
prompt:
Do a C++ simulation to find the optimal trimmed mean estimator of
the location of the Cauchy distribution, trying trimming proportions
of 0%, 10%, 20%, 30%, 40%, and 45%. Have the simulation use 100 samples of
1000 observations each.
Only output C++ code. Do not give commentary.

model: qwen-2.5-coder-32b

Code compiled successfully after 1 attempt (generation time: 1.484 seconds, LOC=34)!
Running executable: .\main.exe

Output:
 Trim: 0 Optimized Trimmed Mean: -0.459015
Trim: 0.1 Optimized Trimmed Mean: 0.000221861
Trim: 0.2 Optimized Trimmed Mean: -2.59736e-05
Trim: 0.3 Optimized Trimmed Mean: 5.22513e-06
Trim: 0.4 Optimized Trimmed Mean: 0.00341165
Trim: 0.45 Optimized Trimmed Mean: -0.00236174


Total generation time: 1.484 seconds across 1 attempt

Compilation command: g++ -o main main.cpp
```
