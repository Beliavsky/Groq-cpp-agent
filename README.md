# Groq-cpp-agent
Python script that uses LLMs on Groq to create C++ programs, iterating with compiler error messages until they compile

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
The code produced is
```cpp
// Generated from prompt file: prompt_cauchy.txt
// Model used: qwen-2.5-coder-32b
// Time generated: 2025-03-08 16:52:58
// Generation time: 1.484 seconds
#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>
#include <random>

double trimmedMean(std::vector<double>& data, double trim) {
    std::sort(data.begin(), data.end());
    int trimSize = std::floor(trim * data.size());
    double sum = 0.0;
    for (int i = trimSize; i < data.size() - trimSize; ++i) {
        sum += data[i];
    }
    return sum / (data.size() - 2 * trimSize);
}

int main() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::cauchy_distribution<> dis(0.0, 1.0);

    int numSamples = 100;
    int sampleSize = 1000;
    double trims[] = {0.0, 0.1, 0.2, 0.3, 0.4, 0.45};

    for (double trim : trims) {
        double totalTrimmedMean = 0.0;
        for (int i = 0; i < numSamples; ++i) {
            std::vector<double> sample(sampleSize);
            for (int j = 0; j < sampleSize; ++j) {
                sample[j] = dis(gen);
            }
            totalTrimmedMean += trimmedMean(sample, trim);
        }
        std::cout << "Trim: " << trim << " Optimized Trimmed Mean: " << totalTrimmedMean / numSamples << std::endl;
    }

    return 0;
}
```
